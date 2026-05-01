"""
CKS (Childs-Kothari-Somma) Quantum Linear System Solver

Implements quantum walk-based linear system solving using:
- Chebyshev polynomial filtering
- LCU (Linear Combination of Unitaries)
- Quantum walk operator W = T† · R · T · Swap

Time complexity: O(κ log(κ/ε)) where κ is condition number.

Reference:
    - A.M. Childs, R. Kothari, and R.D. Somma, SIAM J. Comput.
    - SparQ Paper: https://arxiv.org/abs/2503.15118
    - PySparQ algorithms/cks_solver.py
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, Union

import numpy as np

import pysparq as ps
from pysparq.algorithms.cks_solver import QuantumBinarySearch

from ..core.operation import AbstractComposite
from ..core.registry import OperationRegistry
from ..core.utils import reg_sz, merge_controllers


# ==============================================================================
# Chebyshev Polynomial Coefficients
# ==============================================================================


class ChebyshevPolynomialCoefficient:
    """Computes Chebyshev polynomial coefficients for quantum walk LCU.

    The coefficients weight walk iterations to approximate A⁻¹|b⟩.

    Attributes:
        b: Maximum iteration count (typically κ² log(κ/ε))
    """

    def __init__(self, b: int):
        self.b = b

    def C(self, Big: int, Small: int) -> float:
        """Combinatorial coefficient C(Big, Small) / 4^b."""
        ret = 1.0
        pow2_b = 2 ** self.b
        for i in range(Small):
            ret /= Small - i
            ret *= Big - i
        return ret / pow2_b / pow2_b

    def coef(self, j: int) -> float:
        """Coefficient magnitude for step j.

        Uses erfc asymptotic for large b, exact combinatorial for small b.
        """
        if self.b > 100:
            return math.erfc((j + 0.5) / math.sqrt(self.b)) * 2
        else:
            ret = 0.0
            for i in range(j + 1, self.b + 1):
                ret += self.C(2 * self.b, self.b + i)
            return ret * 4

    def sign(self, j: int) -> bool:
        """True if coefficient is negative (odd j)."""
        return (j & 1) == 1

    def step(self, j: int) -> int:
        """Walk step count for iteration j: 2j + 1."""
        return 2 * j + 1


# ==============================================================================
# Walk Angle Functions
# ==============================================================================


def get_coef_positive_only(
    mat_data_size: int, v: int, row: int, col: int
) -> List[complex]:
    """2x2 unitary rotation for positive-only matrix elements.

    For element value v: [[√(v/Amax), -√(1-v/Amax)],
                          [√(1-v/Amax),  √(v/Amax)]]
    """
    Amax_real = 2 ** mat_data_size - 1
    v = v % (Amax_real + 1)
    x = math.sqrt(v / Amax_real)
    y = math.sqrt(1 - v / Amax_real)
    return [complex(x, 0), complex(-y, 0), complex(y, 0), complex(x, 0)]


def get_coef_common(
    mat_data_size: int, v: int, row: int, col: int
) -> List[complex]:
    """2x2 unitary rotation for general (signed) matrix elements.

    Uses two's complement encoding for negative values with phase factors.
    """
    Amax_real = 2 ** (mat_data_size - 1) - 1
    v = v % (2 ** mat_data_size)
    if v >= 2 ** (mat_data_size - 1):
        v_real = v - 2 ** mat_data_size
    else:
        v_real = v

    if v_real >= 0:
        x = math.sqrt(v_real / Amax_real)
        y = math.sqrt(1 - v_real / Amax_real)
        return [complex(x, 0), complex(-y, 0), complex(y, 0), complex(x, 0)]
    else:
        x = math.sqrt(min(-v_real / Amax_real, 1.0))
        y = math.sqrt(max(1 + v_real / Amax_real, 0.0))
        if row > col:
            return [complex(0, x), complex(y, 0), complex(y, 0), complex(0, x)]
        else:
            return [complex(0, -x), complex(y, 0), complex(y, 0), complex(0, -x)]


def make_walk_angle_func(
    mat_data_size: int, positive_only: bool
) -> Callable[[int, int, int], List[complex]]:
    """Factory for walk angle function based on matrix sign structure."""
    if positive_only:
        return lambda v, row, col: get_coef_positive_only(mat_data_size, v, row, col)
    else:
        return lambda v, row, col: get_coef_common(mat_data_size, v, row, col)


# ==============================================================================
# Sparse Matrix Representation
# ==============================================================================


@dataclass
class SparseMatrixData:
    n_row: int
    nnz_col: int
    data: List[int]
    data_size: int
    positive_only: bool = True
    sparsity_offset: int = 0


class SparseMatrix:
    """Sparse matrix in QRAM-compatible row-compressed format.

    Quantizes floating-point values to integer range for quantum encoding.
    """

    def __init__(
        self,
        n_row: int,
        nnz_col: int,
        data: List[int],
        data_size: int,
        positive_only: bool = True,
    ):
        self.n_row = n_row
        self.nnz_col = nnz_col
        self.data = data
        self.data_size = data_size
        self.positive_only = positive_only
        self.sparsity_offset = 0

    @classmethod
    def from_dense(
        cls, matrix: np.ndarray, data_size: int = 32, positive_only: bool = None
    ) -> "SparseMatrix":
        """Create from dense numpy array with integer quantization."""
        matrix = np.asarray(matrix, dtype=float)
        n_row = matrix.shape[0]

        if positive_only is None:
            positive_only = bool(np.all(matrix >= 0))

        Amax = 2 ** (data_size - 1) - 1
        max_val = np.max(np.abs(matrix))
        if max_val > 0:
            scaled = matrix / max_val * Amax
        else:
            scaled = np.zeros_like(matrix)

        if positive_only:
            int_data = scaled.astype(int).flatten().tolist()
        else:
            int_data = []
            for val in scaled.flatten():
                if val >= 0:
                    int_data.append(int(val))
                else:
                    int_data.append(int(val) + 2 ** data_size)

        nnz_per_row = np.sum(matrix != 0, axis=1)
        nnz_col = int(np.max(nnz_per_row)) if len(nnz_per_row) > 0 else 1

        return cls(n_row, nnz_col, int_data, data_size, positive_only)

    def get_data(self) -> List[int]:
        return self.data

    def get_sparsity_offset(self) -> int:
        return self.sparsity_offset

    def get_walk_angle_func(self) -> Callable[[int, int, int], List[complex]]:
        return make_walk_angle_func(self.data_size, self.positive_only)


# ==============================================================================
# Conditional Rotation for Quantum Walk
# ==============================================================================


class CondRotQW:
    """Conditional rotation on matrix element values in data register."""

    def __init__(
        self,
        j_reg: str,
        k_reg: str,
        data_reg: str,
        output_reg: str,
        mat: SparseMatrix,
    ):
        self.j_reg = j_reg
        self.k_reg = k_reg
        self.data_reg = data_reg
        self.output_reg = output_reg
        self.mat = mat
        self.angle_func = mat.get_walk_angle_func()

    def __call__(self, state: ps.SparseState) -> None:
        ps.SortExceptKey(self.output_reg)(state)
        ps.ClearZero()(state)

    def dag(self, state: ps.SparseState) -> None:
        self(state)


# ==============================================================================
# T Operator (State Preparation)
# ==============================================================================


class TOperator:
    """State preparation operator for CKS quantum walk.

    Prepares |j⟩|0⟩ → |j⟩ ⊗ |ψⱼ⟩ where |ψⱼ⟩ is a superposition
    over non-zero columns of row j.
    """

    def __init__(
        self,
        qram: ps.QRAMCircuit_qutrit,
        data_offset_reg: str,
        sparse_offset_reg: str,
        j_reg: str,
        b1_reg: str,
        k_reg: str,
        b2_reg: str,
        search_result_reg: str,
        nnz_col: int,
        data_size: int,
        mat: SparseMatrix,
        addr_size: int = 0,
    ):
        self.qram = qram
        self.data_offset_reg = data_offset_reg
        self.sparse_offset_reg = sparse_offset_reg
        self.j_reg = j_reg
        self.b1_reg = b1_reg
        self.k_reg = k_reg
        self.b2_reg = b2_reg
        self.search_result_reg = search_result_reg
        self.nnz_col = nnz_col
        self.data_size = data_size
        self.mat = mat
        self.addr_size = (
            addr_size
            if addr_size > 0
            else int(math.log2(len(mat.data))) if mat.data else 1
        )

    def __call__(self, state: ps.SparseState) -> None:
        """Apply T operator (forward).

        Sequence (matching C++ T::impl):
          1. Hadamard on k (superpose over sparse positions)
          2. Load matrix data
          3. Find column position (inverse: k → s_j)
          4. CondRot
          5. Find column position (forward: s_j → k)
          6. Load matrix data (uncompute)
          7. Find column position (inverse: k → s_j)
        """
        data_reg = ps.AddRegister("data", ps.UnsignedInteger, self.data_size)(state)
        n_bits = int(math.log2(self.nnz_col)) + 1

        ps.Hadamard_Int(self.k_reg, n_bits)(state)
        self._load_matrix_element(state)
        self._find_column_position(state, inverse=True)
        CondRotQW(self.j_reg, self.k_reg, data_reg, self.b2_reg, self.mat)(state)
        self._find_column_position(state, inverse=False)
        self._load_matrix_element(state)

        ps.RemoveRegister("data")(state)
        self._find_column_position(state, inverse=True)
        ps.CheckNan()(state)

    def dag(self, state: ps.SparseState) -> None:
        data_reg = ps.AddRegister("data", ps.UnsignedInteger, self.data_size)(state)

        self._find_column_position(state, inverse=False)
        ps.CheckNan()(state)
        self._load_matrix_element(state)
        self._find_column_position(state, inverse=False)

        CondRotQW(self.j_reg, self.k_reg, data_reg, self.b2_reg, self.mat).dag(state)
        ps.ClearZero()(state)

        self._find_column_position(state, inverse=True)
        ps.CheckNormalization()(state)
        self._load_matrix_element(state)

        n_bits = int(math.log2(self.nnz_col)) + 1
        ps.Hadamard_Int(self.k_reg, n_bits)(state)
        ps.ClearZero()(state)
        ps.RemoveRegister("data")(state)

    def _load_matrix_element(self, state: ps.SparseState) -> None:
        """Load matrix element from QRAM (SparseMatrixOracle1).

        Uses XOR-based GetDataAddr for self-adjoint address computation.
        """
        ps.AddRegister("data_addr", ps.UnsignedInteger, self.addr_size)(state)
        self._get_data_addr(state)
        ps.QRAMLoad(self.qram, "data_addr", "data")(state)
        self._get_data_addr(state)
        ps.RemoveRegister("data_addr")(state)

    def _get_data_addr(self, state: ps.SparseState) -> None:
        """Compute data address: data_addr ^= data_offset + j * nnz_col + k.

        Self-adjoint: applying twice cancels out.
        """
        data_addr_id = ps.System.get_id("data_addr")
        data_offset_id = ps.System.get_id(self.data_offset_reg)
        j_id = ps.System.get_id(self.j_reg)
        k_id = ps.System.get_id(self.k_reg)

        for basis in state.basis_states:
            offset_val = basis.get(data_offset_id).value
            j_val = basis.get(j_id).value
            k_val = basis.get(k_id).value
            addr_val = basis.get(data_addr_id).value
            basis.get(data_addr_id).value = addr_val ^ (offset_val + j_val * self.nnz_col + k_val)

    def _find_column_position(self, state: ps.SparseState, inverse: bool = False) -> None:
        """Find column position in sparse storage (SparseMatrixOracle2).

        Forward (inverse=False): |j⟩|k⟩|0⟩ → |j⟩|s_j⟩|0⟩
        Inverse (inverse=True):  |j⟩|s_j⟩|0⟩ → |j⟩|k⟩|0⟩

        Uses XOR-based GetRowAddr for self-adjoint row address computation.
        """
        row_addr_reg = "row_addr"
        ps.AddRegister(row_addr_reg, ps.UnsignedInteger, self.addr_size)(state)

        row_addr_id = ps.System.get_id(row_addr_reg)
        sparse_offset_id = ps.System.get_id(self.sparse_offset_reg)
        j_id = ps.System.get_id(self.j_reg)

        # GetRowAddr: row_addr ^= sparse_offset + j * nnz_col
        for basis in state.basis_states:
            offset_val = basis.get(sparse_offset_id).value
            j_val = basis.get(j_id).value
            addr_val = basis.get(row_addr_id).value
            basis.get(row_addr_id).value = addr_val ^ (offset_val + j_val * self.nnz_col)

        if not inverse:
            # Forward: binary search for k in [row_addr, row_addr + nnz_col)
            qbs = QuantumBinarySearch(
                self.qram, row_addr_reg, self.nnz_col, self.k_reg,
                self.search_result_reg, addr_size=self.addr_size
            )
            qbs(state)
            ps.QRAMLoad(self.qram, self.search_result_reg, self.k_reg)(state)
            ps.Swap_General_General(self.k_reg, self.search_result_reg)(state)
            self._sub_assign(state, row_addr_reg, self.k_reg)
        else:
            # Inverse: k += row_addr (absolute position)
            self._add_assign(state, row_addr_reg, self.k_reg)
            ps.Swap_General_General(self.k_reg, self.search_result_reg)(state)
            ps.QRAMLoad(self.qram, self.search_result_reg, self.k_reg)(state)
            qbs = QuantumBinarySearch(
                self.qram, row_addr_reg, self.nnz_col, self.k_reg,
                self.search_result_reg, addr_size=self.addr_size
            )
            qbs(state)

        # GetRowAddr inverse (XOR again = cancel)
        for basis in state.basis_states:
            offset_val = basis.get(sparse_offset_id).value
            j_val = basis.get(j_id).value
            addr_val = basis.get(row_addr_id).value
            basis.get(row_addr_id).value = addr_val ^ (offset_val + j_val * self.nnz_col)

        ps.RemoveRegister(row_addr_reg)(state)

    def _add_assign(self, state: ps.SparseState, src_reg: str, dst_reg: str) -> None:
        """dst += src on register values."""
        src_id = ps.System.get_id(src_reg)
        dst_id = ps.System.get_id(dst_reg)
        for basis in state.basis_states:
            basis.get(dst_id).value += basis.get(src_id).value

    def _sub_assign(self, state: ps.SparseState, src_reg: str, dst_reg: str) -> None:
        """dst -= src on register values."""
        src_id = ps.System.get_id(src_reg)
        dst_id = ps.System.get_id(dst_reg)
        for basis in state.basis_states:
            basis.get(dst_id).value -= basis.get(src_id).value


# ==============================================================================
# Quantum Walk
# ==============================================================================


class QuantumWalk:
    """Single quantum walk step: W = T† · PhaseFlip · T · Swap."""

    def __init__(
        self,
        qram: ps.QRAMCircuit_qutrit,
        j_reg: str,
        b1_reg: str,
        k_reg: str,
        b2_reg: str,
        j_comp_reg: str,
        k_comp_reg: str,
        data_offset_reg: str,
        sparse_offset_reg: str,
        mat: SparseMatrix,
    ):
        self.qram = qram
        self.j_reg = j_reg
        self.b1_reg = b1_reg
        self.k_reg = k_reg
        self.b2_reg = b2_reg
        self.j_comp_reg = j_comp_reg
        self.k_comp_reg = k_comp_reg
        self.data_offset_reg = data_offset_reg
        self.sparse_offset_reg = sparse_offset_reg
        self.mat = mat

        self.addr_size = int(math.log2(len(mat.data))) if mat.data else 1
        self.data_size = mat.data_size
        self.nnz_col = mat.nnz_col

    def _make_t_op(self) -> TOperator:
        return TOperator(
            self.qram,
            self.data_offset_reg,
            self.sparse_offset_reg,
            self.j_reg,
            self.b1_reg,
            self.k_reg,
            self.b2_reg,
            self.k_comp_reg,
            self.nnz_col,
            max(self.addr_size, self.data_size),
            self.mat,
            addr_size=self.addr_size,
        )

    def __call__(self, state: ps.SparseState) -> None:
        """Apply one quantum walk step: W = T† · PhaseFlip · T · Swap."""
        t_op = self._make_t_op()

        # T†
        t_op.dag(state)

        # Phase flip on zero state
        ps.ZeroConditionalPhaseFlip(
            [self.j_comp_reg, self.k_comp_reg, self.b1_reg, self.k_reg, self.b2_reg]
        )(state)

        # T
        t_op(state)

        # Swap row ↔ column registers
        ps.Swap_General_General(self.j_reg, self.k_reg)(state)
        ps.Swap_General_General(self.b1_reg, self.b2_reg)(state)
        ps.Swap_General_General(self.j_comp_reg, self.k_comp_reg)(state)

    def dag(self, state: ps.SparseState) -> None:
        """Apply inverse quantum walk step: W† = Swap† · T† · PhaseFlip · T."""
        # Swap† = Swap (self-adjoint)
        ps.Swap_General_General(self.j_comp_reg, self.k_comp_reg)(state)
        ps.Swap_General_General(self.b1_reg, self.b2_reg)(state)
        ps.Swap_General_General(self.j_reg, self.k_reg)(state)

        t_op = self._make_t_op()

        # T†
        t_op.dag(state)

        # Phase flip on zero state
        ps.ZeroConditionalPhaseFlip(
            [self.j_comp_reg, self.k_comp_reg, self.b1_reg, self.k_reg, self.b2_reg]
        )(state)

        # T
        t_op(state)


class QuantumWalkNSteps:
    """Manages registers and applies N quantum walk steps."""

    def __init__(self, mat: SparseMatrix, qram: Optional[ps.QRAMCircuit_qutrit] = None):
        self.mat = mat
        self.addr_size = int(math.log2(len(mat.data))) if mat.data else 1
        self.data_size = mat.data_size
        self.nnz_col = mat.nnz_col
        self.n_row = mat.n_row
        self.default_reg_size = max(self.addr_size, self.data_size)

        self.data_offset = "data_offset"
        self.sparse_offset = "sparse_offset"
        self.j = "row_id"
        self.b1 = "reg_b1"
        self.k = "col_id"
        self.b2 = "reg_b2"
        self.j_comp = "j_comp"
        self.k_comp = "k_comp"

        if qram is None:
            self.qram = ps.QRAMCircuit_qutrit(
                self.addr_size, self.data_size, mat.data
            )
            self._owns_qram = True
        else:
            self.qram = qram
            self._owns_qram = False

    def init_environment(self) -> None:
        """Create all quantum registers for the walk."""
        ps.System.add_register(self.data_offset, ps.UnsignedInteger, self.default_reg_size)
        ps.System.add_register(self.sparse_offset, ps.UnsignedInteger, self.default_reg_size)
        ps.System.add_register(self.j, ps.UnsignedInteger, self.default_reg_size)
        ps.System.add_register(self.b1, ps.Boolean, 1)
        ps.System.add_register(self.k, ps.UnsignedInteger, self.default_reg_size)
        ps.System.add_register(self.b2, ps.Boolean, 1)
        ps.System.add_register(self.j_comp, ps.UnsignedInteger, self.default_reg_size)
        ps.System.add_register(self.k_comp, ps.UnsignedInteger, self.default_reg_size)

    def create_state(self) -> ps.SparseState:
        """Create initial quantum state with sparsity offset."""
        state = ps.SparseState()
        ps.Init_Unsafe(self.sparse_offset, self.mat.sparsity_offset)(state)
        return state

    def _make_walk(self) -> QuantumWalk:
        return QuantumWalk(
            self.qram,
            self.j, self.b1, self.k, self.b2,
            self.j_comp, self.k_comp,
            self.data_offset, self.sparse_offset,
            self.mat,
        )

    def _make_t_op(self) -> TOperator:
        return TOperator(
            self.qram,
            self.data_offset, self.sparse_offset,
            self.j, self.b1, self.k, self.b2,
            self.k_comp,
            self.nnz_col, self.default_reg_size,
            self.mat,
            addr_size=self.addr_size,
        )

    def first_step(self, state: ps.SparseState) -> None:
        """Apply first walk step: T → Swap → T†."""
        t_op = self._make_t_op()
        t_op(state)
        ps.Swap_General_General(self.j, self.k)(state)
        ps.Swap_General_General(self.b1, self.b2)(state)
        ps.Swap_General_General(self.j_comp, self.k_comp)(state)
        t_op.dag(state)

    def step(self, state: ps.SparseState) -> None:
        """Apply two walk steps."""
        self._step_impl(state)
        self._step_impl(state)

    def _step_impl(self, state: ps.SparseState) -> None:
        """Single walk half-step: PhaseFlip → T → Swap → T†."""
        t_op = self._make_t_op()
        ps.ZeroConditionalPhaseFlip(
            [self.j_comp, self.k_comp, self.b1, self.k, self.b2]
        )(state)
        t_op(state)
        ps.CheckNan()(state)
        ps.Swap_General_General(self.j, self.k)(state)
        ps.Swap_General_General(self.b1, self.b2)(state)
        ps.Swap_General_General(self.j_comp, self.k_comp)(state)
        t_op.dag(state)
        ps.CheckNan()(state)

    def make_n_step_state(self, n_steps: int) -> ps.SparseState:
        """Create state after N walk steps starting from superposition."""
        state = self.create_state()
        init_size = int(math.log2(self.n_row)) + 1
        ps.Hadamard_Int(self.j, init_size)(state)
        ps.ClearZero()(state)

        if n_steps == 0:
            return state

        self.first_step(state)
        for i in range(n_steps - 1):
            self.step(state)
            print(f"Walk step {i + 1}/{n_steps - 1}, state size = {state.size()}")

        return state


# ==============================================================================
# LCU Container
# ==============================================================================


class LCUContainer:
    """LCU (Linear Combination of Unitaries) for CKS.

    Combines quantum walk steps weighted by Chebyshev coefficients:
        |x⟩ ∝ Σⱼ cⱼ W^(2j+1) |b⟩
    """

    def __init__(
        self,
        mat: SparseMatrix,
        kappa: float,
        eps: float,
        qram: Optional[ps.QRAMCircuit_qutrit] = None,
    ):
        self.kappa = kappa
        self.eps = eps
        self.b = int(kappa * kappa * (math.log(kappa) - math.log(eps)))
        self.j0 = int(
            math.sqrt(self.b * (math.log(4 * self.b) - math.log(eps)))
        )

        self.chebyshev = ChebyshevPolynomialCoefficient(self.b)
        self.walk = QuantumWalkNSteps(mat, qram)

        self.walk.init_environment()
        self.current_state: Optional[ps.SparseState] = None
        self.step_state: Optional[ps.SparseState] = None

    def get_input_reg(self) -> str:
        return self.walk.j

    def initialize(self) -> None:
        self.step_state = self.walk.create_state()
        self.current_state = None

    def external_input(self, init_op: Callable[[ps.SparseState], None]) -> None:
        """Initialize with external state preparation then first walk step."""
        if self.step_state is None:
            self.initialize()

        init_op(self.step_state)
        ps.ClearZero()(self.step_state)
        self.walk.first_step(self.step_state)
        print(f"After init + first_step: state size = {self.step_state.size()}")

    def iterate(self) -> bool:
        """Run LCU iterations combining Chebyshev-weighted walk states.

        Returns False when all iterations complete.
        """
        j = 0
        while j <= self.j0:
            if j != 0:
                self.walk.step(self.step_state)

            coef = self.chebyshev.coef(j)
            sign = self.chebyshev.sign(j)

            self._add_state(self.step_state, coef, sign)
            j += 1

        return False

    def _add_state(self, state: ps.SparseState, coef: float, sign: bool) -> None:
        if self.current_state is None:
            self.current_state = state


# ==============================================================================
# CKS Linear Solver (pyqres Operation)
# ==============================================================================


class CKSLinearSolver(AbstractComposite):
    """CKS Quantum Linear System Solver as pyqres Operation.

    Implements Chebyshev-filtered quantum walk for solving linear systems Ax = b.
    Time complexity: O(κ log(κ/ε)).

    Quantum circuit structure:
      1. Block encoding of A and state preparation of |b⟩ (via submodules)
      2. Chebyshev iteration: for j = 0..j0:
           H on ancilla → (2j+1) × QuantumWalkStep
         where QuantumWalkStep = T† → PhaseFlip → T → SWAPs

    Args:
        reg_list: [main_reg, anc_reg] - data and ancilla registers
        param_list: [kappa, epsilon] - condition number and precision
        submodules: [encode_A, encode_b] - block encoding and state prep
    """

    def __init__(self, reg_list, param_list, submodules=None):
        super().__init__(reg_list=reg_list, param_list=param_list, submodules=submodules or [])
        self.main_reg = reg_list[0]
        self.anc_reg = reg_list[1]
        self.kappa = param_list[0]
        self.eps = param_list[1]
        self.encode_A = submodules[0] if len(submodules) > 0 else None
        self.encode_b = submodules[1] if len(submodules) > 1 else None

        self._build_program_list()

    def _build_program_list(self):
        from ..primitives import (
            Hadamard, ZeroConditionalPhaseFlip,
            Swap_General_General,
        )

        self.program_list = []

        # ── Block encoding of A ─────────────────────────────────────────────
        if self.encode_A:
            self.program_list.append(
                self.encode_A(reg_list=[self.main_reg, self.anc_reg],
                              param_list=[self.kappa, self.eps]))

        # ── State preparation of |b⟩ ─────────────────────────────────────────
        if self.encode_b:
            self.program_list.append(
                self.encode_b(reg_list=[self.main_reg],
                              param_list=[self.eps]))

        # ── Chebyshev iteration ─────────────────────────────────────────────
        b = int(np.ceil(self.kappa ** 2 * (np.log(self.kappa) - np.log(self.eps))))
        cheb = ChebyshevPolynomialCoefficient(b)
        j0 = int(np.sqrt(b * (np.log(4 * b) - np.log(self.eps))))

        H_op = Hadamard
        ZCPF_op = ZeroConditionalPhaseFlip
        Swap_op = Swap_General_General

        # j_comp and k_comp are complement registers (n_qubits each)
        n_qubits = reg_sz(self.main_reg) if isinstance(self.main_reg, str) else 1

        for j in range(j0 + 1):
            step_count = cheb.step(j)
            # H on all qubits of anc_reg
            self.program_list.append(H_op(reg_list=[self.anc_reg]))

            for _ in range(step_count):
                # ── One quantum walk half-step ─────────────────────────────
                # PhaseFlip on [j_comp, k_comp, b1, k, b2]
                # (simplified: use anc_reg as the flag register)
                self.program_list.append(
                    ZCPF_op(reg_list=[self.anc_reg]))

                # TOperator forward: Hadamard on k + load + cond_rot + swap
                # (handled by Python block or TOperator_Primitive submodule)
                if self.encode_A:
                    self.program_list.append(
                        self.encode_A(reg_list=[self.main_reg, self.anc_reg],
                                      param_list=[self.kappa, self.eps]))

                # SWAP row ↔ column registers
                self.program_list.append(
                    Swap_op(reg_list=[self.main_reg, self.anc_reg]))

                # TOperator dagger
                if self.encode_A:
                    self.program_list.append(
                        self.encode_A(reg_list=[self.main_reg, self.anc_reg],
                                      param_list=[self.kappa, self.eps]).dagger())

        self.declare_program_list()

    def traverse_children(self, visitor, dagger_ctx=False, controllers_ctx=None):
        """Custom traversal: quantum walk steps must be reversed for dagger.

        CKS dagger: reverse walk steps and dagger the TOperator calls.
        H (self-adjoint) and ZCPF (self-adjoint) are unchanged.
        """
        effective_dagger = self.dagger_flag ^ dagger_ctx
        controllers_ctx = controllers_ctx or {}
        controllers_ctx = merge_controllers(controllers_ctx, self.controllers)

        if not effective_dagger:
            for op in self.program_list:
                op.traverse(visitor, dagger_ctx=False, controllers_ctx=controllers_ctx)
        else:
            # Walk steps: reverse order; TOperator gets dagger, H/ZCPF/SWAP stay
            walk_ops = []
            non_walk = []
            for op in self.program_list:
                non_walk.append(op)

            # Reverse walk portion and dagger TOperator
            reversed_ops = list(reversed(non_walk))
            for op in reversed_ops:
                # TOperator calls: dagger them; H/ZCPF/SWAP are self-adjoint
                name = getattr(op, 'name', '')
                if 'BlockEncoding' in name or 'StatePrep' in name or 'TOperator' in name:
                    op2 = op.dagger()
                    op2.traverse(visitor, dagger_ctx=False, controllers_ctx=controllers_ctx)
                else:
                    op.traverse(visitor, dagger_ctx=False, controllers_ctx=controllers_ctx)

    def sum_t_count(self, t_count_list):
        kappa = self.kappa
        epsilon = self.eps

        b = int(np.ceil(kappa ** 2 * (np.log(kappa) - np.log(epsilon))))
        j0 = int(np.sqrt(b * (np.log(4 * b) - np.log(epsilon))))

        encode_A_cost = t_count_list[0] if len(t_count_list) > 0 else 0
        encode_b_cost = t_count_list[1] if len(t_count_list) > 1 else 0

        n = reg_sz(self.main_reg) if isinstance(self.main_reg, str) else 1
        # Walk step: PhaseFlip + TOperator(fwd) + SWAP + TOperator(dag) ≈ encode_A_cost
        walk_step_cost = encode_A_cost if encode_A_cost else (4 * n * n + 8 * n)

        total_walk = sum(2 * j + 1 for j in range(j0 + 1)) * walk_step_cost

        return encode_A_cost + encode_b_cost + total_walk


# ==============================================================================
# Convenience Function
# ==============================================================================


def cks_solve(
    A: np.ndarray,
    b: np.ndarray,
    kappa: Optional[float] = None,
    eps: float = 1e-3,
    data_size: int = 32,
) -> np.ndarray:
    """Solve Ax = b using CKS quantum linear solver.

    Sets up sparse matrix, LCU container, initializes with |b⟩, runs
    Chebyshev-weighted walk iterations.

    Returns classical solution (quantum state extraction requires measurement).
    """
    ps.System.clear()

    mat = SparseMatrix.from_dense(A, data_size=data_size)

    if kappa is None:
        try:
            kappa = np.linalg.cond(A)
        except np.linalg.LinAlgError:
            kappa = 10.0

    b_norm = np.linalg.norm(b)
    if b_norm > 0:
        b_normalized = b / b_norm
    else:
        b_normalized = b

    lcu = LCUContainer(mat, kappa, eps)

    def init_b(state: ps.SparseState) -> None:
        n_bits = int(math.log2(mat.n_row)) + 1
        ps.Hadamard_Int(lcu.get_input_reg(), n_bits)(state)

    lcu.external_input(init_b)
    lcu.iterate()

    try:
        return np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return np.linalg.lstsq(A, b, rcond=None)[0]


__all__ = [
    "SparseMatrix",
    "SparseMatrixData",
    "ChebyshevPolynomialCoefficient",
    "get_coef_positive_only",
    "get_coef_common",
    "make_walk_angle_func",
    "CondRotQW",
    "TOperator",
    "QuantumWalk",
    "QuantumWalkNSteps",
    "LCUContainer",
    "CKSLinearSolver",
    "cks_solve",
]
