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


class TestNewGates:
    """Tests for Phase 2 gate primitives."""

    def test_hadamard_bool_is_primitive(self):
        from pyqres.primitives import Hadamard_Bool
        assert issubclass(Hadamard_Bool, Primitive)

    def test_hadamard_bool_t_count(self):
        from pyqres.primitives import Hadamard_Bool
        declare_regs(b0=1)
        h = Hadamard_Bool(['b0'])
        assert h.t_count() == 0
        assert getattr(h, '__self_conjugate__', False)

    def test_sgate_t_count(self):
        from pyqres.primitives import Sgate
        declare_regs(b0=1)
        s = Sgate(['b0'], [0])
        assert s.t_count() == 0

    def test_tgate_t_count(self):
        from pyqres.primitives import Tgate
        declare_regs(b0=1)
        t = Tgate(['b0'], [0])
        # T gate uses rotation decomposition
        assert t.t_count() > 0

    def test_sxgate_t_count(self):
        from pyqres.primitives import SXgate
        declare_regs(b0=1)
        sx = SXgate(['b0'], [0])
        assert sx.t_count() > 0

    def test_u2gate_t_count(self):
        from pyqres.primitives import U2gate
        declare_regs(b0=1)
        u2 = U2gate(['b0'], [0, 0.5, 1.0])
        assert u2.t_count() > 0

    def test_swap_bool_bool_t_count(self):
        from pyqres.primitives import Swap_Bool_Bool
        declare_regs(b0=1, b1=1)
        sw = Swap_Bool_Bool(['b0', 'b1'], [0, 1])
        assert sw.t_count() == 0
        assert getattr(sw, '__self_conjugate__', False)

    def test_global_phase_t_count(self):
        from pyqres.primitives import GlobalPhase
        gp = GlobalPhase([], [0.5])
        assert gp.t_count() == 0


class TestNewArithmetic:
    """Tests for Phase 2 arithmetic primitives."""

    def test_add_mult_uint_constuint_t_count(self):
        from pyqres.primitives import Add_Mult_UInt_ConstUInt
        declare_regs(input_reg=4, output_reg=4)
        op = Add_Mult_UInt_ConstUInt(['input_reg', 'output_reg'], [3, 0])
        assert op.t_count() >= 0

    def test_get_data_addr_t_count(self):
        from pyqres.primitives import GetDataAddr
        declare_regs(offset=4, row=4, col=4, data_offset=4)
        op = GetDataAddr(['offset', 'row', 'col', 'data_offset'], [8])
        # Self-adjoint (XOR-based)
        assert getattr(op, '__self_conjugate__', False)
        assert op.t_count() >= 0

    def test_get_row_addr_t_count(self):
        from pyqres.primitives import GetRowAddr
        declare_regs(offset=4, row=4, row_offset=4)
        op = GetRowAddr(['offset', 'row', 'row_offset'], [8])
        assert getattr(op, '__self_conjugate__', False)
        assert op.t_count() >= 0


class TestNewRegisterOps:
    """Tests for Phase 2 register management primitives."""

    def test_add_register_t_count(self):
        from pyqres.primitives import AddRegister
        ar = AddRegister([], ['new_reg', 'UnsignedInteger', 4])
        assert ar.t_count() == 0

    def test_remove_register_t_count(self):
        from pyqres.primitives import RemoveRegister
        rr = RemoveRegister([], ['old_reg'])
        assert rr.t_count() == 0


class TestMeasurement:
    """Tests for measurement primitives."""

    def test_partial_trace_t_count(self):
        from pyqres.primitives import PartialTrace
        pt = PartialTrace(['reg1', 'reg2'])
        assert pt.t_count() == 0
        assert getattr(pt, '__self_conjugate__', False)

    def test_prob_t_count(self):
        from pyqres.primitives import Prob
        p = Prob(['reg1'])
        assert p.t_count() == 0
        assert getattr(p, '__self_conjugate__', False)

    def test_state_print_t_count(self):
        from pyqres.primitives import StatePrint
        sp = StatePrint(['reg1'], [0])
        assert sp.t_count() == 0
        assert getattr(sp, '__self_conjugate__', False)


class TestNewCondRot:
    """Tests for Phase 2 conditional rotation primitives."""

    def test_condrot_rational_bool_t_count(self):
        from pyqres.primitives import CondRot_Rational_Bool
        declare_regs(reg_in=4, reg_out=1)
        op = CondRot_Rational_Bool(['reg_in', 'reg_out'])
        assert getattr(op, '__self_conjugate__', False)
        result = op.t_count()
        assert result >= 0


class TestViewNormalization:
    """Tests for ViewNormalization."""

    def test_view_normalization_t_count(self):
        from pyqres.primitives import ViewNormalization
        vn = ViewNormalization([])
        assert vn.t_count() == 0
        assert getattr(vn, '__self_conjugate__', False)


class TestRegistry:
    def test_primitives_registered(self):
        assert OperationRegistry.has_class("Hadamard")
        assert OperationRegistry.has_class("X")
        assert OperationRegistry.has_class("CNOT")
        assert OperationRegistry.has_class("Toffoli")
        # New primitives should be registered
        assert OperationRegistry.has_class("Hadamard_Bool")
        assert OperationRegistry.has_class("CondRot_Rational_Bool")
        assert OperationRegistry.has_class("GetDataAddr")
        assert OperationRegistry.has_class("PartialTrace")

    def test_get_class(self):
        cls = OperationRegistry.get_class("Hadamard")
        assert cls is Hadamard
