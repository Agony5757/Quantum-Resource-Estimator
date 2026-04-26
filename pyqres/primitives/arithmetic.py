import pysparq

from ..core.operation import Primitive
from ..core.utils import get_control_qubit_count, merge_controllers, reg_sz, mcx_t_count
from ..core.simulator import PyQSparseOperationWrapper


class Add_UInt_UInt(Primitive):
    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.input_reg1 = reg_list[0]
        self.input_reg2 = reg_list[1]
        self.output_reg = reg_list[2]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.Add_UInt_UInt(self.input_reg1, self.input_reg2, self.output_reg))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        n = reg_sz(self.input_reg1)
        return (n - 1) * mcx_t_count(ncontrols + 2)


class Add_UInt_UInt_InPlace(Primitive):
    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.input_reg = reg_list[0]
        self.output_reg = reg_list[1]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.Add_UInt_UInt_InPlace(self.input_reg, self.output_reg))
        obj.set_dagger(dagger_ctx ^ self.dagger_flag)
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        n = reg_sz(self.input_reg)
        return 2 * (n - 1) * mcx_t_count(ncontrols + 2)


class Add_UInt_ConstUInt(Primitive):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.input_reg = reg_list[0]
        self.output_reg = reg_list[1]
        self.add = param_list[0]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.Add_UInt_ConstUInt(self.input_reg, self.add, self.output_reg))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        n = reg_sz(self.input_reg)
        return (n - 1) * mcx_t_count(ncontrols + 2)


class Add_ConstUInt(Primitive):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.input_reg = reg_list[0]
        self.add = param_list[0]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.Add_ConstUInt(self.input_reg, self.add))
        obj.set_dagger(dagger_ctx ^ self.dagger_flag)
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        n = reg_sz(self.input_reg)
        return (n - 1) * mcx_t_count(ncontrols + 2)


class Mult_UInt_ConstUInt(Primitive):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.input_reg = reg_list[0]
        self.output_reg = reg_list[1]
        self.multiplier = param_list[0]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.Mult_UInt_ConstUInt(self.input_reg, self.multiplier, self.output_reg))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        n = reg_sz(self.input_reg)
        return (n - 1) ** 2 * mcx_t_count(ncontrols + 2)


class ShiftLeft(Primitive):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg = reg_list[0]
        self.shift_bits = param_list[0]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(pysparq.ShiftLeft(self.reg, self.shift_bits))
        obj.set_dagger(dagger_ctx ^ self.dagger_flag)
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0


class ShiftRight(Primitive):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg = reg_list[0]
        self.shift_bits = param_list[0]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(pysparq.ShiftRight(self.reg, self.shift_bits))
        obj.set_dagger(dagger_ctx ^ self.dagger_flag)
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0


class Compare_UInt_UInt(Primitive):
    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.left_reg = reg_list[0]
        self.right_reg = reg_list[1]
        self.less_flag_reg = reg_list[2]
        self.equal_flag_reg = reg_list[3]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.Compare_UInt_UInt(
                self.left_reg, self.right_reg,
                self.less_flag_reg, self.equal_flag_reg))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        n = reg_sz(self.left_reg)
        return (n - 1) * mcx_t_count(ncontrols + 2)


class Less_UInt_UInt(Primitive):
    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.left_reg = reg_list[0]
        self.right_reg = reg_list[1]
        self.less_flag_reg = reg_list[2]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.Less_UInt_UInt(self.left_reg, self.right_reg, self.less_flag_reg))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        n = reg_sz(self.left_reg)
        return (n - 1) * mcx_t_count(ncontrols + 2)


class GetMid_UInt_UInt(Primitive):
    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.left_reg = reg_list[0]
        self.right_reg = reg_list[1]
        self.mid_reg = reg_list[2]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.GetMid_UInt_UInt(self.left_reg, self.right_reg, self.mid_reg))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        n = reg_sz(self.left_reg)
        return (n - 1) * mcx_t_count(ncontrols + 2)


class Assign(Primitive):
    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.src = reg_list[0]
        self.dst = reg_list[1]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(pysparq.Assign(self.src, self.dst))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0


class Swap_General_General(Primitive):
    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.reg1 = reg_list[0]
        self.reg2 = reg_list[1]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.Swap_General_General(self.reg1, self.reg2))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0


class Div_Sqrt_Arccos_Int_Int(Primitive):
    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.left_reg = reg_list[0]
        self.right_reg = reg_list[1]
        self.output_reg = reg_list[2]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.Div_Sqrt_Arccos_Int_Int(self.left_reg, self.right_reg, self.output_reg))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        raise NotImplementedError("Div_Sqrt_Arccos_Int_Int t_count not yet parameterized")


class Sqrt_Div_Arccos_Int_Int(Primitive):
    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.left_reg = reg_list[0]
        self.right_reg = reg_list[1]
        self.output_reg = reg_list[2]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.Sqrt_Div_Arccos_Int_Int(self.left_reg, self.right_reg, self.output_reg))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        raise NotImplementedError("Sqrt_Div_Arccos_Int_Int t_count not yet parameterized")


class GetRotateAngle_Int_Int(Primitive):
    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.left_reg = reg_list[0]
        self.right_reg = reg_list[1]
        self.output_reg = reg_list[2]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.GetRotateAngle_Int_Int(self.left_reg, self.right_reg, self.output_reg))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        raise NotImplementedError("GetRotateAngle_Int_Int t_count not yet parameterized")


# ==============================================================================
# New arithmetic primitives (Phase 2)
# ==============================================================================


class Add_Mult_UInt_ConstUInt(Primitive):
    """Multiply-add: output = input * multiplier + add_const.

    Computes output = input * multiplier + add_const in a single fused operation.
    Used in block encoding and Shor's algorithm.
    """
    __self_conjugate__ = True  # Self-adjoint (XOR-based)

    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.input_reg = reg_list[0]
        self.output_reg = reg_list[1]
        self.multiplier = param_list[0]
        self.add_constant = param_list[1] if len(param_list) > 1 else 0

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.Add_Mult_UInt_ConstUInt(self.input_reg, self.multiplier, self.output_reg))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        n = reg_sz(self.input_reg)
        return (n - 1) * mcx_t_count(ncontrols + 2)


class AddAssign_AnyInt_AnyInt(Primitive):
    """In-place addition: dst += src on arbitrary integer types.

    Type-flexible in-place addition across Integer register types.
    Used in CKS TOperator for column position finding.
    """
    __self_conjugate__ = True  # Self-adjoint (inverse = subtraction)

    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.input_reg = reg_list[0]
        self.output_reg = reg_list[1]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.AddAssign_AnyInt_AnyInt(self.input_reg, self.output_reg))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        n = reg_sz(self.input_reg)
        return (n - 1) * mcx_t_count(ncontrols + 2)


class CustomArithmetic(Primitive):
    """Custom classical arithmetic function applied as a quantum operation.

    Args:
        reg_list: [reg1, reg2, ...] - input and output registers
        param_list: [func, in_sz, out_sz]
            func: callable f(input_values) -> output_values
            in_sz: total input bit size
            out_sz: total output bit size

    Used in Shor's modular exponentiation.
    """
    __self_conjugate__ = True  # Self-adjoint when func is its own inverse

    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.regs = reg_list
        self.func = param_list[0]
        self.in_sz = param_list[1]
        self.out_sz = param_list[2]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.CustomArithmetic(self.regs, self.in_sz, self.out_sz, self.func))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        raise NotImplementedError("CustomArithmetic t_count depends on the function")


class PlusOneAndOverflow(Primitive):
    """Increment a register by 1, with separate overflow flag qubit.

    Used in block encoding for carry/borrow logic.
    Inverse = MinusOneAndOverflow (different op, use dagger).
    """
    __self_conjugate__ = False  # Inverse is MinusOneAndOverflow

    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.main_reg = reg_list[0]
        self.overflow_reg = reg_list[1]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        dagger = dagger_ctx ^ self.dagger_flag
        obj = PyQSparseOperationWrapper(
            pysparq.PlusOneAndOverflow(self.main_reg, self.overflow_reg))
        obj.set_dagger(dagger)
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        return mcx_t_count(ncontrols + 1)  # ripple-carry addition


class GetDataAddr(Primitive):
    """Compute XOR-based data address for QRAM access.

    data_addr ^= data_offset + row * row_size + col
    Self-adjoint: applying twice cancels (XOR property).
    Used in CKS TOperator for matrix element loading.
    """
    __self_conjugate__ = True

    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg_offset = reg_list[0]
        self.reg_row = reg_list[1]
        self.reg_col = reg_list[2]
        self.row_size = param_list[0]
        self.reg_data_offset = reg_list[3]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.GetDataAddr(
                self.reg_offset, self.reg_row, self.reg_col,
                self.row_size, self.reg_data_offset))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        n = reg_sz(self.reg_offset)
        return n * mcx_t_count(ncontrols + 1)


class GetRowAddr(Primitive):
    """Compute XOR-based row address for sparse QRAM access.

    row_addr ^= sparse_offset + row * row_size
    Self-adjoint: applying twice cancels (XOR property).
    Used in CKS TOperator for column position finding.
    """
    __self_conjugate__ = True

    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg_offset = reg_list[0]
        self.reg_row = reg_list[1]
        self.row_size = param_list[0]
        self.reg_row_offset = reg_list[2]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.GetRowAddr(
                self.reg_offset, self.reg_row, self.row_size, self.reg_row_offset))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        n = reg_sz(self.reg_offset)
        return n * mcx_t_count(ncontrols + 1)
