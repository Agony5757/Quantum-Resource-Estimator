"""Tests for Grover search algorithm (pyqres.algorithms.grover)."""

import pytest
from pyqres.algorithms.grover import (
    GroverOracle, DiffusionOperator, GroverOperator,
    GroverSearch, grover_search,
)
from pyqres.core.operation import AbstractComposite, StandardComposite, Primitive


class TestGroverPrimitives:
    def test_grover_oracle_is_primitive(self):
        assert issubclass(GroverOracle, Primitive)

    def test_grover_oracle_self_conjugate(self):
        assert getattr(GroverOracle, '__self_conjugate__', False)

    def test_grover_oracle_t_count(self):
        op = GroverOracle(
            reg_list=['addr', 'data', 'search'],
            param_list=None,
            addr_reg='addr', data_reg='data', search_reg='search',
        )
        tc = op.t_count()
        assert isinstance(tc, int)
        assert tc >= 0

    def test_diffusion_operator_is_primitive(self):
        assert issubclass(DiffusionOperator, Primitive)

    def test_diffusion_self_conjugate(self):
        assert getattr(DiffusionOperator, '__self_conjugate__', False)

    def test_diffusion_t_count(self):
        from pyqres.core.metadata import RegisterMetadata
        RegisterMetadata.get_register_metadata().declare_register('addr', 3)
        op = DiffusionOperator(['addr'])
        tc = op.t_count()
        assert isinstance(tc, int)
        assert tc > 0  # ZeroConditionalPhaseFlip has non-zero cost

    def test_grover_operator_is_standard_composite(self):
        assert issubclass(GroverOperator, StandardComposite)

    def test_grover_operator_self_conjugate(self):
        assert getattr(GroverOperator, '__self_conjugate__', False)


class TestGroverSearch:
    def test_grover_search_is_abstract_composite(self):
        assert issubclass(GroverSearch, AbstractComposite)

    def test_grover_search_builds_program_list(self):
        from pyqres.core.metadata import RegisterMetadata
        RegisterMetadata.get_register_metadata().declare_register('addr', 3)
        RegisterMetadata.get_register_metadata().declare_register('data', 32)
        RegisterMetadata.get_register_metadata().declare_register('search', 32)

        search = GroverSearch(
            reg_list=['addr', 'data', 'search'],
            param_list=[[1, 2, 3, 4], 2, None, None],
        )
        assert len(search.program_list) > 0
        assert search.n_iterations >= 1

    def test_grover_search_iteration_count_auto(self):
        from pyqres.core.metadata import RegisterMetadata
        RegisterMetadata.get_register_metadata().declare_register('addr', 3)
        RegisterMetadata.get_register_metadata().declare_register('data', 8)
        RegisterMetadata.get_register_metadata().declare_register('search', 8)

        # N=4, auto iterations = floor(pi/4 * sqrt(4)) = floor(1.57) = 1
        search = GroverSearch(
            reg_list=['addr', 'data', 'search'],
            param_list=[[1, 2, 3, 4], 2, None, None],
        )
        assert search.n_iterations == 1

    def test_grover_search_iteration_count_explicit(self):
        from pyqres.core.metadata import RegisterMetadata
        RegisterMetadata.get_register_metadata().declare_register('addr', 3)
        RegisterMetadata.get_register_metadata().declare_register('data', 8)
        RegisterMetadata.get_register_metadata().declare_register('search', 8)

        search = GroverSearch(
            reg_list=['addr', 'data', 'search'],
            param_list=[[1, 2, 3, 4], 2, 5, 8],
        )
        assert search.n_iterations == 5

    def test_grover_search_sum_t_count(self):
        from pyqres.core.metadata import RegisterMetadata
        RegisterMetadata.get_register_metadata().declare_register('addr', 3)
        RegisterMetadata.get_register_metadata().declare_register('data', 8)
        RegisterMetadata.get_register_metadata().declare_register('search', 8)

        search = GroverSearch(
            reg_list=['addr', 'data', 'search'],
            param_list=[[1, 2, 3, 4], 2, 2, 8],
        )
        # GroverSearch.t_count() uses sum_t_count() with explicit formula:
        # With memory=[1,2,3,4], n_bits=2 (ceil(log2(4))), data_size=8, n_iters=2
        # per_iter = oracle + diffusion = (4*data_size + 4*n_bits + 1) + 2*(4*n_bits+1)
        #         = (32 + 8 + 1) + 2*9 = 41 + 18 = 59
        # total = 2 * 59 = 118
        tc = search.t_count()
        assert tc == 118

    def test_grover_search_n_bits_computed(self):
        from pyqres.core.metadata import RegisterMetadata
        RegisterMetadata.get_register_metadata().declare_register('addr', 3)
        RegisterMetadata.get_register_metadata().declare_register('data', 8)
        RegisterMetadata.get_register_metadata().declare_register('search', 8)

        search = GroverSearch(
            reg_list=['addr', 'data', 'search'],
            param_list=[[1, 2, 3, 4], 2, None, None],
        )
        assert search.n_bits == 2  # ceil(log2(4)) = 2
