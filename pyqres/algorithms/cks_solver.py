"""
CKS (Childs-Kothari-Somma) Quantum Linear System Solver - Resource Estimation

This module provides resource estimation for CKS quantum linear system solver.
Mathematical components are imported from PySparQ for consistency.

Time complexity: O(κ log(κ/ε)) where κ is condition number.

Reference:
    - A.M. Childs, R. Kothari, and R.D. Somma, SIAM J. Comput.
    - SparQ Paper: https://arxiv.org/abs/2503.15118
"""

from __future__ import annotations

import math
from typing import List, Optional

import numpy as np

# Import shared mathematical components from PySparQ
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


# Re-export for backward compatibility
__all__ = [
    "SparseMatrix",
    "SparseMatrixData",
    "ChebyshevPolynomialCoefficient",
    "get_coef_positive_only",
    "get_coef_common",
    "make_walk_angle_func",
    "CKSLinearSolver",
]


class CKSLinearSolver(AbstractComposite):
    """CKS Quantum Linear System Solver as pyqres Operation.

    This class focuses on resource estimation, not simulation.

    T-count formula:
        b = ceil(κ² * (log(κ) - log(ε)))
        j0 = sqrt(b * (log(4b) - log(ε)))
        total_walk = sum(2j+1 for j in range(j0+1)) * walk_step_cost
        T_count = encode_A_cost + encode_b_cost + total_walk

    Args:
        reg_list: [main_reg, anc_reg] - data and ancilla registers
        param_list: [kappa, epsilon] - condition number and precision
        submodules: [encode_A, encode_b] - block encoding and state prep
    """

    def __init__(self, reg_list, param_list, submodules=None):
        super().__init__(
            reg_list=reg_list, param_list=param_list, submodules=submodules or []
        )
        self.main_reg = reg_list[0]
        self.anc_reg = reg_list[1]
        self.kappa = param_list[0]
        self.eps = param_list[1]
        self.encode_A = submodules[0] if len(submodules) > 0 else None
        self.encode_b = submodules[1] if len(submodules) > 1 else None

        self._build_program_list()

    def _build_program_list(self):
        """Build operation tree for resource estimation.

        Note: This builds a representative operation tree; actual simulation
        requires PySparQ's quantum walk implementation.
        """
        self.program_list = []

        if self.encode_A:
            self.program_list.append(
                self.encode_A(
                    reg_list=[self.main_reg, self.anc_reg],
                    param_list=[self.kappa, self.eps],
                )
            )

        if self.encode_b:
            self.program_list.append(
                self.encode_b(reg_list=[self.main_reg], param_list=[self.eps])
            )

        # Build representative walk operations for T-count estimation
        b = int(np.ceil(self.kappa**2 * (np.log(self.kappa) - np.log(self.eps))))
        cheb = ChebyshevPolynomialCoefficient(b)
        j0 = int(np.sqrt(b * (np.log(4 * b) - np.log(self.eps))))

        H_op = OperationRegistry.get_class("Hadamard")
        R_op = OperationRegistry.get_class("Reflection_Bool")

        for j in range(min(cheb.b, j0 + 1)):
            step_count = cheb.step(j)  # 2j + 1
            for _ in range(step_count):
                self.program_list.append(H_op(reg_list=[self.anc_reg]))
                self.program_list.append(
                    R_op(reg_list=[self.anc_reg], param_list=[True])
                )

        self.declare_program_list()

    def sum_t_count(self, t_count_list):
        """Compute total T-count for CKS algorithm.

        Formula derived from CKS quantum walk complexity:
        - Number of walk iterations: j0 ≈ sqrt(b * log(4b/ε))
        - Each iteration j has 2j+1 walk steps
        - Walk step cost: O(n²) for n-qubit register
        """
        kappa = self.kappa
        epsilon = self.eps

        b = int(np.ceil(kappa**2 * (np.log(kappa) - np.log(epsilon))))
        j0 = int(np.sqrt(b * (np.log(4 * b) - np.log(epsilon))))

        encode_A_cost = t_count_list[0] if len(t_count_list) > 0 else 0
        encode_b_cost = t_count_list[1] if len(t_count_list) > 1 else 0

        # Walk step cost: 4n² + 8n per walk operator (from CKS paper)
        n = reg_sz(self.main_reg) if isinstance(self.main_reg, str) else 1
        walk_step_cost = 4 * n * n + 8 * n

        # Total walk iterations: sum of (2j+1) for j in range(j0+1)
        total_walk_steps = sum(2 * j + 1 for j in range(j0 + 1))
        total_walk = total_walk_steps * walk_step_cost

        return encode_A_cost + encode_b_cost + total_walk
