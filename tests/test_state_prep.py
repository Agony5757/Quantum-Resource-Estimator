"""Tests for state preparation algorithms (pyqres.algorithms.state_prep)."""

import pytest
import math
from pyqres.algorithms.state_prep import (
    StatePrepViaQRAM, StatePreparation,
    make_vector_tree, make_func, make_func_inv,
    pow2, get_complement, make_complement,
)
from pyqres.core.operation import StandardComposite


class TestUtilityFunctions:
    def test_pow2(self):
        assert pow2(0) == 1
        assert pow2(1) == 2
        assert pow2(10) == 1024

    def test_get_complement_positive(self):
        assert get_complement(5, 8) == 5

    def test_get_complement_negative(self):
        assert get_complement(253, 8) == -3  # 0xFD = -3 in 8-bit two's complement

    def test_get_complement_zero(self):
        assert get_complement(0, 8) == 0

    def test_get_complement_zero_bits(self):
        assert get_complement(123, 0) == 0

    def test_make_complement_positive(self):
        assert make_complement(5, 8) == 5

    def test_make_complement_negative(self):
        assert make_complement(-3, 8) == 253  # -3 in 8-bit two's complement

    def test_make_vector_tree_4_elements(self):
        tree = make_vector_tree([0, 0, 0, 0], data_size=4)
        assert len(tree) > 4  # Tree is larger than original
        assert tree[-1] == 0  # Trailing 0

    def test_make_func_zero(self):
        mat = make_func(0, 4)
        # theta = 0 → [[1,0],[0,1]]
        assert abs(mat[0] - 1) < 1e-10
        assert abs(mat[1]) < 1e-10
        assert abs(mat[2]) < 1e-10
        assert abs(mat[3] - 1) < 1e-10

    def test_make_func_non_zero(self):
        mat = make_func(8, 4)  # theta = 8/16 * 2*pi = pi
        assert abs(abs(mat[0]) - 1) < 1e-10  # cos(pi) = -1
        assert abs(mat[1]) < 1e-10  # -sin(pi) = 0

    def test_make_func_inv_zero(self):
        mat = make_func_inv(0, 4)
        assert abs(mat[0] - 1) < 1e-10
        assert abs(mat[1]) < 1e-10
        assert abs(mat[2]) < 1e-10
        assert abs(mat[3] - 1) < 1e-10


class TestStatePrepViaQRAM:
    def test_is_standard_composite(self):
        assert issubclass(StatePrepViaQRAM, StandardComposite)

    def test_builds_program_list(self):
        from pyqres.core.metadata import RegisterMetadata
        RegisterMetadata.get_register_metadata().declare_register('main', 3)

        sp = StatePrepViaQRAM(
            qram=None,
            work_qubit='main',
            data_size=8,
            rational_size=4,
        )
        assert len(sp.program_list) > 0
        assert sp.addr_size == 3
        assert sp.data_size == 8
        assert sp.rational_size == 4

    def test_addr_size_from_reg_metadata(self):
        from pyqres.core.metadata import RegisterMetadata
        RegisterMetadata.get_register_metadata().declare_register('wq', 5)

        sp = StatePrepViaQRAM(
            qram=None, work_qubit='wq',
            data_size=8, rational_size=4,
        )
        assert sp.addr_size == 5


class TestStatePreparation:
    def test_init(self):
        sp = StatePreparation(qubit_number=3, data_size=8, data_range=4)
        assert sp.qubit_number == 3
        assert sp.data_size == 8
        assert sp.data_range == 4
        assert sp.rational_size == min(50, 8 * 2)

    def test_rational_size_capped_at_50(self):
        sp = StatePreparation(qubit_number=10, data_size=40, data_range=10)
        assert sp.rational_size == 50

    def test_set_distribution_length_check(self):
        sp = StatePreparation(qubit_number=3)  # expects 8 elements
        sp.set_distribution([1, 2, 3, 4, 5, 6, 7, 8])
        assert len(sp.dist) == 8

    def test_set_distribution_wrong_length_raises(self):
        sp = StatePreparation(qubit_number=3)  # expects 8 elements
        with pytest.raises(ValueError):
            sp.set_distribution([1, 2, 3])  # wrong length

    def test_get_real_dist_normalizes(self):
        from pyqres.core.metadata import RegisterMetadata
        RegisterMetadata.get_register_metadata().declare_register('main_reg', 4)

        sp = StatePreparation(qubit_number=2, data_size=8)
        sp.set_distribution([1, 2, 3, 4])
        dist = sp.get_real_dist()
        assert len(dist) == 4
        total = sum(abs(x) ** 2 for x in dist)
        assert abs(total - 1.0) < 1e-10  # normalized

    def test_get_real_dist_zeros(self):
        from pyqres.core.metadata import RegisterMetadata
        RegisterMetadata.get_register_metadata().declare_register('main_reg', 4)

        sp = StatePreparation(qubit_number=2, data_size=8)
        sp.set_distribution([0, 0, 0, 0])
        dist = sp.get_real_dist()
        assert all(abs(x) < 1e-10 for x in dist)
