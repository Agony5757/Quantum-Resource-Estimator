"""Tests for the lowering engine and resource estimation."""

import pytest

from pyqres.core.operation import Primitive, StandardComposite, AbstractComposite
from pyqres.core.metadata import RegisterMetadata
from pyqres.core.lowering import LoweringEngine, TCountEstimator
from pyqres.core.visitor import TCounter
from pyqres.primitives import Hadamard, X, CNOT, Toffoli


@pytest.fixture(autouse=True)
def clean_metadata():
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


class TestLoweringEngine:
    def test_primitive_t_count(self):
        declare_regs(q0=1, q1=1, q2=1)
        toffoli = Toffoli(['q0', 'q1', 'q2'])
        engine = LoweringEngine()
        result = engine.estimate(toffoli, TCountEstimator())
        assert result == 7

    def test_composite_t_count(self):
        declare_regs(q0=1, q1=1, q2=1)

        class TripleToffoli(StandardComposite):
            __abstract__ = False

            def __init__(self, reg_list):
                super().__init__(reg_list=reg_list)
                self.program_list = [
                    Toffoli(reg_list=reg_list),
                    Toffoli(reg_list=reg_list),
                    Toffoli(reg_list=reg_list),
                ]
                self.declare_program_list()

        tc = TripleToffoli(['q0', 'q1', 'q2'])
        engine = LoweringEngine()
        result = engine.estimate(tc, TCountEstimator())
        assert result == 21  # 3 * 7

    def test_nested_composite(self):
        declare_regs(q0=1, q1=1, q2=1)

        class InnerComposite(StandardComposite):
            __abstract__ = False

            def __init__(self, reg_list):
                super().__init__(reg_list=reg_list)
                self.program_list = [
                    Toffoli(reg_list=[reg_list[0], reg_list[1], reg_list[2]]),
                ]
                self.declare_program_list()

        class OuterComposite(StandardComposite):
            __abstract__ = False

            def __init__(self, reg_list):
                super().__init__(reg_list=reg_list)
                self.program_list = [
                    InnerComposite(reg_list=reg_list),
                    Toffoli(reg_list=reg_list),
                ]
                self.declare_program_list()

        oc = OuterComposite(['q0', 'q1', 'q2'])
        engine = LoweringEngine()
        result = engine.estimate(oc, TCountEstimator())
        assert result == 14  # 2 * Toffoli


class TestResourceEstimator:
    def test_tcount_estimator_name(self):
        est = TCountEstimator()
        assert est.name == "T-count"

    def test_tcount_estimator_creates_visitor(self):
        est = TCountEstimator()
        visitor = est.create_visitor()
        assert isinstance(visitor, TCounter)


class TestAbstractComposite:
    def test_custom_sum_t_count(self):
        declare_regs(q0=1)

        class Doubler(AbstractComposite):
            __abstract__ = False

            def __init__(self, reg_list):
                super().__init__(reg_list=reg_list)
                self.program_list = [Hadamard(reg_list=reg_list)]
                self.declare_program_list()

            def sum_t_count(self, t_count_list):
                return 2 * sum(t_count_list)

        d = Doubler(['q0'])
        engine = LoweringEngine()
        result = engine.estimate(d, TCountEstimator())
        assert result == 0  # 2 * 0
