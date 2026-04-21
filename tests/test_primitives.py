"""Tests for primitive operation definitions."""

import pytest
import sympy as sp

from pyqres.core.operation import Primitive, Composite, OperationRegistry
from pyqres.core.metadata import RegisterMetadata
from pyqres.core.utils import mcx_t_count
from pyqres.primitives import (
    Hadamard, X, Y, CNOT, Toffoli, Rx, Ry, PhaseGate, Rz, U3,
    Add_UInt_UInt, ShiftLeft, SplitRegister, CombineRegister,
    QFT, InverseQFT, Normalize, ClearZero, QRAM,
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


class TestGates:
    def test_hadamard_is_primitive(self):
        assert issubclass(Hadamard, Primitive)

    def test_hadamard_t_count(self):
        declare_regs(q0=1)
        h = Hadamard(['q0'])
        assert h.t_count() == 0

    def test_x_is_primitive(self):
        assert issubclass(X, Primitive)

    def test_x_t_count(self):
        declare_regs(q0=1)
        x = X(['q0'])
        assert x.t_count() == 0

    def test_x_t_count_with_qubit_index(self):
        declare_regs(q0=4)
        x = X(['q0'], [2])
        assert x.t_count() == 0

    def test_cnot_is_primitive(self):
        assert issubclass(CNOT, Primitive)

    def test_cnot_t_count(self):
        declare_regs(q0=1, q1=1)
        cnot = CNOT(['q0', 'q1'])
        assert cnot.t_count() == 0  # CNOT is a basic gate, no T gates needed

    def test_toffoli_is_primitive(self):
        assert issubclass(Toffoli, Primitive)

    def test_toffoli_t_count(self):
        declare_regs(q0=1, q1=1, q2=1)
        toffoli = Toffoli(['q0', 'q1', 'q2'])
        assert toffoli.t_count() == 7

    def test_rx_t_count(self):
        declare_regs(q0=1)
        rx = Rx(['q0'], [0.5, 0.01])
        result = rx.t_count()
        assert result > 0

    def test_ry_t_count(self):
        declare_regs(q0=1)
        ry = Ry(['q0'], [0.5, 0.01])
        result = ry.t_count()
        assert result > 0

    def test_phase_gate_t_count(self):
        declare_regs(q0=1)
        pg = PhaseGate(['q0'], [0.5, 0.01])
        result = pg.t_count()
        assert result > 0

    def test_rz_t_count(self):
        declare_regs(q0=1)
        rz = Rz(['q0'], [0.5, 0.01])
        result = rz.t_count()
        assert result > 0


class TestArithmetic:
    def test_add_uint_uint_t_count(self):
        declare_regs(a=4, b=4, c=4)
        add = Add_UInt_UInt(['a', 'b', 'c'])
        # (n-1) * mcx_t_count(2) = 3 * 7 = 21
        assert add.t_count() == 21

    def test_shift_left_t_count(self):
        declare_regs(r=4)
        sl = ShiftLeft(['r'], [2])
        # Shift is classical, 0 T gates
        assert sl.t_count() == 0


class TestRegisterOps:
    def test_split_register_t_count(self):
        declare_regs(main=4, sub1=2, sub2=2)
        sr = SplitRegister(['main', 'sub1', 'sub2'], [2, 2])
        assert sr.t_count() == 0

    def test_combine_register_t_count(self):
        declare_regs(first=2, second=2)
        cr = CombineRegister(['first', 'second'])
        assert cr.t_count() == 0


class TestTransform:
    def test_qft_t_count(self):
        declare_regs(r=4)
        qft = QFT(['r'])
        # n(n-1)/2 * mcx_t_count(2) = 6 * 7 = 42
        assert qft.t_count() == 42


class TestStatePrep:
    def test_normalize_t_count(self):
        n = Normalize([])
        assert n.t_count() == 0

    def test_clear_zero_t_count(self):
        cz = ClearZero([], [0.01])
        assert cz.t_count() == 0


class TestUtils:
    def test_mcx_t_count(self):
        assert mcx_t_count(0) == 0
        assert mcx_t_count(1) == 0
        assert mcx_t_count(2) == 7
        assert mcx_t_count(3) == 16 * 7 * 3


class TestRegistry:
    def test_primitives_registered(self):
        assert OperationRegistry.has_class("Hadamard")
        assert OperationRegistry.has_class("X")
        assert OperationRegistry.has_class("CNOT")
        assert OperationRegistry.has_class("Toffoli")

    def test_get_class(self):
        cls = OperationRegistry.get_class("Hadamard")
        assert cls is Hadamard
