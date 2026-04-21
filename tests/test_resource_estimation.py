"""Tests for resource estimation: T-count, T-depth, Toffoli-count."""

import pytest

from pyqres.core.metadata import RegisterMetadata
from pyqres.core.lowering import (
    LoweringEngine, TCountEstimator, TDepthEstimator, ToffoliCountEstimator
)
from pyqres.core.operation import Composite
from pyqres.primitives import (
    Hadamard, X, Y, CNOT, Toffoli, Rx, Ry, PhaseGate, Rz, U3,
    Add_UInt_UInt, Add_UInt_UInt_InPlace, Add_UInt_ConstUInt, Add_ConstUInt,
    Mult_UInt_ConstUInt, ShiftLeft, ShiftRight,
    Compare_UInt_UInt, Less_UInt_UInt, GetMid_UInt_UInt, Assign, Swap_General_General,
    Push, Pop,
    QFT, InverseQFT, Reflection_Bool,
)


@pytest.fixture(autouse=True)
def clean_metadata():
    """Clean register metadata between tests."""
    while len(RegisterMetadata.register_metadata_stack) > 1:
        RegisterMetadata.pop_register_metadata()
    RegisterMetadata.register_metadata_stack.clear()
    RegisterMetadata.push_register_metadata()
    yield
    while len(RegisterMetadata.register_metadata_stack) > 0:
        RegisterMetadata.pop_register_metadata()
    RegisterMetadata.push_register_metadata()


def declare_regs(**regs):
    for name, size in regs.items():
        RegisterMetadata.get_register_metadata().declare_register(name, size)


class TestTCountEstimation:
    """Test T-count estimation for various primitives."""

    def test_hadamard_t_count(self):
        declare_regs(q=1)
        h = Hadamard(['q'])
        engine = LoweringEngine()
        assert engine.estimate(h, TCountEstimator()) == 0

    def test_x_t_count(self):
        declare_regs(q=1)
        x = X(['q'])
        engine = LoweringEngine()
        assert engine.estimate(x, TCountEstimator()) == 0

    def test_y_t_count(self):
        declare_regs(q=1)
        y = Y(['q'], [0])
        engine = LoweringEngine()
        assert engine.estimate(y, TCountEstimator()) == 0

    def test_toffoli_t_count(self):
        declare_regs(q0=1, q1=1, q2=1)
        toffoli = Toffoli(['q0', 'q1', 'q2'])
        engine = LoweringEngine()
        assert engine.estimate(toffoli, TCountEstimator()) == 7

    def test_rx_t_count(self):
        declare_regs(q=1)
        rx = Rx(['q'], [0.5, 0.01])
        engine = LoweringEngine()
        result = engine.estimate(rx, TCountEstimator())
        assert result > 0  # 3 * ceil(log(1/eps))

    def test_ry_t_count(self):
        declare_regs(q=1)
        ry = Ry(['q'], [0.5, 0.01])
        engine = LoweringEngine()
        result = engine.estimate(ry, TCountEstimator())
        assert result > 0

    def test_add_uint_uint_t_count(self):
        declare_regs(a=4, b=4, c=4)
        add = Add_UInt_UInt(['a', 'b', 'c'])
        engine = LoweringEngine()
        # (n-1) * 7 = 3 * 7 = 21
        assert engine.estimate(add, TCountEstimator()) == 21

    def test_add_uint_uint_inplace_t_count(self):
        declare_regs(a=4, b=4)
        add = Add_UInt_UInt_InPlace(['a', 'b'])
        engine = LoweringEngine()
        # 2 * (n-1) * 7 = 2 * 3 * 7 = 42
        assert engine.estimate(add, TCountEstimator()) == 42

    def test_mult_uint_constuint_t_count(self):
        declare_regs(a=4, b=4)
        mult = Mult_UInt_ConstUInt(['a', 'b'], [5])
        engine = LoweringEngine()
        # (n-1)^2 * 7 = 9 * 7 = 63
        assert engine.estimate(mult, TCountEstimator()) == 63

    def test_shift_t_count(self):
        declare_regs(r=4)
        sl = ShiftLeft(['r'], [2])
        sr = ShiftRight(['r'], [2])
        engine = LoweringEngine()
        assert engine.estimate(sl, TCountEstimator()) == 0
        assert engine.estimate(sr, TCountEstimator()) == 0

    def test_compare_t_count(self):
        declare_regs(a=4, b=4, less=1, eq=1)
        cmp = Compare_UInt_UInt(['a', 'b', 'less', 'eq'])
        engine = LoweringEngine()
        # (n-1) * 7 = 21
        assert engine.estimate(cmp, TCountEstimator()) == 21

    def test_assign_t_count(self):
        declare_regs(src=4, dst=4)
        assign = Assign(['src', 'dst'])
        engine = LoweringEngine()
        assert engine.estimate(assign, TCountEstimator()) == 0

    def test_qft_t_count(self):
        declare_regs(q=4)
        qft = QFT(['q'])
        engine = LoweringEngine()
        # n(n-1)/2 * 7 = 6 * 7 = 42
        assert engine.estimate(qft, TCountEstimator()) == 42

    def test_push_pop_t_count(self):
        declare_regs(r=4)
        push = Push(['r'], [False])
        pop = Pop(['r'])
        engine = LoweringEngine()
        assert engine.estimate(push, TCountEstimator()) == 0
        assert engine.estimate(pop, TCountEstimator()) == 0


class TestTDepthEstimation:
    """Test T-depth estimation."""

    def test_single_toffoli_t_depth(self):
        declare_regs(q0=1, q1=1, q2=1)
        toffoli = Toffoli(['q0', 'q1', 'q2'])
        engine = LoweringEngine()
        assert engine.estimate(toffoli, TDepthEstimator()) == 7

    def test_sequential_toffoli_t_depth(self):
        declare_regs(q0=1, q1=1, q2=1)

        class TwoToffoli(Composite):
            def __init__(self):
                super().__init__(['q0', 'q1', 'q2'])
                self.program_list = [
                    Toffoli(['q0', 'q1', 'q2']),
                    Toffoli(['q0', 'q1', 'q2']),
                ]
                self.declare_program_list()

        two_toff = TwoToffoli()
        engine = LoweringEngine()
        # Sequential execution: depth = 7 + 7 = 14
        assert engine.estimate(two_toff, TDepthEstimator()) == 14


class TestToffoliCountEstimation:
    """Test Toffoli-count estimation."""

    def test_single_toffoli(self):
        declare_regs(q0=1, q1=1, q2=1)
        toffoli = Toffoli(['q0', 'q1', 'q2'])
        engine = LoweringEngine()
        assert engine.estimate(toffoli, ToffoliCountEstimator()) == 1

    def test_hadamard_zero_toffoli(self):
        declare_regs(q=1)
        h = Hadamard(['q'])
        engine = LoweringEngine()
        assert engine.estimate(h, ToffoliCountEstimator()) == 0

    def test_composite_toffoli_count(self):
        declare_regs(q0=1, q1=1, q2=1)

        class ThreeToffoli(Composite):
            def __init__(self):
                super().__init__(['q0', 'q1', 'q2'])
                self.program_list = [
                    Toffoli(['q0', 'q1', 'q2']),
                    Toffoli(['q0', 'q1', 'q2']),
                    Toffoli(['q0', 'q1', 'q2']),
                ]
                self.declare_program_list()

        three_toff = ThreeToffoli()
        engine = LoweringEngine()
        assert engine.estimate(three_toff, ToffoliCountEstimator()) == 3


class TestControlledOperations:
    """Test resource estimation for controlled operations."""

    def test_controlled_x_t_count(self):
        declare_regs(ctrl=1, target=1)
        x = X(['target']).control(['ctrl'])
        engine = LoweringEngine()
        # MCX with 1 control = 0 T gates
        assert engine.estimate(x, TCountEstimator()) == 0

    def test_controlled_toffoli_t_count(self):
        declare_regs(c=1, q0=1, q1=1, q2=1)
        toffoli = Toffoli(['q0', 'q1', 'q2']).control(['c'])
        engine = LoweringEngine()
        # MCX with 3 controls = 16 * 7 * 3 = 336 T gates
        assert engine.estimate(toffoli, TCountEstimator()) == 336
