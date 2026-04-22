"""pyqres algorithms module.

This module provides resource estimation for quantum algorithms.
Mathematical components are imported from PySparQ for consistency.
"""

from .amplitude_amplification import AmplitudeAmplification
from .tomography import Tomography
from .linear_solver import LinearSolver
from .shor import ShorFactor, SemiClassicalShor, factor

# CKS solver - local implementation with PySparQ imports
from .cks_solver import (
    CKSLinearSolver,
    # Re-exported from PySparQ for convenience
    SparseMatrix,
    SparseMatrixData,
    ChebyshevPolynomialCoefficient,
    get_coef_positive_only,
    get_coef_common,
    make_walk_angle_func,
)

# QDA solver - local implementation with PySparQ imports
from .qda_solver import (
    QDALinearSolver,
    # Re-exported from PySparQ for convenience
    compute_fs,
    compute_rotation_matrix,
    chebyshev_T,
    dolph_chebyshev,
    compute_fourier_coeffs,
    calculate_angles,
    classical_to_quantum,
)

# Import additional classes from PySparQ for convenience
from pysparq.algorithms import BlockEncoding, StatePreparation
from pysparq.algorithms.cks_solver import cks_solve, LCUContainer
from pysparq.algorithms.qda_solver import (
    qda_solve,
    BlockEncodingHs,
    BlockEncodingHsPD,
    WalkS,
    LCU,
    Filtering,
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
    "SparseMatrix",
    "SparseMatrixData",
    "ChebyshevPolynomialCoefficient",
    "get_coef_positive_only",
    "get_coef_common",
    "make_walk_angle_func",
    "cks_solve",
    "LCUContainer",
    # QDA
    "QDALinearSolver",
    "compute_fs",
    "compute_rotation_matrix",
    "chebyshev_T",
    "dolph_chebyshev",
    "compute_fourier_coeffs",
    "calculate_angles",
    "classical_to_quantum",
    "qda_solve",
    "BlockEncodingHs",
    "BlockEncodingHsPD",
    "WalkS",
    "LCU",
    "Filtering",
    "BlockEncoding",
    "StatePreparation",
]
