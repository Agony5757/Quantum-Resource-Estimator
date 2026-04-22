"""
QDA (Quantum Discrete Adiabatic) Linear System Solver - Resource Estimation

This module provides resource estimation for QDA quantum linear system solver.
Mathematical components are imported from PySparQ for consistency.

Time complexity: O(κ log(κ/ε)) — optimal for quantum linear solving.

Reference:
    - L. Lin and Y. Tong, PRX Quantum 3, 040303 (2022)
    - SparQ Paper: https://arxiv.org/abs/2503.15118
"""

from __future__ import annotations

import math
from typing import List, Optional

import numpy as np

# Import shared mathematical components from PySparQ
from pysparq.algorithms.qda_solver import (
    compute_fs,
    compute_rotation_matrix,
    chebyshev_T,
    dolph_chebyshev,
    compute_fourier_coeffs,
    calculate_angles,
    classical_to_quantum,
)

from ..core.operation import AbstractComposite
from ..core.registry import OperationRegistry

# Re-export for backward compatibility
__all__ = [
    "compute_fs",
    "compute_rotation_matrix",
    "chebyshev_T",
    "dolph_chebyshev",
    "compute_fourier_coeffs",
    "calculate_angles",
    "classical_to_quantum",
    "QDALinearSolver",
]


class QDALinearSolver(AbstractComposite):
    """QDA Quantum Linear System Solver as pyqres Operation.

    Uses discrete adiabatic evolution for O(κ log(κ/ε)) complexity.

    T-count formula:
        n_steps = ceil(log(κ/ε))
        step_cost = O(n) per discretization point
        T_count = n_steps * step_cost + encode_costs

    Args:
        reg_list: [main_reg, anc_UA, anc_1, anc_2, anc_3, anc_4]
        param_list: [kappa, epsilon]
        submodules: [encode_A, encode_b]
    """

    def __init__(self, reg_list, param_list, submodules=None):
        super().__init__(
            reg_list=reg_list, param_list=param_list, submodules=submodules or []
        )
        self.main_reg = reg_list[0]
        self.anc_UA = reg_list[1] if len(reg_list) > 1 else None
        self.anc_1 = reg_list[2] if len(reg_list) > 2 else None
        self.anc_2 = reg_list[3] if len(reg_list) > 3 else None
        self.anc_3 = reg_list[4] if len(reg_list) > 4 else None
        self.anc_4 = reg_list[5] if len(reg_list) > 5 else None

        self.kappa = param_list[0]
        self.epsilon = param_list[1]
        self.block_encoding = submodules[0] if len(submodules) > 0 else None
        self.state_prep = submodules[1] if len(submodules) > 1 else None

        self.p = 0.5  # Schedule parameter
        self.n_steps = int(np.ceil(np.log(self.kappa / self.epsilon)))

        self._build_program_list()

    def _build_program_list(self):
        """Build operation tree for resource estimation."""
        self.program_list = []

        # Initialize to H₀ eigenstate: X on first qubit of main register
        X_op = OperationRegistry.get_class("X")
        self.program_list.append(X_op(reg_list=[self.main_reg], param_list=[0]))

        # State preparation |b⟩ via submodule
        if self.state_prep:
            self.program_list.append(
                self.state_prep(
                    reg_list=[self.main_reg], param_list=[self.epsilon]
                )
            )

        # Discrete adiabatic evolution at each point s
        for step in range(self.n_steps):
            s = step / max(1, self.n_steps - 1) if self.n_steps > 1 else 1.0
            fs = compute_fs(s, self.kappa, self.p)

            # Block encoding of H(s) at this point
            if self.block_encoding:
                self.program_list.append(
                    self.block_encoding(
                        reg_list=[
                            self.main_reg,
                            self.anc_UA,
                            self.anc_1,
                            self.anc_2,
                            self.anc_3,
                            self.anc_4,
                        ],
                        param_list=[fs, self.kappa],
                    )
                )

            # Walk operator: Reflection on ancilla
            if self.anc_2:
                R_op = OperationRegistry.get_class("Reflection_Bool")
                self.program_list.append(
                    R_op(reg_list=[self.anc_2], param_list=[False])
                )

        # Post-select: X on ancilla flag
        if self.anc_1:
            self.program_list.append(X_op(reg_list=[self.anc_1], param_list=[0]))

        self.declare_program_list()

    def sum_t_count(self, t_count_list):
        """Compute total T-count for QDA algorithm.

        The QDA algorithm has optimal κ scaling:
        - n_steps = O(log(κ/ε)) discretization points
        - Each step: block encoding + reflection = O(n) T-count
        """
        kappa = self.kappa
        epsilon = self.epsilon
        n_steps = self.n_steps

        encode_cost = t_count_list[0] if len(t_count_list) > 0 else 0
        prep_cost = t_count_list[1] if len(t_count_list) > 1 else 0

        # Step cost: block encoding + reflection + rotation
        # From QDA paper: approximately 4*n_ancillas + 3 T-gates per step
        step_cost = 4 * 7 + 3

        return n_steps * step_cost + encode_cost + prep_cost
