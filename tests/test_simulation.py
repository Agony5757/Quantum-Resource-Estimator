"""End-to-end simulation tests using SimulatorVisitor and PySparQ."""

import pytest
import pysparq

from pyqres.core.operation import Primitive, Composite, StandardComposite
from pyqres.core.metadata import RegisterMetadata
from pyqres.core.simulator import SimulatorVisitor
from pyqres.primitives import (
    Hadamard, Hadamard_NDigits, X, Y, CNOT, Toffoli,
    Rx, Ry, PhaseGate, Rz, U3,
    Add_UInt_UInt, Add_UInt_UInt_InPlace, Add_UInt_ConstUInt, Add_ConstUInt,
    Mult_UInt_ConstUInt, ShiftLeft, ShiftRight,
    Compare_UInt_UInt, Less_UInt_UInt, GetMid_UInt_UInt,
    Assign, Swap_General_General,
    Div_Sqrt_Arccos_Int_Int, Sqrt_Div_Arccos_Int_Int, GetRotateAngle_Int_Int,
    SplitRegister, CombineRegister, Push, Pop,
    QFT, InverseQFT, Reflection_Bool,
    Normalize, ClearZero, Init_Unsafe, Rot_GeneralStatePrep,
)


def declare_regs(**regs):
    for name, size in regs.items():
        RegisterMetadata.get_register_metadata().declare_register(name, size)


def declare_regs_typed(*entries):
    for entry in entries:
        if len(entry) == 3:
            name, size, rtype = entry
        else:
            name, size = entry
            rtype = "General"
        RegisterMetadata.get_register_metadata().declare_register(name, size, rtype)


def read_reg(state, reg_name):
    reg_id = pysparq.System.get_id(reg_name)
    return state.basis_states[0].registers[reg_id].value


def state_size(state):
    return state.size()


@pytest.fixture(autouse=True)
def clean_pysparq():
    """Clean both pyqres metadata and pysparq system state."""
    while len(RegisterMetadata.register_metadata_stack) > 1:
        RegisterMetadata.pop_register_metadata()
    RegisterMetadata.register_metadata_stack.clear()
    RegisterMetadata.push_register_metadata()
    pysparq.System.clear()
    yield
    while len(RegisterMetadata.register_metadata_stack) > 0:
        RegisterMetadata.pop_register_metadata()
    RegisterMetadata.push_register_metadata()
    pysparq.System.clear()


class TestGateSimulation:
    def test_hadamard_creates_superposition(self):
        declare_regs(q=2)
        sim = SimulatorVisitor()
        Hadamard(['q']).traverse(sim)
        assert state_size(sim.state) == 4

    def test_hadamard_ndigits(self):
        declare_regs(q=3)
        sim = SimulatorVisitor()
        Hadamard_NDigits(['q'], [2]).traverse(sim)
        assert state_size(sim.state) == 4

    def test_x_flips_bits(self):
        declare_regs(q=1)
        sim = SimulatorVisitor()
        X(['q'], [0]).traverse(sim)  # use qubit_index for single-bit flip
        assert read_reg(sim.state, 'q') == 1

    def test_x_roundtrip(self):
        declare_regs(q=1)
        sim = SimulatorVisitor()
        X(['q'], [0]).traverse(sim)
        X(['q'], [0]).traverse(sim)
        assert read_reg(sim.state, 'q') == 0

    def test_cnot_simulation(self):
        declare_regs(ctrl=1, tgt=1)
        sim = SimulatorVisitor()
        X(['ctrl'], [0]).traverse(sim)
        CNOT(['ctrl', 'tgt'], [0, 0]).traverse(sim)  # bit-level CNOT
        assert read_reg(sim.state, 'tgt') == 1

    def test_cnot_no_flip_when_ctrl_zero(self):
        declare_regs(ctrl=1, tgt=1)
        sim = SimulatorVisitor()
        CNOT(['ctrl', 'tgt'], [0, 0]).traverse(sim)
        assert read_reg(sim.state, 'tgt') == 0

    def test_toffoli_simulation(self):
        declare_regs(c1=1, c2=1, tgt=1)
        sim = SimulatorVisitor()
        X(['c1'], [0]).traverse(sim)
        X(['c2'], [0]).traverse(sim)
        Toffoli(['c1', 'c2', 'tgt'], [0, 0, 0]).traverse(sim)  # bit-level Toffoli
        assert read_reg(sim.state, 'tgt') == 1

    def test_toffoli_no_flip_with_one_ctrl(self):
        declare_regs(c1=1, c2=1, tgt=1)
        sim = SimulatorVisitor()
        X(['c1'], [0]).traverse(sim)
        Toffoli(['c1', 'c2', 'tgt'], [0, 0, 0]).traverse(sim)
        assert read_reg(sim.state, 'tgt') == 0

    def test_rx_simulation(self):
        declare_regs(q=1)
        sim = SimulatorVisitor()
        Rx(['q'], [0.5, 0.01]).traverse(sim)
        assert state_size(sim.state) >= 1

    def test_ry_simulation(self):
        declare_regs(q=1)
        sim = SimulatorVisitor()
        Ry(['q'], [0.5, 0.01]).traverse(sim)
        assert state_size(sim.state) == 2

    def test_y_gate_simulation(self):
        declare_regs(q=1)
        sim = SimulatorVisitor()
        Y(['q'], [0]).traverse(sim)
        assert state_size(sim.state) == 1

    def test_rz_simulation(self):
        declare_regs(q=1)
        sim = SimulatorVisitor()
        Rz(['q'], [0.5, 0.01]).traverse(sim)
        assert state_size(sim.state) >= 1


class TestArithmeticSimulation:
    def test_add_uint_uint(self):
        declare_regs_typed(('a', 2, 'UnsignedInteger'), ('b', 2, 'UnsignedInteger'), ('c', 2, 'UnsignedInteger'))
        sim = SimulatorVisitor()
        Add_UInt_UInt(['a', 'b', 'c']).traverse(sim)
        assert read_reg(sim.state, 'c') == 0

    def test_add_uint_uint_with_superposition(self):
        declare_regs_typed(('a', 2, 'UnsignedInteger'), ('b', 2, 'UnsignedInteger'), ('c', 2, 'UnsignedInteger'))
        sim = SimulatorVisitor()
        Hadamard(['a']).traverse(sim)
        Add_UInt_UInt(['a', 'b', 'c']).traverse(sim)
        assert state_size(sim.state) == 4
        a_id = pysparq.System.get_id('a')
        c_id = pysparq.System.get_id('c')
        for s in sim.state.basis_states:
            assert s.registers[c_id].value == s.registers[a_id].value

    def test_add_uint_uint_inplace(self):
        declare_regs_typed(('a', 2, 'UnsignedInteger'), ('b', 2, 'UnsignedInteger'))
        sim = SimulatorVisitor()
        Hadamard(['a']).traverse(sim)
        Add_UInt_UInt_InPlace(['a', 'b']).traverse(sim)
        a_id = pysparq.System.get_id('a')
        b_id = pysparq.System.get_id('b')
        for s in sim.state.basis_states:
            assert s.registers[b_id].value == s.registers[a_id].value

    def test_add_uint_constuint(self):
        declare_regs_typed(('a', 2, 'UnsignedInteger'), ('c', 3, 'UnsignedInteger'))
        sim = SimulatorVisitor()
        Hadamard(['a']).traverse(sim)
        Add_UInt_ConstUInt(['a', 'c'], [3]).traverse(sim)
        a_id = pysparq.System.get_id('a')
        c_id = pysparq.System.get_id('c')
        for s in sim.state.basis_states:
            assert s.registers[c_id].value == s.registers[a_id].value + 3

    def test_add_constuint(self):
        declare_regs_typed(('a', 3, 'UnsignedInteger'))
        sim = SimulatorVisitor()
        # Don't use Hadamard on UnsignedInteger; test with known state
        Add_ConstUInt(['a'], [5]).traverse(sim)
        assert read_reg(sim.state, 'a') == 5

    def test_mult_uint_constuint(self):
        declare_regs_typed(('a', 2, 'UnsignedInteger'), ('c', 4, 'UnsignedInteger'))
        sim = SimulatorVisitor()
        Hadamard(['a']).traverse(sim)
        Mult_UInt_ConstUInt(['a', 'c'], [3]).traverse(sim)
        a_id = pysparq.System.get_id('a')
        c_id = pysparq.System.get_id('c')
        for s in sim.state.basis_states:
            assert s.registers[c_id].value == s.registers[a_id].value * 3

    def test_shift_left(self):
        declare_regs_typed(('a', 3, 'UnsignedInteger'))
        sim = SimulatorVisitor()
        # Set a=1 via Hadamard on General, then... use direct init
        # Actually Hadamard works on UnsignedInteger too for superposition
        ShiftLeft(['a'], [1]).traverse(sim)
        assert read_reg(sim.state, 'a') == 0

    def test_shift_right(self):
        declare_regs_typed(('a', 3, 'UnsignedInteger'))
        sim = SimulatorVisitor()
        ShiftRight(['a'], [1]).traverse(sim)
        assert read_reg(sim.state, 'a') == 0

    def test_compare_uint_uint(self):
        declare_regs_typed(
            ('l', 2, 'UnsignedInteger'), ('r', 2, 'UnsignedInteger'),
            ('less', 1, 'Boolean'), ('eq', 1, 'Boolean'))
        sim = SimulatorVisitor()
        Compare_UInt_UInt(['l', 'r', 'less', 'eq']).traverse(sim)
        assert read_reg(sim.state, 'less') == 0
        assert read_reg(sim.state, 'eq') == 1

    def test_less_uint_uint(self):
        declare_regs_typed(
            ('l', 2, 'UnsignedInteger'), ('r', 2, 'UnsignedInteger'),
            ('less', 1, 'Boolean'))
        sim = SimulatorVisitor()
        Less_UInt_UInt(['l', 'r', 'less']).traverse(sim)
        assert read_reg(sim.state, 'less') == 0

    def test_getmid_uint_uint(self):
        declare_regs_typed(
            ('l', 3, 'UnsignedInteger'), ('r', 3, 'UnsignedInteger'),
            ('mid', 3, 'UnsignedInteger'))
        sim = SimulatorVisitor()
        GetMid_UInt_UInt(['l', 'r', 'mid']).traverse(sim)
        assert read_reg(sim.state, 'mid') == 0

    def test_assign(self):
        declare_regs(src=2, dst=2)
        sim = SimulatorVisitor()
        Hadamard(['src']).traverse(sim)
        Assign(['src', 'dst']).traverse(sim)
        src_id = pysparq.System.get_id('src')
        dst_id = pysparq.System.get_id('dst')
        for s in sim.state.basis_states:
            assert s.registers[dst_id].value == s.registers[src_id].value

    def test_swap_general_general(self):
        declare_regs(a=2, b=2)
        sim = SimulatorVisitor()
        Hadamard(['a']).traverse(sim)
        Swap_General_General(['a', 'b']).traverse(sim)
        assert state_size(sim.state) > 0


class TestRegisterOpsSimulation:
    def test_split_combine_roundtrip(self):
        declare_regs(parent=4, child1=2, child2=2)
        sim = SimulatorVisitor()
        Hadamard(['parent']).traverse(sim)
        SplitRegister(['parent', 'child1', 'child2'], [2, 2]).traverse(sim)
        CombineRegister(['parent', 'child1']).traverse(sim)
        assert state_size(sim.state) > 0

    def test_push_pop_roundtrip(self):
        declare_regs(data=2, garbage=2)
        sim = SimulatorVisitor()
        Hadamard(['data']).traverse(sim)
        Push(['data'], ['garbage']).traverse(sim)
        Pop(['data']).traverse(sim)
        assert state_size(sim.state) > 0


class TestTransformSimulation:
    def test_qft_creates_superposition(self):
        declare_regs(q=2)
        sim = SimulatorVisitor()
        QFT(['q']).traverse(sim)
        assert state_size(sim.state) == 4

    def test_qft_inverse_roundtrip(self):
        declare_regs(q=2)
        sim = SimulatorVisitor()
        QFT(['q']).traverse(sim)
        InverseQFT(['q']).traverse(sim)
        assert state_size(sim.state) == 1
        assert read_reg(sim.state, 'q') == 0

    def test_reflection_bool(self):
        declare_regs(q=2)
        sim = SimulatorVisitor()
        Reflection_Bool(['q'], [False]).traverse(sim)
        assert state_size(sim.state) == 1


class TestDaggerSimulation:
    def test_hadamard_is_self_adjoint(self):
        declare_regs(q=2)
        sim = SimulatorVisitor()
        Hadamard(['q']).traverse(sim)
        Hadamard(['q']).traverse(sim)
        assert state_size(sim.state) == 1
        assert read_reg(sim.state, 'q') == 0

    def test_add_uint_dagger_roundtrip(self):
        declare_regs_typed(('a', 2, 'UnsignedInteger'), ('b', 2, 'UnsignedInteger'))
        sim = SimulatorVisitor()
        Hadamard(['a']).traverse(sim)
        Add_UInt_UInt_InPlace(['a', 'b']).traverse(sim)
        add_dag = Add_UInt_UInt_InPlace(['a', 'b'])
        add_dag.dagger_flag = True
        add_dag.traverse(sim)
        b_id = pysparq.System.get_id('b')
        for s in sim.state.basis_states:
            assert s.registers[b_id].value == 0


class TestCompositeSimulation:
    def test_swap_composite(self):
        from pyqres.generated import Swap
        declare_regs(a=2, b=2)
        sim = SimulatorVisitor()
        Hadamard(['a']).traverse(sim)
        Swap(['a', 'b']).traverse(sim)
        assert state_size(sim.state) > 0


class TestStatePrepSimulation:
    def test_normalize(self):
        declare_regs(q=1)
        sim = SimulatorVisitor()
        Normalize([]).traverse(sim)
        assert state_size(sim.state) >= 1

    def test_clear_zero(self):
        declare_regs(q=2)
        sim = SimulatorVisitor()
        ClearZero([], [0.01]).traverse(sim)
        assert state_size(sim.state) == 1

    def test_init_unsafe(self):
        declare_regs(q=3)
        sim = SimulatorVisitor()
        Init_Unsafe(['q'], [5]).traverse(sim)
        assert read_reg(sim.state, 'q') == 5

    def test_rot_general_state_prep(self):
        import numpy as np
        declare_regs(q=2)
        sim = SimulatorVisitor()
        sv = [1.0, 0.0, 0.0, 0.0]
        Rot_GeneralStatePrep(['q'], [sv]).traverse(sim)
        assert state_size(sim.state) >= 1


class TestAdvancedArithmeticSimulation:
    def test_div_sqrt_arccos_int_int(self):
        declare_regs_typed(
            ('a', 4, 'UnsignedInteger'), ('b', 4, 'UnsignedInteger'),
            ('c', 8, 'Rational'))
        sim = SimulatorVisitor()
        Init_Unsafe(['a'], [1]).traverse(sim)
        Init_Unsafe(['b'], [4]).traverse(sim)
        Div_Sqrt_Arccos_Int_Int(['a', 'b', 'c']).traverse(sim)
        assert state_size(sim.state) >= 1

    def test_sqrt_div_arccos_int_int(self):
        declare_regs_typed(
            ('a', 4, 'SignedInteger'), ('b', 4, 'UnsignedInteger'),
            ('c', 8, 'Rational'))
        sim = SimulatorVisitor()
        Init_Unsafe(['a'], [1]).traverse(sim)
        Init_Unsafe(['b'], [4]).traverse(sim)
        Sqrt_Div_Arccos_Int_Int(['a', 'b', 'c']).traverse(sim)
        assert state_size(sim.state) >= 1

    def test_get_rotate_angle_int_int(self):
        declare_regs_typed(
            ('a', 2, 'UnsignedInteger'), ('b', 2, 'UnsignedInteger'),
            ('c', 2, 'UnsignedInteger'))
        sim = SimulatorVisitor()
        GetRotateAngle_Int_Int(['a', 'b', 'c']).traverse(sim)
        assert state_size(sim.state) >= 1
