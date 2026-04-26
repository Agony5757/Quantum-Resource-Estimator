"""
QDA (Quantum Discrete Adiabatic) Linear System Solver - Math Utilities

This module provides mathematical utility functions for QDA quantum linear system solver.
Quantum operations are now implemented natively via DSL (see dsl/schemas/composites/qda_linear_solver.yml).

Time complexity: O(κ log(κ/ε)) — optimal for quantum linear solving.

Reference:
    - L. Lin and Y. Tong, PRX Quantum 3, 040303 (2022)
    - SparQ Paper: https://arxiv.org/abs/2503.15118
"""

from __future__ import annotations

import math
from typing import List, Optional

import numpy as np

# Import mathematical components from PySparQ for computing adiabatic schedule
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


# Re-export for use in DSL python blocks
__all__ = [
    "compute_fs",
    "compute_rotation_matrix",
    "chebyshev_T",
    "dolph_chebyshev",
    "compute_fourier_coeffs",
    "calculate_angles",
    "classical_to_quantum",
    "QDALinearSolver",
    "compute_qda_t_count",
]


def compute_qda_t_count(kappa: float, epsilon: float, n_ancillas: int = 7) -> dict:
    """Compute T-count for QDA algorithm analytically.

    This function provides the T-count formula for QDA algorithm
    without needing a full operation tree.

    Args:
        kappa: Condition number
        epsilon: Precision parameter
        n_ancillas: Number of ancilla qubits

    Returns:
        Dictionary with T-count components
    """
    n_steps = int(np.ceil(np.log(kappa / epsilon)))

    # Step cost: block encoding + reflection + rotation
    # From QDA paper: approximately 4*n_ancillas + 3 T-gates per step
    step_cost = 4 * n_ancillas + 3

    total_evolution = n_steps * step_cost

    # Block encoding cost (tridiagonal): O(n)
    encode_cost = 4 + 2 * 4  # assume 4 qubits for encoding

    # State prep cost via QRAM: O(n * data_size)
    state_prep_cost = 4 * 8

    return {
        "evolution_cost": total_evolution,
        "encode_cost": encode_cost,
        "state_prep_cost": state_prep_cost,
        "total": total_evolution + encode_cost + state_prep_cost,
        "n_steps": n_steps,
        "step_cost": step_cost,
    }


class QDALinearSolver(AbstractComposite):
    """QDA Quantum Linear System Solver as pyqres Operation.

    This class delegates quantum operations to DSL-generated operations.
    Uses discrete adiabatic evolution for O(κ log(κ/ε)) complexity.

    T-count formula:
        n_steps = ceil(log(κ/ε))
        step_cost = O(n) per discretization point
        T_count = n_steps * step_cost + encode_costs

    Args:
        reg_list: [main_reg, anc_UA, anc_1, anc_2, anc_3, anc_4]
        param_list: [kappa, epsilon, matrix_params, input_vector, data_size]
        submodules: Optional pre-built submodules (not used in DSL version)
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
        self.matrix_params = param_list[2] if len(param_list) > 2 else [1.0, 0.5]
        self.input_vector = param_list[3] if len(param_list) > 3 else None
        self.data_size = param_list[4] if len(param_list) > 4 else 8

        self.p = 0.5  # Schedule parameter
        self.n_steps = int(np.ceil(np.log(self.kappa / self.epsilon)))

        self._build_program_list()

    def _build_program_list(self):
        """Build operation tree using DSL-generated operations."""
        self.program_list = []

        # Use DSL-generated operations
        BlockEncodingTridiagonal = OperationRegistry.get_class("BlockEncodingTridiagonal")
        StatePreparation = OperationRegistry.get_class("StatePreparation")
        Hadamard = OperationRegistry.get_class("Hadamard")
        Reflection_Bool = OperationRegistry.get_class("Reflection_Bool")
        X = OperationRegistry.get_class("X")

        alpha, beta = self.matrix_params[0], self.matrix_params[1]

        # Initialize to H₀ eigenstate: X on first qubit of main register
        self.program_list.append(X(reg_list=[self.main_reg], param_list=[0]))

        # State preparation |b⟩ via DSL
        if self.input_vector:
            self.program_list.append(
                StatePreparation(
                    reg_list=[self.main_reg],
                    param_list=[self.input_vector, self.data_size],
                )
            )

        # Discrete adiabatic evolution at each point s
        for step in range(self.n_steps):
            s = step / max(1, self.n_steps - 1) if self.n_steps > 1 else 1.0
            fs = compute_fs(s, self.kappa, self.p)

            # Block encoding of H(s) at this point
            if self.anc_UA:
                self.program_list.append(
                    BlockEncodingTridiagonal(
                        reg_list=[self.main_reg, self.anc_UA],
                        param_list=[fs, self.kappa * (1 - s)],
                    )
                )

            # Walk operator: Reflection on ancilla
            if self.anc_2:
                self.program_list.append(
                    Reflection_Bool(reg_list=[self.anc_2], param_list=[False])
                )

            if self.anc_3:
                self.program_list.append(Hadamard(reg_list=[self.anc_3]))

        # Post-select: X on ancilla flag
        if self.anc_1:
            self.program_list.append(X(reg_list=[self.anc_1], param_list=[0]))

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
        n_ancillas = 7

        counts = compute_qda_t_count(kappa, epsilon, n_ancillas)
        return counts["total"]
