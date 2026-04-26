import pysparq

from ..core.operation import Primitive
from ..core.utils import merge_controllers
from ..core.simulator import PyQSparseOperationWrapper


class Normalize(Primitive):
    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(pysparq.Normalize())
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0


class ClearZero(Primitive):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.epsilon = param_list[0]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(pysparq.ClearZero(self.epsilon))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0


class Init_Unsafe(Primitive):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg = reg_list[0]
        self.value = param_list[0]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(pysparq.Init_Unsafe(self.reg, self.value))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0


class Rot_GeneralStatePrep(Primitive):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg = reg_list[0]
        self.state_vector = param_list[0] if len(param_list) == 1 and hasattr(param_list[0], '__len__') else param_list

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.Rot_GeneralStatePrep(self.reg, self.state_vector))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        raise NotImplementedError("Rot_GeneralStatePrep t_count not yet parameterized")


class ViewNormalization(Primitive):
    """Apply QRAM view normalization (l2-norm normalization over a view).

    Normalizes the amplitude vector within a QRAM memory view.
    T-count = 0 (no non-Clifford gates needed for normalization).
    """
    __self_conjugate__ = True

    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(pysparq.ViewNormalization())
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0
