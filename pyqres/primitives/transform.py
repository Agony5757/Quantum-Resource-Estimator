import pysparq
import sympy as sp

from ..core.operation import Primitive
from ..core.utils import merge_controllers, reg_sz, get_control_qubit_count, mcx_t_count
from ..core.simulator import PyQSparseOperationWrapper


class QFT(Primitive):
    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.reg = reg_list[0]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(pysparq.QFT(self.reg))
        obj.set_dagger(dagger_ctx ^ self.dagger_flag)
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        n = reg_sz(self.reg)
        return (n - 1) * n // 2 * mcx_t_count(ncontrols + 2)


class InverseQFT(Primitive):
    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.reg = reg_list[0]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(pysparq.inverseQFT(self.reg))
        obj.set_dagger(dagger_ctx ^ self.dagger_flag)
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        n = reg_sz(self.reg)
        return (n - 1) * n // 2 * mcx_t_count(ncontrols + 2)


class Reflection_Bool(Primitive):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg = reg_list[0]
        self.inverse = param_list[0]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.Reflection_Bool(self.reg, self.inverse))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        n = reg_sz(self.reg)
        return mcx_t_count(ncontrols + n)
