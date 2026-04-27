import pysparq

from ..core.operation import Primitive
from ..core.utils import merge_controllers, get_control_qubit_count, mcx_t_count, reg_sz
from ..core.simulator import PyQSparseOperationWrapper


class CondRot_General_Bool(Primitive):
    """Conditional rotation based on rational value register.

    Supports two forms:
    - 2-arg (resource estimation only): reg_list=[cond_reg, target_reg]
    - 3-arg (simulation): reg_list=[cond_reg, target_reg], param_list=[angle_function]
      where angle_function is a Callable[[int], list[complex]].

    pysparq requires the 3-arg form: CondRot_General_Bool(reg_in, reg_out, angle_function).
    angle_function receives the register value and returns a 2x2 unitary matrix.
    """
    def __init__(self, reg_list, param_list=None, angle_function=None):
        super().__init__(reg_list, param_list)
        self.cond_reg = reg_list[0]
        self.target_reg = reg_list[1]
        # Prefer keyword arg; fall back to param_list[0]
        self.angle_function = angle_function if angle_function is not None else (
            param_list[0] if param_list else None)

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        if self.angle_function is not None:
            obj = PyQSparseOperationWrapper(
                pysparq.CondRot_General_Bool(
                    self.cond_reg, self.target_reg, self.angle_function))
        else:
            # Fallback for resource estimation without angle_function:
            # use identity rotation (theta=0)
            n = reg_sz(self.cond_reg)
            default_func = lambda value, _n=n: [complex(1, 0), 0j, 0j, complex(1, 0)]
            obj = PyQSparseOperationWrapper(
                pysparq.CondRot_General_Bool(
                    self.cond_reg, self.target_reg, default_func))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        if self.angle_function is not None:
            raise NotImplementedError(
                "CondRot_General_Bool (3-arg) t_count depends on angle_function")
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        if ncontrols == 0:
            return 0
        return 4 * ncontrols + 3


class CondRot_General_Bool_QW(Primitive):
    """Conditional rotation for quantum walk operations.

    Similar to CondRot_General_Bool but optimized for quantum walk style
    amplitude loading with 2x2 rotation matrices. Uses CondRot_Rational_Bool
    internally with a matrix-structured angle function.
    """
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.j_reg = reg_list[0]
        self.k_reg = reg_list[1]
        self.reg_in = reg_list[2]
        self.reg_out = reg_list[3]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        raise NotImplementedError(
            "CondRot_General_Bool_QW: use CondRot_Rational_Bool or "
            "CondRot_General_Bool with angle_function instead")

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        raise NotImplementedError(
            "CondRot_General_Bool_QW t_count depends on matrix structure")


class ZeroConditionalPhaseFlip(Primitive):
    """Apply phase flip to states where all specified qubits are zero."""
    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.qubit_regs = reg_list

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        # Multi-controlled Z gate
        obj = PyQSparseOperationWrapper(
            pysparq.ZeroConditionalPhaseFlip([r for r in self.qubit_regs]))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = len(self.qubit_regs)
        if ncontrols == 0:
            return 0
        return 4 * ncontrols + 1


class RangeConditionalPhaseFlip(Primitive):
    """Apply phase flip to states in a specified range."""
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg = reg_list[0]
        self.low = param_list[0]
        self.high = param_list[1]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.RangeConditionalPhaseFlip(self.reg, self.low, self.high))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        size = self.high - self.low + 1
        return size * (mcx_t_count(ncontrols + 1) + 3)


# ==============================================================================
# New conditional rotation primitives (Phase 2)
# ==============================================================================


class CondRot_Rational_Bool(Primitive):
    """Conditional rotation using rational (fractional) angle encoding.

    Applies a rotation to the target qubit based on the rational value in the
    input register. Used in CKS quantum walk and block encoding.

    Note: pysparq marks this as self-adjoint (CondRot_Rational_Bool† = CondRot_Rational_Bool).
    """
    __self_conjugate__ = True

    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.reg_in = reg_list[0]
        self.reg_out = reg_list[1]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.CondRot_Rational_Bool(self.reg_in, self.reg_out))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        if ncontrols == 0:
            return 0
        return 4 * ncontrols + 3


class Rot_GeneralUnitary(Primitive):
    """General unitary rotation specified by an arbitrary 2x2 complex matrix.

    Args:
        reg_list: [register_name]
        param_list: [unitary_matrix] where unitary_matrix is a 4-element
            list [a, b, c, d] representing [[a, b], [c, d]].

    Used in block encoding for arbitrary rotation angles.
    """
    __self_conjugate__ = False  # Inverse = conjugate transpose

    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg = reg_list[0]
        self.unitary_matrix = param_list[0]  # list of 4 complex numbers

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        dagger = dagger_ctx ^ self.dagger_flag
        obj = PyQSparseOperationWrapper(
            pysparq.Rot_GeneralUnitary(self.reg, self.unitary_matrix))
        obj.set_dagger(dagger)
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        raise NotImplementedError(
            "Rot_GeneralUnitary t_count depends on the matrix decomposition")
