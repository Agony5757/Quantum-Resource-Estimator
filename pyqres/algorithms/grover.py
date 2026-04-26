"""
Grover's Quantum Search Algorithm for pyqres.

Implements register-level Grover search with resource estimation:
- GroverOracle: QRAM load → Compare → PhaseFlip → Uncompute
- DiffusionOperator: H-P-H reflection about uniform superposition
- GroverSearch: AbstractComposite with O(√N) iteration formula
- grover_search(): convenience function for simulation
- grover_count(): quantum counting variant using phase estimation

Reference:
    L.K. Grover, "A fast quantum mechanical algorithm for database search"
    SparQ Paper: https://arxiv.org/abs/2503.15118
    pysparq/algorithms/grover.py
"""

from __future__ import annotations

import math
from typing import List, Optional, Union

import numpy as np

import pysparq as ps

from ..core.operation import AbstractComposite, Primitive, StandardComposite
from ..core.registry import OperationRegistry
from ..core.metadata import RegisterMetadata
from ..core.utils import merge_controllers, get_control_qubit_count, mcx_t_count
from ..core.simulator import PyQSparseOperationWrapper
from ..primitives.gates import Hadamard
from ..primitives.cond_rot import ZeroConditionalPhaseFlip
from ..primitives.arithmetic import Compare_UInt_UInt


# ==============================================================================
# Grover Oracle
# ==============================================================================

class GroverOracle(Primitive):
    """Oracle for Grover's search that marks target values.

    Operation sequence:
      1. QRAM load: |addr>|0> → |addr>|data[addr]>
      2. Compare: Check if data matches search value
      3. Phase flip: Apply -1 phase to matching states
      4. Uncompute: Reverse comparison and QRAM load

    Self-adjoint: the uncomputation makes O† = O.

    Attributes:
        qram: pysparq.QRAMCircuit_qutrit containing search data
        addr_reg: Address register name
        data_reg: Data register name
        search_reg: Search value register name
        condition_regs: Optional controller registers
    """
    __self_conjugate__ = True

    def __init__(
        self,
        reg_list,
        param_list=None,
        qram=None,
        addr_reg=None,
        data_reg=None,
        search_reg=None,
    ):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.qram = qram
        self.addr_reg = addr_reg or (reg_list[0] if len(reg_list) > 0 else None)
        self.data_reg = data_reg or (reg_list[1] if len(reg_list) > 1 else None)
        self.search_reg = search_reg or (reg_list[2] if len(reg_list) > 2 else None)
        self.temp_regs: List[str] = []

    def _make_temp_compare_regs(self) -> List[str]:
        """Create temporary boolean comparison registers."""
        self.temp_regs = ["compare_less", "compare_equal"]
        for r in self.temp_regs:
            ps.System.add_register(r, ps.Boolean, 1)
        return self.temp_regs

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        raise NotImplementedError(
            "GroverOracle uses pysparq-level QRAM primitives directly; "
            "use grover_search() for simulation")

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        """T-count for one Grover oracle invocation.

        Dominated by the Compare_UInt_UInt operation between data and search
        registers (O(m) Toffoli for m-bit comparison). Phase flip is O(1).
        QRAM loading is excluded (bucket-brigade has different cost model).
        """
        # Number of comparison bits = data register size
        data_reg = self.data_reg
        meta = RegisterMetadata.get_register_metadata()
        data_size = meta.registers.get(data_reg, 32)
        if not isinstance(data_size, int):
            data_size = 32

        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))

        # O(m) Toffoli for m-bit comparison using ripple-carry
        compare_tc = 4 * data_size
        # Phase flip on match flag
        phase_tc = 4 * ncontrols + 1 if ncontrols > 0 else 0

        return compare_tc + phase_tc


# ==============================================================================
# Diffusion Operator
# ==============================================================================

class DiffusionOperator(Primitive):
    """HPH (Hadamard-Phase-Hadamard) diffusion operator.

    Implements D = H ⊗⊗n (2|0⟩⟨0| - I) H ⊗⊗n = 2|s⟩⟨s| - I
    where |s⟩ is the uniform superposition over all n-qubit states.

    Self-adjoint: D† = D.

    Attributes:
        addr_reg: Address register to diffuse over
    """
    __self_conjugate__ = True

    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.addr_reg = reg_list[0] if reg_list else None

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        raise NotImplementedError(
            "DiffusionOperator is composite; use SimulatorVisitor for simulation")

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        """T-count for diffusion operator.

        Cost = 2 * ZeroConditionalPhaseFlip(n) where n = address bits.
        Each n-qubit ZeroConditionalPhaseFlip costs 4n + 1 T-gates.
        """
        addr_reg = self.addr_reg
        meta = RegisterMetadata.get_register_metadata()
        addr_size = meta.registers.get(addr_reg, 1)
        if not isinstance(addr_size, int):
            addr_size = 1

        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        total_controls = ncontrols + addr_size

        if total_controls == 0:
            return 0
        return 2 * (4 * total_controls + 1)


# ==============================================================================
# Grover Operator (one iteration)
# ==============================================================================

class GroverOperator(StandardComposite):
    """One complete Grover iteration: Oracle followed by Diffusion.

    G = D · O

    where O is the Grover oracle and D is the diffusion operator.
    Self-adjoint: G† = G.

    Attributes:
        addr_reg: Address register
        data_reg: Data register (temporary)
        search_reg: Search value register
        qram: pysparq QRAM circuit
    """
    __self_conjugate__ = True

    def __init__(
        self,
        reg_list,
        param_list=None,
        submodules=None,
        qram=None,
    ):
        super().__init__(reg_list=reg_list, param_list=param_list, submodules=submodules)
        self.addr_reg = reg_list[0] if len(reg_list) > 0 else None
        self.data_reg = reg_list[1] if len(reg_list) > 1 else None
        self.search_reg = reg_list[2] if len(reg_list) > 2 else None
        self.qram = qram

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        raise NotImplementedError(
            "GroverOperator is composite; use SimulatorVisitor for simulation")

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        # Delegates to visitor via sum of children
        return None


# ==============================================================================
# Grover Search (full algorithm)
# ==============================================================================

class GroverSearch(AbstractComposite):
    """Grover's quantum search algorithm.

    Finds a target value in an unsorted memory of N items in O(√N) queries,
    providing a quadratic speedup over classical search.

    Args:
        reg_list: [addr_reg, data_reg, search_reg]
        param_list: [memory, target, n_iterations, data_size]
            - memory: List[int] — search data
            - target: int — value to find
            - n_iterations: int — number of Grover iterations (auto if None)
            - data_size: int — bits for data register (auto if None)
        submodules: Not used; grover_ops built internally

    Resource estimation (per iteration):
        T-count ≈ 2 * (4(n+m) + 1) + 4m
        where n = ceil(log2 N), m = data_size

    Example:
        >>> search = GroverSearch(
        ...     reg_list=["addr", "data", "search"],
        ...     param_list=[[5, 12, 3, 8], 8, None, None]
        ... )
        >>> tc = search.t_count()
        >>> print(f"T-count estimate: {tc}")
    """

    def __init__(self, reg_list, param_list=None, submodules=None, qram=None):
        super().__init__(reg_list=reg_list, param_list=param_list, submodules=submodules or [])
        self.addr_reg = reg_list[0] if len(reg_list) > 0 else None
        self.data_reg = reg_list[1] if len(reg_list) > 1 else None
        self.search_reg = reg_list[2] if len(reg_list) > 2 else None

        self.memory = param_list[0] if len(param_list) > 0 else []
        self.target = param_list[1] if len(param_list) > 1 else None
        n_iters = param_list[2] if len(param_list) > 2 else None
        self.data_size = param_list[3] if len(param_list) > 3 else None

        n = len(self.memory)
        self.n_bits = max(1, (n - 1).bit_length())

        if self.data_size is None:
            max_val = max(max(self.memory), self.target)
            self.data_size = max(1, max_val.bit_length())
            self.data_size = max(self.data_size, 6)

        if n_iters is None:
            self.n_iterations = max(1, int(math.pi / 4 * math.sqrt(n)))
        else:
            self.n_iterations = n_iters

        self.qram = qram
        self._build_program_list()

    def _build_program_list(self):
        """Build the list of operations for Grover's algorithm."""

        self.program_list = []

        # Initialize: equal superposition over address space
        self.program_list.append(
            Hadamard(reg_list=[self.addr_reg]))

        # Grover iterations
        for _ in range(self.n_iterations):
            # --- Oracle ---
            # (1) QRAM load — excluded from T-count (bucket-brigade model)
            # (2) Compare data[addr] vs search_reg
            self.program_list.append(
                Compare_UInt_UInt(
                    reg_list=[self.data_reg, self.search_reg,
                              "_compare_less", "_compare_equal"],
                    param_list=[]))

            # (3) Phase flip on match: apply -1 to |data == search>
            self.program_list.append(
                ZeroConditionalPhaseFlip(
                    reg_list=["_compare_equal"],
                    param_list=None))

            # (4) Uncompute comparison
            self.program_list.append(
                Compare_UInt_UInt(
                    reg_list=[self.data_reg, self.search_reg,
                              "_compare_less", "_compare_equal"],
                    param_list=[]))

            # --- Diffusion ---
            # H on all address qubits
            self.program_list.append(
                Hadamard(reg_list=[self.addr_reg]))

            # Phase flip on |0...0⟩
            self.program_list.append(
                ZeroConditionalPhaseFlip(
                    reg_list=[self.addr_reg],
                    param_list=None))

            # H again
            self.program_list.append(
                Hadamard(reg_list=[self.addr_reg]))

        self.declare_program_list()

    def sum_t_count(self, t_count_list):
        """Sum T-counts of all Grover operations.

        Formula per iteration (ignoring QRAM):
          Oracle:  4 * data_size  (m-bit comparison)
                   + 4 * n_bits + 1  (phase flip on match)
          Diffusion: 2 * (4 * n_bits + 1)  (two ZeroConditionalPhaseFlip)

        Total per iteration: 4 * data_size + 3 * (4 * n_bits + 1)
        """
        # The program_list has: 1 H (init) + n_iters * 7 operations
        # But we use the explicit formula based on register sizes
        oracle_tc = 4 * self.data_size + 4 * self.n_bits + 1
        diffusion_tc = 2 * (4 * self.n_bits + 1)
        per_iter = oracle_tc + diffusion_tc
        return self.n_iterations * per_iter

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return self.sum_t_count([0] * len(self.program_list))


# ==============================================================================
# Convenience functions
# ==============================================================================

def grover_search(
    memory: List[int],
    target: int,
    n_iterations: Optional[int] = None,
    data_size: Optional[int] = None,
) -> tuple[int, float]:
    """Execute Grover's search on a pysparq SparseState.

    Args:
        memory: List of integers to search through
        target: Value to find
        n_iterations: Number of Grover iterations (auto-computed if None)
        data_size: Bit size for data register (auto-computed if None)

    Returns:
        (index, probability) — most likely index containing target

    Note: Requires pysparq installed. Falls back gracefully if not available.
    """
    try:
        import pysparq as ps
    except ImportError:
        raise ImportError(
            "grover_search requires pysparq: pip install pysparq")

    ps.System.clear()

    n = len(memory)
    n_bits = max(1, (n - 1).bit_length())
    actual_n = 2 ** n_bits

    if actual_n != n:
        memory = memory + [target + i + 1 for i in range(actual_n - n)]

    if data_size is None:
        max_val = max(max(memory), target)
        data_size = max(1, max_val.bit_length())
        data_size = max(data_size, 6)

    if n_iterations is None:
        n_iterations = max(1, int(math.pi / 4 * math.sqrt(len(memory))))

    qram = ps.QRAMCircuit_qutrit(n_bits, data_size, memory)
    state = ps.SparseState()

    addr_reg = ps.AddRegister("addr", ps.UnsignedInteger, n_bits)(state)
    data_reg = ps.AddRegister("data", ps.UnsignedInteger, data_size)(state)
    search_reg = ps.AddRegister("search", ps.UnsignedInteger, data_size)(state)

    ps.Init_Unsafe("search", target)(state)
    ps.Hadamard_Int_Full("addr")(state)

    from pysparq.algorithms.grover import GroverOperator
    grover_op = GroverOperator(qram, "addr", "data", "search")

    for _ in range(n_iterations):
        grover_op(state)

    addr_id = ps.System.get_id("addr")
    addr_probs: dict[int, float] = {}
    for basis in state.basis_states:
        addr_val = basis.get(addr_id).value
        prob = abs(basis.amplitude) ** 2
        addr_probs[addr_val] = addr_probs.get(addr_val, 0) + prob

    best_addr = max(addr_probs, key=addr_probs.get)  # type: ignore[arg-type]
    best_prob = addr_probs[best_addr]
    return best_addr, best_prob


def grover_count(
    memory: List[int],
    target: int,
    precision_bits: int = 8,
    data_size: Optional[int] = None,
) -> tuple[int, float]:
    """Quantum counting variant of Grover's algorithm.

    Uses phase estimation to count how many memory entries equal target.

    Args:
        memory: List of integers to search
        target: Value to count
        precision_bits: Bits in precision register
        data_size: Bits for data register (auto if None)

    Returns:
        (estimated_count, probability)
    """
    try:
        import pysparq as ps
    except ImportError:
        raise ImportError("grover_count requires pysparq: pip install pysparq")

    ps.System.clear()

    n = len(memory)
    n_bits = max(1, (n - 1).bit_length())
    actual_n = 2 ** n_bits

    if actual_n != n:
        memory = memory + [target + i + 100 for i in range(actual_n - n)]

    if data_size is None:
        max_val = max(max(memory), target)
        data_size = max(1, max_val.bit_length())
        data_size = max(data_size, 4)

    qram = ps.QRAMCircuit_qutrit(n_bits, data_size, memory)
    state = ps.SparseState()

    count_reg = ps.AddRegister("count", ps.UnsignedInteger, precision_bits)(state)
    addr_reg = ps.AddRegister("addr", ps.UnsignedInteger, n_bits)(state)
    data_reg = ps.AddRegister("data", ps.UnsignedInteger, data_size)(state)
    search_reg = ps.AddRegister("search", ps.UnsignedInteger, data_size)(state)

    ps.Init_Unsafe("search", target)(state)
    ps.Hadamard_Int_Full("count")(state)
    ps.Hadamard_Int_Full("addr")(state)

    from pysparq.algorithms.grover import GroverOperator
    grover_op = GroverOperator(qram, "addr", "data", "search")

    for i in range(precision_bits):
        for _ in range(2 ** i):
            grover_op.conditioned_by_bit("count", i)(state)

    ps.inverseQFT("count")(state)
    measured_results, prob = ps.PartialTrace(
        ["addr", "data", "search"])(state)

    return measured_results[0], prob
