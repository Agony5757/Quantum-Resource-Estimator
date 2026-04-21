"""Tests for the visitor pattern and traversal."""

import pytest

from pyqres.core.operation import Primitive, Composite, StandardComposite
from pyqres.core.metadata import RegisterMetadata
from pyqres.core.visitor import TCounter, TDepthCounter, TreeRenderer
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


class TestTCounter:
    def test_hadamard_t_count(self):
        declare_regs(q0=1)
        h = Hadamard(['q0'])
        counter = TCounter()
        h.traverse(counter)
        assert counter.get_count() == 0

    def test_cnot_t_count(self):
        declare_regs(q0=1, q1=1)
        cnot = CNOT(['q0', 'q1'])
        counter = TCounter()
        cnot.traverse(counter)
        assert counter.get_count() == 0  # CNOT is basic, no T gates

    def test_composite_sum(self):
        declare_regs(q0=1, q1=1, q2=1)

        class DoubleToffoli(StandardComposite):
            __abstract__ = False

            def __init__(self, reg_list):
                super().__init__(reg_list=reg_list)
                self.program_list = [
                    Toffoli(reg_list=reg_list),
                    Toffoli(reg_list=reg_list),
                ]
                self.declare_program_list()

        dc = DoubleToffoli(['q0', 'q1', 'q2'])
        counter = TCounter()
        dc.traverse(counter)
        assert counter.get_count() == 14  # 2 * 7

    def test_dagger_reverses_order(self):
        """Dagger should reverse program_list traversal."""
        declare_regs(q0=1, q1=1, q2=1)
        toffoli = Toffoli(['q0', 'q1', 'q2']).dagger()
        counter = TCounter()
        toffoli.traverse(counter)
        # T-count should be same for Toffoli and Toffoli.dagger()
        assert counter.get_count() == 7


class TestTreeRenderer:
    def test_hadamard_render(self):
        declare_regs(q0=1)
        h = Hadamard(['q0'])
        renderer = TreeRenderer()
        h.traverse(renderer)
        assert "Hadamard" in renderer.text

    def test_composite_render(self):
        declare_regs(q0=1, q1=1)

        class DoubleCNOT(StandardComposite):
            __abstract__ = False

            def __init__(self, reg_list):
                super().__init__(reg_list=reg_list)
                self.program_list = [
                    CNOT(reg_list=reg_list),
                    CNOT(reg_list=reg_list),
                ]
                self.declare_program_list()

        dc = DoubleCNOT(['q0', 'q1'])
        renderer = TreeRenderer()
        dc.traverse(renderer)
        assert "DoubleCNOT" in renderer.text
        assert "CNOT" in renderer.text


class TestControllerPropagation:
    def test_control_by_all_ones(self):
        declare_regs(q0=1, q1=1, ctrl=1)
        cnot = CNOT(['q0', 'q1']).control_by_all_ones(['ctrl'])
        assert 'conditioned_by_all_ones' in cnot.controllers
        assert 'ctrl' in cnot.controllers['conditioned_by_all_ones']

    def test_dagger_chain(self):
        declare_regs(q0=1)
        h = Hadamard(['q0']).dagger()
        assert h.dagger_flag is True
        h2 = h.dagger()
        assert h2.dagger_flag is False
