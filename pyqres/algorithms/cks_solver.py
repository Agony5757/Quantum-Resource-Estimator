"""
CKS (Childs-Kothari-Somma) Quantum Linear System Solver - Math Utilities

This module provides mathematical utility functions for CKS quantum linear system solver.
Quantum operations are now implemented natively via DSL (see dsl/schemas/composites/cks_linear_solver.yml).

Time complexity: O(κ log(κ/ε)) where κ is condition number.

Reference:
    - A.M. Childs, R. Kothari, and R.D. Somma, SIAM J. Comput.
    - SparQ Paper: https://arxiv.org/abs/2503.15118
"""

from __future__ import annotations

import math
from typing import List, Optional

import numpy as np

# Import mathematical components from PySparQ for computing Chebyshev coefficients
from pysparq.algorithms.cks_solver import (
    ChebyshevPolynomialCoefficient,
    SparseMatrix,
    SparseMatrixData,
    get_coef_positive_only,
    get_coef_common,
    make_walk_angle_func,
)

from ..core.operation import AbstractComposite
from ..core.registry import OperationRegistry
from ..core.utils import reg_sz


# Re-export for use in DSL python blocks
__all__ = [
    "SparseMatrix",
    "SparseMatrixData",
    "ChebyshevPolynomialCoefficient",
    "get_coef_positive_only",
    "get_coef_common",
    "make_walk_angle_func",
    "CKSLinearSolver",
    "compute_cks_t_count",
]


def compute_cks_t_count(kappa: float, epsilon: float, n_qubits: int = 1) -> dict:
    """Compute T-count for CKS algorithm analytically.

    This function provides the T-count formula for CKS algorithm
    without needing a full operation tree.

    Args:
        kappa: Condition number
        epsilon: Precision parameter
        n_qubits: Number of qubits in main register

    Returns:
        Dictionary with T-count components
    """
    b = int(np.ceil(kappa**2 * (np.log(kappa) - np.log(epsilon))))
    j0 = int(np.sqrt(b * (np.log(4 * b) - np.log(epsilon))))

    # Walk step cost: 4n² + 8n per walk operator (from CKS paper)
    walk_step_cost = 4 * n_qubits * n_qubits + 8 * n_qubits

    # Total walk iterations: sum of (2j+1) for j in range(j0+1)
    total_walk_steps = sum(2 * j + 1 for j in range(j0 + 1))
    total_walk = total_walk_steps * walk_step_cost

    # Block encoding cost (tridiagonal): 4 T-gates for prep_state + reflections
    encode_cost = 4 + 2 * n_qubits

    # State prep cost via QRAM: O(n * data_size)
    state_prep_cost = n_qubits * 8

    return {
        "walk_cost": total_walk,
        "encode_cost": encode_cost,
        "state_prep_cost": state_prep_cost,
        "total": total_walk + encode_cost + state_prep_cost,
        "b": b,
        "j0": j0,
        "total_walk_steps": total_walk_steps,
    }


class CKSLinearSolver(AbstractComposite):
    """CKS Quantum Linear System Solver as pyqres Operation.

    This class delegates quantum operations to DSL-generated operations.
    The actual quantum circuit is built from native DSL operations.

    T-count formula:
        b = ceil(κ² * (log(κ) - log(ε)))
        j0 = sqrt(b * (log(4b) - log(ε)))
        total_walk = sum(2j+1 for j in range(j0+1)) * walk_step_cost
        T_count = encode_A_cost + encode_b_cost + total_walk

    Args:
        reg_list: [main_reg, anc_reg] - data and ancilla registers
        param_list: [kappa, epsilon, matrix_params, input_vector, data_size]
        submodules: Optional pre-built submodules (not used in DSL version)
    """

    def __init__(self, reg_list, param_list, submodules=None):
        super().__init__(
            reg_list=reg_list, param_list=param_list, submodules=submodules or []
        )
        self.main_reg = reg_list[0]
        self.anc_reg = reg_list[1]
        self.kappa = param_list[0]
        self.eps = param_list[1]
        self.matrix_params = param_list[2] if len(param_list) > 2 else [1.0, 0.5]
        self.input_vector = param_list[3] if len(param_list) > 3 else None
        self.data_size = param_list[4] if len(param_list) > 4 else 8

        self._build_program_list()

    def _build_program_list(self):
        """Build operation tree using DSL-generated operations."""
        self.program_list = []

        # Use BlockEncodingTridiagonal for matrix encoding
        BlockEncodingTridiagonal = OperationRegistry.get_class("BlockEncodingTridiagonal")
        StatePreparation = OperationRegistry.get_class("StatePreparation")
        Hadamard = OperationRegistry.get_class("Hadamard")
        Reflection_Bool = OperationRegistry.get_class("Reflection_Bool")

        alpha, beta = self.matrix_params[0], self.matrix_params[1]

        # Block encoding of A
        self.program_list.append(
            BlockEncodingTridiagonal(
                reg_list=[self.main_reg, self.anc_reg],
                param_list=[alpha, beta],
            )
        )

        # State preparation |b⟩
        if self.input_vector:
            self.program_list.append(
                StatePreparation(
                    reg_list=[self.main_reg],
                    param_list=[self.input_vector, self.data_size],
                )
            )

        # Chebyshev-weighted quantum walk
        b = int(np.ceil(self.kappa**2 * (np.log(self.kappa) - np.log(self.eps))))
        cheb = ChebyshevPolynomialCoefficient(b)
        j0 = int(np.sqrt(b * (np.log(4 * b) - np.log(self.eps))))

        for j in range(min(cheb.b, j0 + 1)):
            step_count = cheb.step(j)  # 2j + 1
            for _ in range(step_count):
                self.program_list.append(Hadamard(reg_list=[self.anc_reg]))
                self.program_list.append(
                    Reflection_Bool(reg_list=[self.anc_reg], param_list=[True])
                )

        self.declare_program_list()

    def sum_t_count(self, t_count_list):
        """Compute total T-count for CKS algorithm."""
        kappa = self.kappa
        epsilon = self.eps
        n = reg_sz(self.main_reg) if isinstance(self.main_reg, str) else 1

        counts = compute_cks_t_count(kappa, epsilon, n)
        return counts["total"]
