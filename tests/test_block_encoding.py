"""Tests for BlockEncoding implementations in PySparQ."""

import pytest
import numpy as np
import pysparq as ps

from pysparq.algorithms.block_encoding import (
    BlockEncodingTridiagonal,
    BlockEncodingQRAM,
    StatePreparation,
    BlockEncoding,
    _is_tridiagonal,
    _extract_tridiagonal_params,
)


@pytest.fixture(autouse=True)
def clean_pysparq():
    """Clean PySparQ state before/after each test."""
    ps.System.clear()
    yield
    ps.System.clear()


class TestBlockEncodingTridiagonal:
    """Tests for tridiagonal block encoding."""

    def test_create_tridiagonal_encoding(self):
        """Test creating tridiagonal block encoding."""
        alpha, beta = 0.5, 0.25

        ps.System.add_register("main", ps.UnsignedInteger, 2)
        ps.System.add_register("anc", ps.UnsignedInteger, 2)

        enc = BlockEncodingTridiagonal(alpha, beta, "main", "anc")

        assert enc.alpha == alpha
        assert enc.beta == beta
        assert len(enc.prep_state) == 4

    def test_prep_state_normalization(self):
        """Test that prep_state is normalized."""
        enc = BlockEncodingTridiagonal(0.5, 0.25, "main", "anc")

        # Sum of squares should be approximately 1
        total = sum(abs(x) ** 2 for x in enc.prep_state)
        assert abs(total - 1.0) < 1e-10

    def test_tridiagonal_simulation(self):
        """Test tridiagonal block encoding simulation."""
        # anc register needs size matching prep_state (4 elements = 2 qubits)
        ps.System.add_register("main", ps.UnsignedInteger, 2)
        ps.System.add_register("anc", ps.UnsignedInteger, 2)

        enc = BlockEncodingTridiagonal(0.5, 0.25, "main", "anc")
        state = ps.SparseState()

        # Should not raise
        enc(state)
        assert state.size() >= 1

    def test_conditioned_by_all_ones(self):
        """Test conditioning on register."""
        ps.System.add_register("main", ps.UnsignedInteger, 2)
        ps.System.add_register("anc", ps.UnsignedInteger, 2)
        ps.System.add_register("ctrl", ps.Boolean, 1)

        enc = BlockEncodingTridiagonal(0.5, 0.25, "main", "anc")
        enc_cond = enc.conditioned_by_all_ones("ctrl")

        assert enc_cond._condition_regs == ["ctrl"]

    def test_edge_case_zero_alpha(self):
        """Test edge case with zero alpha."""
        enc = BlockEncodingTridiagonal(0.0, 0.5, "main", "anc")

        assert enc.alpha == 0.0
        assert enc.beta == 0.5
        assert len(enc.prep_state) == 4


class TestBlockEncodingQRAM:
    """Tests for QRAM-based block encoding."""

    def test_create_qram_encoding(self):
        """Test creating QRAM block encoding."""
        A = np.array([[2, 1], [1, 2]], dtype=float)

        ps.System.add_register("main", ps.UnsignedInteger, 2)
        ps.System.add_register("anc", ps.UnsignedInteger, 4)

        enc = BlockEncodingQRAM(A, main_reg="main", anc_reg="anc")

        assert enc.sparse_mat.n_row == 2

    def test_qram_encoding_different_sizes(self):
        """Test QRAM encoding with different matrix sizes."""
        for n in [2, 3, 4]:
            ps.System.clear()
            A = np.eye(n, dtype=float)

            ps.System.add_register("main", ps.UnsignedInteger, n)
            ps.System.add_register("anc", ps.UnsignedInteger, n * 2)

            enc = BlockEncodingQRAM(A, main_reg="main", anc_reg="anc")
            assert enc.sparse_mat.n_row == n


class TestStatePreparation:
    """Tests for state preparation."""

    def test_create_state_prep(self):
        """Test creating state preparation."""
        b = np.array([1.0, 1.0]) / np.sqrt(2)

        # 2 elements needs 1 qubit (size 2)
        ps.System.add_register("main", ps.UnsignedInteger, 1)

        prep = StatePreparation(b, "main")

        assert len(prep.prep_state) == 2

    def test_state_prep_normalization(self):
        """Test that prepared state is normalized."""
        b = np.array([1.0, 2.0, 3.0, 4.0])  # 4 elements
        prep = StatePreparation(b, "main")

        norm = np.linalg.norm(prep.prep_state)
        assert abs(norm - 1.0) < 1e-10

    def test_state_prep_simulation(self):
        """Test state preparation simulation."""
        b = np.array([1.0, 1.0]) / np.sqrt(2)

        # 2 elements needs 1 qubit (size 2)
        ps.System.add_register("main", ps.UnsignedInteger, 1)

        prep = StatePreparation(b, "main")
        state = ps.SparseState()

        prep(state)
        assert state.size() >= 1

    def test_state_prep_with_conditioning(self):
        """Test conditioned state preparation."""
        b = np.array([1.0, 1.0]) / np.sqrt(2)

        # 2 elements needs 1 qubit (size 2)
        ps.System.add_register("main", ps.UnsignedInteger, 1)
        ps.System.add_register("ctrl", ps.Boolean, 1)

        prep = StatePreparation(b, "main").conditioned_by_all_ones("ctrl")

        assert prep._condition_regs == ["ctrl"]


class TestBlockEncodingFactory:
    """Tests for BlockEncoding factory function."""

    def test_factory_tridiagonal_detection(self):
        """Test that factory detects tridiagonal matrices."""
        A = np.array(
            [[2, 1, 0], [1, 2, 1], [0, 1, 2]], dtype=float
        )

        enc = BlockEncoding(A, main_reg="main", anc_reg="anc")

        assert isinstance(enc, BlockEncodingTridiagonal)

    def test_factory_dense_matrix(self):
        """Test factory with dense matrix."""
        A = np.array([[2, 1], [1, 2]], dtype=float)

        enc = BlockEncoding(A, main_reg="main", anc_reg="anc")

        # Should return some kind of block encoding
        assert isinstance(enc, (BlockEncodingTridiagonal, BlockEncodingQRAM))


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_is_tridiagonal_true(self):
        """Test tridiagonal detection for tridiagonal matrix."""
        A = np.array([[2, 1, 0], [1, 2, 1], [0, 1, 2]], dtype=float)

        assert _is_tridiagonal(A) is True

    def test_is_tridiagonal_false(self):
        """Test tridiagonal detection for non-tridiagonal matrix."""
        A = np.array([[2, 1, 1], [1, 2, 1], [0, 1, 2]], dtype=float)

        assert _is_tridiagonal(A) is False

    def test_extract_tridiagonal_params(self):
        """Test extracting tridiagonal parameters."""
        A = np.array([[2, 1, 0], [1, 2, 1], [0, 1, 2]], dtype=float)

        alpha, beta = _extract_tridiagonal_params(A)

        assert alpha == 2.0
        assert beta == 1.0


class TestPySparQCompatibility:
    """Tests verifying compatibility with PySparQ."""

    def test_import_from_pysparq(self):
        """Test that imports work from pysparq.algorithms."""
        from pysparq.algorithms import BlockEncoding, StatePreparation

        assert BlockEncoding is not None
        assert StatePreparation is not None

    def test_cks_solver_imports(self):
        """Test that CKS solver components can be imported."""
        from pysparq.algorithms.cks_solver import (
            ChebyshevPolynomialCoefficient,
            SparseMatrix,
        )

        cheb = ChebyshevPolynomialCoefficient(10)
        assert cheb.b == 10

        A = np.array([[1, 2], [2, 1]])
        mat = SparseMatrix.from_dense(A, data_size=8)
        assert mat.n_row == 2

    def test_qda_solver_imports(self):
        """Test that QDA solver components can be imported."""
        from pysparq.algorithms.qda_solver import (
            compute_fs,
            compute_rotation_matrix,
        )

        fs = compute_fs(0.5, 10.0, 0.5)
        assert 0 <= fs <= 1

        R = compute_rotation_matrix(0.5)
        assert len(R) == 4
