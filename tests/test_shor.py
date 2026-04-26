"""Tests for Shor factorization algorithm (pyqres.algorithms.shor)."""

import pytest
import math

from pyqres.algorithms.shor import (
    general_expmod, find_best_fraction, compute_period, check_period,
    shor_postprocess, ShorExecutionFailed,
    ModMul, ExpMod,
    SemiClassicalShor, Shor,
    factor, factor_full_quantum,
)
from pyqres.core.operation import Primitive, AbstractComposite
from pyqres.core.metadata import RegisterMetadata


class TestHelpers:
    def test_general_expmod_known_values(self):
        assert general_expmod(2, 10, 15) == 4   # 2^10 mod 15 = 1024 mod 15 = 4
        assert general_expmod(7, 3, 15) == 13  # 7^3 mod 15 = 343 mod 15 = 13
        assert general_expmod(2, 0, 15) == 1   # a^0 = 1
        assert general_expmod(5, 1, 21) == 5   # a^1 = a
        assert general_expmod(3, 4, 10) == 1   # 3^4 = 81 mod 10 = 1
        assert general_expmod(2, 8, 17) == 1   # 2^8 = 256 mod 17 = 1

    def test_general_expmod_identity(self):
        assert general_expmod(2, 4, 5) == 1
        assert general_expmod(3, 6, 7) == 1

    def test_general_expmod_large_exponent(self):
        result = general_expmod(2, 20, 15)
        assert result == pow(2, 20, 15)

    def test_find_best_fraction_exact(self):
        r, c = find_best_fraction(4, 16, 15)
        assert r == 4 and c == 1  # 4/16 = 1/4

    def test_find_best_fraction_simple(self):
        r, c = find_best_fraction(1, 8, 15)
        assert r == 8 and c == 1  # 1/8 = 1/8

    def test_find_best_fraction_bounded(self):
        for _ in range(10):
            y = 37  # arbitrary
            Q = 256
            N = 50
            r, c = find_best_fraction(y, Q, N)
            assert r <= N
            assert c < r

    def test_compute_period_valid(self):
        # y=64, size=8 → 1/4 fraction → r=4
        r = compute_period(64, 8, 15)
        assert 0 < r <= 15

    def test_compute_period_zero_raises(self):
        with pytest.raises(ShorExecutionFailed):
            compute_period(0, 8, 15)

    def test_check_period_odd_raises(self):
        with pytest.raises(ShorExecutionFailed):
            check_period(3, 2, 15)  # odd period

    def test_check_period_too_large_raises(self):
        with pytest.raises(ShorExecutionFailed):
            check_period(100, 2, 15)  # r > N

    def test_check_period_valid(self):
        check_period(4, 2, 15)  # valid: r=4, a=2, N=15

    def test_shor_postprocess_factors_15_y64(self):
        # y=64 → c/r=1/4 → r=4 → factors of 15 are 3 and 5
        p, q = shor_postprocess(64, 8, 2, 15)
        assert p * q == 15
        assert {p, q} == {3, 5}

    def test_shor_postprocess_factors_15_y192(self):
        # y=192 → c/r=3/4 → r=4 → factors of 15 are 3 and 5
        p, q = shor_postprocess(192, 8, 2, 15)
        assert p * q == 15
        assert {p, q} == {3, 5}

    def test_shor_postprocess_invalid_y_returns_one(self):
        p, q = shor_postprocess(0, 8, 2, 15)
        assert p == 1 and q == 1


class TestModMul:
    def test_modmul_is_primitive(self):
        assert issubclass(ModMul, Primitive)

    def test_modmul_not_self_conjugate(self):
        assert not getattr(ModMul, '__self_conjugate__', True)

    def test_modmul_opnum(self):
        mm = ModMul(reg_list=["r"], param_list=[2, 1, 15])
        assert mm.opnum == 4  # a=2, x=1 → 2^(2^1)=4 mod 15

    def test_modmul_opnum_x0(self):
        mm = ModMul(reg_list=["r"], param_list=[2, 0, 15])
        assert mm.opnum == 2  # 2^(2^0)=2 mod 15

    def test_modmul_opnum_x2(self):
        mm = ModMul(reg_list=["r"], param_list=[2, 2, 15])
        assert mm.opnum == 1  # 2^(2^2)=2^4=16 mod 15 = 1

    def test_modmul_t_count_positive(self):
        RegisterMetadata.get_register_metadata().declare_register("r", 4)
        mm = ModMul(reg_list=["r"], param_list=[2, 1, 15])
        tc = mm.t_count()
        assert isinstance(tc, int)
        assert tc > 0  # Has non-trivial T-cost (controlled Toffoli)

    def test_modmul_t_count_with_controls(self):
        RegisterMetadata.get_register_metadata().declare_register("r", 4)
        RegisterMetadata.get_register_metadata().declare_register("ctrl", 1)
        mm = ModMul(reg_list=["r"], param_list=[2, 1, 15])
        mm.controllers = {'conditioned_by_all_ones': ['ctrl']}
        tc = mm.t_count()
        assert isinstance(tc, int)
        assert tc > 0


class TestExpMod:
    def test_expmod_is_primitive(self):
        assert issubclass(ExpMod, Primitive)

    def test_expmod_self_conjugate(self):
        # XOR semantics: f(f(x)) = 0, so self-adjoint in quantum sense
        assert getattr(ExpMod, '__self_conjugate__', False)

    def test_expmod_axmodn_period(self):
        RegisterMetadata.get_register_metadata().declare_register("x", 4)
        RegisterMetadata.get_register_metadata().declare_register("z", 4)
        em = ExpMod(reg_list=["x", "z"], param_list=[2, 15, 4])
        assert em.axmodn[0] == 1
        assert em.period == 4  # 2^k mod 15 has period 4

    def test_expmod_t_count_positive(self):
        RegisterMetadata.get_register_metadata().declare_register("x", 4)
        RegisterMetadata.get_register_metadata().declare_register("z", 4)
        em = ExpMod(reg_list=["x", "z"], param_list=[2, 15, 4])
        tc = em.t_count()
        assert isinstance(tc, int)
        assert tc > 0


class TestSemiClassicalShor:
    def test_init_coprime(self):
        RegisterMetadata.get_register_metadata().declare_register("anc", 4)
        shor = SemiClassicalShor(reg_list=["anc"], param_list=[2, 15])
        assert shor.a == 2
        assert shor.N == 15
        assert shor.n == 4   # ceil(log2 15) + 1 = 4
        assert shor.size == 8  # 2 * n = 8

    def test_init_non_coprime_raises(self):
        RegisterMetadata.get_register_metadata().declare_register("anc", 4)
        with pytest.raises(ValueError):
            SemiClassicalShor(reg_list=["anc"], param_list=[3, 15])  # gcd=3

    def test_is_abstract_composite(self):
        RegisterMetadata.get_register_metadata().declare_register("anc", 4)
        shor = SemiClassicalShor(reg_list=["anc"], param_list=[2, 15])
        assert issubclass(type(shor), AbstractComposite)

    def test_program_list_not_empty(self):
        RegisterMetadata.get_register_metadata().declare_register("anc", 4)
        shor = SemiClassicalShor(reg_list=["anc"], param_list=[2, 15])
        assert len(shor.program_list) > 0

    def test_t_count_positive(self):
        RegisterMetadata.get_register_metadata().declare_register("anc", 4)
        shor = SemiClassicalShor(reg_list=["anc"], param_list=[2, 15])
        tc = shor.t_count()
        assert isinstance(tc, int)
        assert tc > 0

    def test_t_count_formula_consistency(self):
        """T-count should be deterministic regardless of t_count_list content."""
        RegisterMetadata.get_register_metadata().declare_register("anc", 4)
        shor = SemiClassicalShor(reg_list=["anc"], param_list=[2, 15])
        tc1 = shor.sum_t_count([0] * len(shor.program_list))
        tc2 = shor.sum_t_count([100] * len(shor.program_list))
        assert tc1 == tc2  # formula is explicit, not summed from children


class TestShor:
    def test_init(self):
        RegisterMetadata.get_register_metadata().declare_register("work", 8)
        RegisterMetadata.get_register_metadata().declare_register("anc", 4)
        s = Shor(reg_list=["work", "anc"], param_list=[2, 15, 4])
        assert s.a == 2
        assert s.N == 15
        assert s.period == 4
        assert s.n == 4
        assert s.size == 8

    def test_is_abstract_composite(self):
        RegisterMetadata.get_register_metadata().declare_register("work", 8)
        RegisterMetadata.get_register_metadata().declare_register("anc", 4)
        s = Shor(reg_list=["work", "anc"], param_list=[2, 15, 4])
        assert issubclass(type(s), AbstractComposite)

    def test_program_list_three_ops(self):
        RegisterMetadata.get_register_metadata().declare_register("work", 8)
        RegisterMetadata.get_register_metadata().declare_register("anc", 4)
        s = Shor(reg_list=["work", "anc"], param_list=[2, 15, 4])
        # Hadamard + ExpMod + InverseQFT
        assert len(s.program_list) == 3

    def test_program_list_correct_ops(self):
        RegisterMetadata.get_register_metadata().declare_register("work", 8)
        RegisterMetadata.get_register_metadata().declare_register("anc", 4)
        s = Shor(reg_list=["work", "anc"], param_list=[2, 15, 4])
        from pyqres.primitives import Hadamard, InverseQFT
        from pyqres.algorithms.shor import ExpMod as ExpModPrim
        prog = s.program_list
        assert isinstance(prog[0], Hadamard)
        assert isinstance(prog[1], ExpModPrim)
        assert isinstance(prog[2], InverseQFT)

    def test_t_count_positive(self):
        RegisterMetadata.get_register_metadata().declare_register("work", 8)
        RegisterMetadata.get_register_metadata().declare_register("anc", 4)
        s = Shor(reg_list=["work", "anc"], param_list=[2, 15, 4])
        tc = s.t_count()
        assert isinstance(tc, int)
        assert tc > 0

    def test_period_auto_computed(self):
        RegisterMetadata.get_register_metadata().declare_register("work", 8)
        RegisterMetadata.get_register_metadata().declare_register("anc", 4)
        s = Shor(reg_list=["work", "anc"], param_list=[2, 15])
        assert s.period == 4  # 2^k mod 15 has period 4


class TestConvenienceFunctions:
    def test_factor_even_number(self):
        p, q = factor(14)
        assert p == 2 and q == 7

    def test_factor_with_gcd_not_one(self):
        p, q = factor(15, a=3)  # gcd(3,15)=3
        assert p == 3 and q == 5

    def test_factor_invalid_input(self):
        with pytest.raises(ValueError):
            factor(1)
        with pytest.raises(ValueError):
            factor(0)

    def test_factor_returns_tuple(self):
        p, q = factor(21)
        assert isinstance(p, int)
        assert isinstance(q, int)

    def test_factor_full_quantum_even(self):
        p, q = factor_full_quantum(14)
        assert p == 2 and q == 7

    def test_factor_full_quantum_invalid(self):
        with pytest.raises(ValueError):
            factor_full_quantum(1)
