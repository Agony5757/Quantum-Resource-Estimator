"""Tests for Quantikz LaTeX circuit generation."""

import pytest

from pyqres.core.operation import Primitive, Composite, StandardComposite
from pyqres.core.metadata import RegisterMetadata
from pyqres.quantikz import QuantikzVisitor, LatexGenerator
from pyqres.primitives import (
    Hadamard, X, CNOT, Toffoli,
    Swap_General_General, SplitRegister,
)
from pyqres.generated import Swap


def declare_regs(**regs):
    for name, size in regs.items():
        RegisterMetadata.get_register_metadata().declare_register(name, size)


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


class TestSingleGateLatex:
    def test_hadamard_latex(self):
        declare_regs(q=2)
        vis = QuantikzVisitor()
        Hadamard(['q']).traverse(vis)
        latex = vis.to_latex()
        assert r'\mathrm{Hadamard}' in latex
        assert 'quantikz' in latex

    def test_x_gate_latex(self):
        declare_regs(q=1)
        vis = QuantikzVisitor()
        X(['q'], [0]).traverse(vis)
        latex = vis.to_latex()
        assert r'\mathrm{X}' in latex

    def test_cnot_latex(self):
        declare_regs(ctrl=1, tgt=1)
        vis = QuantikzVisitor()
        CNOT(['ctrl', 'tgt'], [0, 0]).traverse(vis)
        latex = vis.to_latex()
        assert r'\mathrm{CNOT}' in latex

    def test_toffoli_latex(self):
        declare_regs(c1=1, c2=1, tgt=1)
        vis = QuantikzVisitor()
        Toffoli(['c1', 'c2', 'tgt'], [0, 0, 0]).traverse(vis)
        latex = vis.to_latex()
        assert r'\mathrm{Toffoli}' in latex


class TestCompositeLatex:
    def test_swap_composite_latex(self):
        declare_regs(a=2, b=2)
        vis = QuantikzVisitor()
        Swap(['a', 'b']).traverse(vis)
        latex = vis.to_latex()
        assert 'quantikz' in latex

    def test_multiple_gates(self):
        declare_regs(q=2)
        vis = QuantikzVisitor()
        Hadamard(['q']).traverse(vis)
        X(['q'], [0]).traverse(vis)
        latex = vis.to_latex()
        assert r'\mathrm{Hadamard}' in latex
        assert r'\mathrm{X}' in latex


class TestDaggerLatex:
    def test_dagger_marker(self):
        declare_regs(q=1)
        vis = QuantikzVisitor()
        x = X(['q'], [0])
        x.dagger()
        x.traverse(vis)
        latex = vis.to_latex()
        assert r'\dagger' in latex


class TestSplitRegister:
    def test_split_in_circuit(self):
        declare_regs(parent=4, child1=2, child2=2)
        vis = QuantikzVisitor()
        Hadamard(['parent']).traverse(vis)
        SplitRegister(['parent', 'child1', 'child2'], [2, 2]).traverse(vis)
        latex = vis.to_latex()
        assert 'quantikz' in latex


class TestControlTypes:
    def test_control_by_all_ones(self):
        declare_regs(ctrl=2, tgt=1)
        vis = QuantikzVisitor()
        x = X(['tgt'], [0])
        x.control(['ctrl'])
        x.traverse(vis)
        latex = vis.to_latex()
        assert r'\ctrl{' in latex

    def test_control_by_bit(self):
        declare_regs(ctrl=2, tgt=1)
        vis = QuantikzVisitor()
        x = X(['tgt'], [0])
        x.control_by_bit([('ctrl', 0)])
        x.traverse(vis)
        latex = vis.to_latex()
        assert r'\ctrl[open]{' in latex


class TestLatexOutput:
    def test_complete_document(self):
        declare_regs(q=2)
        vis = QuantikzVisitor()
        Hadamard(['q']).traverse(vis)
        latex = vis.to_latex()
        assert latex.startswith(r'\documentclass{standalone}')
        assert r'\begin{quantikz}' in latex
        assert r'\end{quantikz}' in latex
        assert r'\end{document}' in latex

    def test_figure_output(self):
        declare_regs(q=1)
        vis = QuantikzVisitor()
        X(['q'], [0]).traverse(vis)
        latex = vis.to_latex_figure("Test circuit")
        assert r'\begin{figure}' in latex
        assert r'\caption{Test circuit}' in latex
