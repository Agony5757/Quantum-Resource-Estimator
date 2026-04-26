"""pyqres algorithms module.

This module provides resource estimation for quantum algorithms.
Mathematical components are imported from PySparQ for consistency.

Quantum operations (Block Encoding, State Preparation) are now
implemented natively via DSL in the generated/ directory.
"""

from .amplitude_amplification import AmplitudeAmplification
from .tomography import Tomography
from .linear_solver import LinearSolver
from .shor import ShorFactor, SemiClassicalShor, factor

# CKS solver - math functions from PySparQ (used in DSL python blocks)
from .cks_solver import CKSLinearSolver

# QDA solver - math functions from PySparQ (used in DSL python blocks)
from .qda_solver import QDALinearSolver

# Re-export math helper functions from PySparQ (for use in DSL python blocks)
from pysparq.algorithms.cks_solver import (
    ChebyshevPolynomialCoefficient,
    SparseMatrix,
    SparseMatrixData,
    get_coef_positive_only,
    get_coef_common,
    make_walk_angle_func,
)

from pysparq.algorithms.qda_solver import (
    compute_fs,
    compute_rotation_matrix,
    chebyshev_T,
    dolph_chebyshev,
    compute_fourier_coeffs,
    calculate_angles,
    classical_to_quantum,
)

# QRAM utilities for state preparation (local implementation)
from ..utils.qram_utils import (
    pow2,
    make_complement,
    get_complement,
    column_flatten,
    scale_and_convert_vector,
    make_vector_tree,
    make_func,
    make_func_inv,
)

__all__ = [
    "AmplitudeAmplification",
    "Tomography",
    "LinearSolver",
    "ShorFactor",
    "SemiClassicalShor",
    "factor",
    # CKS
    "CKSLinearSolver",
    # CKS math helpers
    "SparseMatrix",
    "SparseMatrixData",
    "ChebyshevPolynomialCoefficient",
    "get_coef_positive_only",
    "get_coef_common",
    "make_walk_angle_func",
    # QDA
    "QDALinearSolver",
    # QDA math helpers
    "compute_fs",
    "compute_rotation_matrix",
    "chebyshev_T",
    "dolph_chebyshev",
    "compute_fourier_coeffs",
    "calculate_angles",
    "classical_to_quantum",
    # QRAM utilities
    "pow2",
    "make_complement",
    "get_complement",
    "column_flatten",
    "scale_and_convert_vector",
    "make_vector_tree",
    "make_func",
    "make_func_inv",
]
