import sympy as sp
import pysparq

from ..core.operation import Primitive
from ..core.utils import reg_sz, get_control_qubit_count, merge_controllers, mcx_t_count
from ..core.simulator import PyQSparseOperationWrapper


class Hadamard(Primitive):
    __self_conjugate__ = True  # H† = H

    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.reg = reg_list[0]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(pysparq.Hadamard_Int_Full(self.reg))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        if ncontrols == 0:
            return 0
        raise NotImplementedError("Controlled Hadamard not implemented.")


class Hadamard_NDigits(Primitive):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg = reg_list[0]
        self.n_digits = param_list[0]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(pysparq.Hadamard_Int(self.reg, self.n_digits))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        if ncontrols == 0:
            return 0
        raise NotImplementedError("Controlled Hadamard_NDigits not implemented.")


class X(Primitive):
    __self_conjugate__ = True  # X† = X

    def __init__(self, reg_list, param_list=None):
        if param_list is None:
            super().__init__(reg_list)
            self.qubit_index = None
        else:
            super().__init__(reg_list=reg_list, param_list=param_list)
            self.qubit_index = param_list[0]
        self.reg = reg_list[0]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        if self.qubit_index is None:
            obj = PyQSparseOperationWrapper(pysparq.FlipBools(self.reg))
        else:
            obj = PyQSparseOperationWrapper(pysparq.Xgate_Bool(self.reg, self.qubit_index))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        sz = reg_sz(self.reg) if self.qubit_index is None else 1
        return mcx_t_count(ncontrols) * sz


class Y(Primitive):
    __self_conjugate__ = True  # Y† = Y (Hermitian)

    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg = reg_list[0]
        self.qubit_index = param_list[0]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(pysparq.Ygate_Bool(self.reg, self.qubit_index))
        obj.set_dagger(dagger_ctx ^ self.dagger_flag)
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        return mcx_t_count(ncontrols)


class CNOT(Primitive):
    __self_conjugate__ = True  # CNOT† = CNOT

    def __init__(self, reg_list, param_list=None):
        if param_list is None:
            super().__init__(reg_list)
            self.control_qubit_index = None
            self.target_qubit_index = None
        else:
            super().__init__(reg_list=reg_list, param_list=param_list)
            self.control_qubit_index = param_list[0]
            self.target_qubit_index = param_list[1]
        self.control_reg = reg_list[0]
        self.target_reg = reg_list[1]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        if self.control_qubit_index is None:
            obj = PyQSparseOperationWrapper(pysparq.FlipBools(self.target_reg))
            additional_controller = {'conditioned_by_all_ones': [self.control_reg]}
            controllers_ctx = merge_controllers(controllers_ctx, additional_controller)
            obj.set_controller(controllers_ctx)
        else:
            obj = PyQSparseOperationWrapper(
                pysparq.Xgate_Bool(self.target_reg, self.target_qubit_index))
            additional_controller = {
                'conditioned_by_bit': [(self.control_reg, self.control_qubit_index)]}
            controllers_ctx = merge_controllers(controllers_ctx, additional_controller)
            obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        sz = reg_sz(self.control_reg) if self.control_qubit_index is None else 1
        return mcx_t_count(ncontrols + 1) * sz


class Toffoli(Primitive):
    __self_conjugate__ = True  # Toffoli† = Toffoli

    def __init__(self, reg_list, param_list=None):
        if param_list is None:
            super().__init__(reg_list)
            self.control_qubit_index1 = None
            self.control_qubit_index2 = None
            self.target_qubit_index = None
        else:
            super().__init__(reg_list=reg_list, param_list=param_list)
            self.control_qubit_index1 = param_list[0]
            self.control_qubit_index2 = param_list[1]
            self.target_qubit_index = param_list[2]
        self.control_reg1 = reg_list[0]
        self.control_reg2 = reg_list[1]
        self.target_reg = reg_list[2]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        if self.control_qubit_index1 is None:
            obj = PyQSparseOperationWrapper(pysparq.FlipBools(self.target_reg))
            additional_controller = {
                'conditioned_by_all_ones': [self.control_reg1, self.control_reg2]}
            controllers_ctx = merge_controllers(controllers_ctx, additional_controller)
            obj.set_controller(controllers_ctx)
        else:
            obj = PyQSparseOperationWrapper(
                pysparq.Xgate_Bool(self.target_reg, self.target_qubit_index))
            additional_controller = {
                'conditioned_by_bit': [
                    (self.control_reg1, self.control_qubit_index1),
                    (self.control_reg2, self.control_qubit_index2)]}
            controllers_ctx = merge_controllers(controllers_ctx, additional_controller)
            obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        sz = reg_sz(self.control_reg1) if self.control_qubit_index1 is None else 1
        return mcx_t_count(ncontrols + 2) * sz


class Rx(Primitive):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg = reg_list[0]
        self.angle = param_list[0]
        self.eps = param_list[1]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        dagger = dagger_ctx ^ self.dagger_flag
        angle = -self.angle if dagger else self.angle
        obj = PyQSparseOperationWrapper(pysparq.RXgate_Bool(self.reg, angle))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        if ncontrols == 0:
            return 3 * sp.ceiling(sp.log(1 / self.eps))
        return 6 * sp.ceiling(sp.log(1 / self.eps)) + mcx_t_count(ncontrols)


class Ry(Primitive):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg = reg_list[0]
        self.angle = param_list[0]
        self.eps = param_list[1]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        dagger = dagger_ctx ^ self.dagger_flag
        angle = -self.angle if dagger else self.angle
        obj = PyQSparseOperationWrapper(pysparq.RYgate_Bool(self.reg, angle))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        if ncontrols == 0:
            return 3 * sp.ceiling(sp.log(1 / self.eps))
        return 6 * sp.ceiling(sp.log(1 / self.eps)) + mcx_t_count(ncontrols)


class PhaseGate(Primitive):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg = reg_list[0]
        self.angle = param_list[0]
        self.eps = param_list[1]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        dagger = dagger_ctx ^ self.dagger_flag
        angle = -self.angle if dagger else self.angle
        obj = PyQSparseOperationWrapper(pysparq.Phase_Bool(self.reg, angle))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        if ncontrols == 0:
            return 3 * sp.ceiling(sp.log(1 / self.eps))
        return 6 * sp.ceiling(sp.log(1 / self.eps)) + mcx_t_count(ncontrols)


class Rz(Primitive):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg = reg_list[0]
        self.angle = param_list[0]
        self.eps = param_list[1]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        dagger = dagger_ctx ^ self.dagger_flag
        angle = -self.angle if dagger else self.angle
        obj = PyQSparseOperationWrapper(pysparq.RZgate_Bool(self.reg, angle))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        if ncontrols == 0:
            return 3 * sp.ceiling(sp.log(1 / self.eps))
        return 6 * sp.ceiling(sp.log(1 / self.eps)) + mcx_t_count(ncontrols)


class U3(Primitive):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg = reg_list[0]
        self.theta = param_list[0]
        self.phi = param_list[1]
        self.lambda_ = param_list[2]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        dagger = dagger_ctx ^ self.dagger_flag
        obj = PyQSparseOperationWrapper(
            pysparq.U3gate_Bool(self.reg, self.theta, self.phi, self.lambda_))
        obj.set_dagger(dagger)
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        if ncontrols == 0:
            return 3 * sp.ceiling(sp.log(1 / self.eps))
        return 6 * sp.ceiling(sp.log(1 / self.eps)) + mcx_t_count(ncontrols)
