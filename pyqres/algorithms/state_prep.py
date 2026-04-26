"""
Quantum state preparation via QRAM for pyqres.

Implements binary-tree quantum state preparation:
- StatePrepViaQRAM: QRAM-based operator traversing a binary tree
- StatePreparation: High-level pipeline (distribution → tree → QRAM → execution)

Reference:
    - SparQ Paper: https://arxiv.org/abs/2503.15118
    - pysparq/algorithms/state_preparation.py
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np

import pysparq as ps

from ..core.operation import AbstractComposite, Primitive, StandardComposite
from ..core.metadata import RegisterMetadata
from ..core.utils import merge_controllers, reg_sz
from ..core.simulator import PyQSparseOperationWrapper
from ..primitives.arithmetic import (
    Add_ConstUInt, Add_UInt_UInt_InPlace, Mult_UInt_ConstUInt,
    ShiftLeft, ShiftRight, GetRotateAngle_Int_Int,
    Div_Sqrt_Arccos_Int_Int,
)
from ..primitives.gates import X as XGate
from ..primitives.qram import QRAMFast
from ..primitives.cond_rot import CondRot_General_Bool
from ..primitives.register_ops import SplitRegister, CombineRegister
from ..primitives.state_prep import ClearZero


# ==============================================================================
# QRAM utility helpers (pure python)
# ==============================================================================

def pow2(n: int) -> int:
    """Return 2**n as an integer left-shift."""
    return 1 << n


def get_complement(data: int, data_sz: int) -> int:
    """Sign-extend unsigned data to a signed integer.

    Ported from pysparq/algorithms/qram_utils.py.
    """
    if data_sz == 0:
        return 0
    if data_sz == 64:
        if data >= (1 << 63):
            return data - (1 << 64)
        return data
    sign_bit = 1 << (data_sz - 1)
    if data & sign_bit:
        return data - (1 << data_sz)
    return data


def make_complement(data: int, data_sz: int) -> int:
    """Convert signed integer to unsigned two's-complement."""
    if data_sz == 64 or data >= 0:
        return data
    return (1 << data_sz) + data


def make_vector_tree(dist: list[int], data_size: int) -> list[int]:
    """Build a binary tree from leaf distribution data for QRAM circuits.

    Ported from pysparq/algorithms/qram_utils.py.
    """
    temp_tree = list(dist)
    current_sz = len(dist)
    is_first = True

    while True:
        temp: list[int] = []
        i = 0
        while i < current_sz:
            if i + 1 < current_sz:
                if is_first:
                    a = get_complement(temp_tree[i], data_size)
                    b = get_complement(temp_tree[i + 1], data_size)
                    temp.append(a * a + b * b)
                else:
                    temp.append(temp_tree[i] + temp_tree[i + 1])
            i += 2

        temp.extend(temp_tree)
        temp_tree = temp
        current_sz = (current_sz + 1) // 2
        is_first = False

        if current_sz <= 1:
            break

    temp_tree.append(0)
    return temp_tree


def make_func(value: int, n_digit: int) -> list[complex]:
    """Compute a 2x2 rotation matrix from a rational register value.

    theta = value / 2**n_digit * 2 * pi
    Matrix: [cos(theta), -sin(theta), sin(theta), cos(theta)]
    """
    if n_digit == 64:
        theta = value * 1.0 / 2 / (1 << 63)
    else:
        theta = value / (1 << n_digit)
    theta *= 2 * math.pi
    return [
        complex(math.cos(theta), 0.0),
        complex(-math.sin(theta), 0.0),
        complex(math.sin(theta), 0.0),
        complex(math.cos(theta), 0.0),
    ]


def make_func_inv(value: int, n_digit: int) -> list[complex]:
    """Inverse 2x2 rotation matrix (off-diagonal signs flipped)."""
    if n_digit == 64:
        theta = value * 1.0 / 2 / (1 << 63)
    else:
        theta = value / (1 << n_digit)
    theta *= 2 * math.pi
    return [
        complex(math.cos(theta), 0.0),
        complex(math.sin(theta), 0.0),
        complex(-math.sin(theta), 0.0),
        complex(math.cos(theta), 0.0),
    ]


# ==============================================================================
# StatePrepViaQRAM
# ==============================================================================

class StatePrepViaQRAM(StandardComposite):
    """QRAM-based quantum state preparation via binary tree decomposition.

    Given a QRAM circuit storing a binary-tree representation of a target
    amplitude distribution, prepares the corresponding quantum state by
    traversing the tree level-by-level, loading parent/child norms from QRAM,
    and applying conditional rotations at each level.

    Attributes:
        qram: QRAMCircuit_qutrit holding the tree-encoded distribution
        work_qubit: Register on which the state is prepared
        data_size: Bit-width of signed integer data stored in QRAM
        rational_size: Bit-width of the rational rotation-angle register
    """

    def __init__(
        self,
        reg_list=None,
        param_list=None,
        submodules=None,
        qram=None,
        work_qubit: str = "main",
        data_size: int = 32,
        rational_size: int = 16,
    ):
        if reg_list is None:
            reg_list = [work_qubit]
        super().__init__(reg_list=reg_list, param_list=param_list, submodules=submodules or [])
        self.qram = qram
        self.work_qubit = work_qubit
        self.data_size = data_size
        self.rational_size = rational_size
        self.addr_size = reg_sz(work_qubit)
        self._build_program_list()

    def _build_program_list(self):
        self.program_list = []

        for k in range(self.addr_size):
            # Split one qubit for rotation angle
            self.program_list.append(
                SplitRegister(reg_list=[self.work_qubit, "_rotation"], param_list=[1]))

            # In-place: _addr_parent += pow2(k) - 1
            self.program_list.append(
                Add_ConstUInt(
                    reg_list=["_addr_parent"], param_list=[pow2(k) - 1]))

            # In-place: _addr_parent += work_qubit
            self.program_list.append(
                Add_UInt_UInt_InPlace(
                    reg_list=[self.work_qubit, "_addr_parent"], param_list=[]))

            # Multiply: _addr_child = _addr_parent * 2
            self.program_list.append(
                Mult_UInt_ConstUInt(
                    reg_list=["_addr_parent", "_addr_child"], param_list=[2]))

            self.program_list.append(
                XGate(reg_list=["_addr_child"], param_list=[0]))

            if k != self.addr_size - 1:
                self.program_list.append(
                    QRAMFast(reg_list=["_addr_parent", "_data_parent"],
                             param_list=[self.qram]))
                self.program_list.append(
                    QRAMFast(reg_list=["_addr_child", "_data_child"],
                             param_list=[self.qram]))
                self.program_list.append(
                    Div_Sqrt_Arccos_Int_Int(
                        reg_list=["_data_child", "_data_parent", "_div_result"],
                        param_list=[]))
                self.program_list.append(
                    CondRot_General_Bool(
                        reg_list=["_div_result", "_rotation"],
                        param_list=[make_func]))
                self.program_list.append(ClearZero(reg_list=[], param_list=[1e-10]))
                # Uncompute
                self.program_list.append(
                    Div_Sqrt_Arccos_Int_Int(
                        reg_list=["_data_child", "_data_parent", "_div_result"],
                        param_list=[]))
                self.program_list.append(
                    QRAMFast(reg_list=["_addr_parent", "_data_parent"],
                             param_list=[self.qram]))
                self.program_list.append(
                    QRAMFast(reg_list=["_addr_child", "_data_child"],
                             param_list=[self.qram]))
            else:
                # Last level: leaf handling
                self.program_list.append(
                    ShiftLeft(reg_list=["_addr_parent"], param_list=[1]))
                self.program_list.append(
                    XGate(reg_list=["_addr_parent"], param_list=[0]))
                # In-place: _addr_child += 1
                self.program_list.append(
                    Add_ConstUInt(reg_list=["_addr_child"], param_list=[1]))
                self.program_list.append(
                    QRAMFast(reg_list=["_addr_parent", "_data_parent"],
                             param_list=[self.qram]))
                self.program_list.append(
                    QRAMFast(reg_list=["_addr_child", "_data_child"],
                             param_list=[self.qram]))
                self.program_list.append(
                    GetRotateAngle_Int_Int(
                        reg_list=["_data_parent", "_data_child", "_div_result"],
                        param_list=[]))
                self.program_list.append(
                    CondRot_General_Bool(
                        reg_list=["_div_result", "_rotation"],
                        param_list=[make_func]))
                self.program_list.append(ClearZero(reg_list=[], param_list=[1e-10]))
                # Uncompute
                self.program_list.append(
                    GetRotateAngle_Int_Int(
                        reg_list=["_data_parent", "_data_child", "_div_result"],
                        param_list=[]))
                self.program_list.append(
                    QRAMFast(reg_list=["_addr_parent", "_data_parent"],
                             param_list=[self.qram]))
                self.program_list.append(
                    QRAMFast(reg_list=["_addr_child", "_data_child"],
                             param_list=[self.qram]))
                # In-place: _addr_child -= 1 (dagger)
                self.program_list.append(
                    Add_ConstUInt(reg_list=["_addr_child"], param_list=[-1]))
                self.program_list.append(
                    XGate(reg_list=["_addr_parent"], param_list=[0]))
                self.program_list.append(
                    ShiftRight(reg_list=["_addr_parent"], param_list=[1]))

            # Uncompute address computation
            self.program_list.append(
                XGate(reg_list=["_addr_child"], param_list=[0]))
            self.program_list.append(
                Mult_UInt_ConstUInt(
                    reg_list=["_addr_parent", "_addr_child"], param_list=[2]))
            # Uncompute: _addr_parent -= work_qubit
            self.program_list.append(
                Add_UInt_UInt_InPlace(
                    reg_list=[self.work_qubit, "_addr_parent"], param_list=[]).dagger())
            # Uncompute: _addr_parent -= pow2(k) - 1
            self.program_list.append(
                Add_ConstUInt(
                    reg_list=["_addr_parent"], param_list=[-(pow2(k) - 1)]))
            self.program_list.append(
                CombineRegister(reg_list=[self.work_qubit, "_rotation"]))
            self.program_list.append(
                ShiftLeft(reg_list=[self.work_qubit], param_list=[1]))

        self.program_list.append(ShiftRight(reg_list=[self.work_qubit], param_list=[1]))
        self.declare_program_list()

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        raise NotImplementedError(
            "StatePrepViaQRAM is composite; "
            "use pysparq pysparq.algorithms.state_preparation.StatePrepViaQRAM")


# ==============================================================================
# StatePreparation (high-level wrapper)
# ==============================================================================

class StatePreparation:
    """High-level pipeline for QRAM-based state preparation.

    Manages: random distribution generation, binary tree construction,
    QRAM creation, and execution.

    Attributes:
        qubit_number: Number of qubits (log2 of distribution length)
        data_size: Bit-width for signed integer amplitude encoding
        data_range: Bit-range controlling random amplitude magnitude
        rational_size: Bit-width for rational rotation-angle register
        dist: Raw distribution values (unsigned two's complement)
        tree: Binary tree built from dist for QRAM storage
        qram: QRAM circuit instance
    """

    def __init__(
        self,
        qubit_number: int,
        data_size: int = 8,
        data_range: int = 4,
    ):
        self.qubit_number = qubit_number
        self.data_size = data_size
        self.data_range = data_range
        self.rational_size = min(50, data_size * 2)

        self.dist: list[int] = []
        self.tree: list[int] = []
        self.qram: Optional[ps.QRAMCircuit_qutrit] = None
        self._state: Optional[ps.SparseState] = None

    def random_distribution(self) -> None:
        """Generate a random amplitude distribution.

        Each entry is sampled uniformly from [0, 2**data_range).
        Values in the upper half are mapped to negative via two's complement.
        """
        sz = pow2(self.qubit_number)
        data_max = pow2(self.data_range)
        self.dist = [0] * sz

        for i in range(sz):
            data = int(np.random.randint(0, data_max))
            if data >= pow2(self.data_range - 1):
                data = pow2(self.data_size) - (pow2(self.data_range) - data)
            self.dist[i] = data

    def set_distribution(self, dist: list[int]) -> None:
        """Set a specific distribution instead of generating randomly."""
        if len(dist) != pow2(self.qubit_number):
            raise ValueError(
                f"Distribution length {len(dist)} != {pow2(self.qubit_number)} "
                f"(2^{self.qubit_number})")
        self.dist = list(dist)

    def make_tree(self) -> None:
        """Build the binary tree from the current distribution."""
        self.tree = make_vector_tree(self.dist, self.data_size)

    def make_qram(self) -> None:
        """Create an empty QRAM circuit sized for the tree data."""
        self.qram = ps.QRAMCircuit_qutrit(
            self.qubit_number + 1, self.data_size)

    def set_qram(self) -> None:
        """Load the binary tree data into the QRAM circuit."""
        self.qram = ps.QRAMCircuit_qutrit(
            self.qubit_number + 1, self.data_size, self.tree)

    def get_real_dist(self) -> list[float]:
        """Return normalized amplitude distribution as floats."""
        total = sum(get_complement(a, self.data_size) ** 2 for a in self.dist)
        norm = math.sqrt(total) if total > 0 else 1.0
        return [
            get_complement(a, self.data_size) / norm if norm != 0 else 0.0
            for a in self.dist
        ]

    def get_fidelity(self) -> float:
        """Compute fidelity of prepared state vs target distribution."""
        if self._state is None:
            return 0.0

        total = sum(get_complement(a, self.data_size) ** 2 for a in self.dist)
        norm = math.sqrt(total) if total > 0 else 1.0

        addr_id = ps.System.get_id("main_reg")
        fid = complex(0, 0)

        for basis in self._state.basis_states:
            idx = basis.get(addr_id).value & (pow2(self.qubit_number) - 1)
            target_amp = get_complement(self.dist[idx], self.data_size) / norm
            prepared_amp = basis.amplitude
            fid += target_amp * prepared_amp

        if not math.isnan(fid.real):
            return fid.real * fid.real + fid.imag * fid.imag
        return 0.0

    def run(self) -> None:
        """Execute the full state-preparation pipeline.

        Creates registers, initializes state, and applies StatePrepViaQRAM.
        """
        ps.System.clear()

        addr_sz = self.qubit_number + 1
        ps.System.add_register("main_reg", ps.UnsignedInteger, addr_sz)

        self._state = ps.SparseState()

        state_prep_op = StatePrepViaQRAM(
            qram=self.qram,
            work_qubit="main_reg",
            data_size=self.data_size,
            rational_size=self.rational_size,
        )
        state_prep_op(self._state)
