"""Measurement and observation primitives.

These operations interact with the quantum state for measurement or inspection.
They have zero T-count since they don't involve non-Clifford gates.
"""
import pysparq

from ..core.operation import Primitive
from ..core.utils import merge_controllers
from ..core.simulator import PyQSparseOperationWrapper


class PartialTrace(Primitive):
    """Trace out specified registers from the quantum state.

    Removes (traces over) the degrees of freedom of given registers,
    producing a reduced density matrix for the remaining registers.
    T-count = 0.
    """
    __self_conjugate__ = True

    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.reg_names = reg_list  # list of register names to trace out

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.PartialTrace(list(self.reg_names)))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0


class PartialTraceSelect(Primitive):
    """Selectively trace out registers based on their values.

    Keeps only basis states where each named register has the specified value.
    T-count = 0.
    """
    __self_conjugate__ = True

    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.name_value_map = dict(zip(reg_list, param_list))

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.PartialTraceSelect(self.name_value_map))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0


class PartialTraceSelectRange(Primitive):
    """Trace out registers in a specified range of values.

    Keeps only basis states where the register value falls within [low, high].
    T-count = 0.
    """
    __self_conjugate__ = True

    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg = reg_list[0]
        self.low = param_list[0]
        self.high = param_list[1]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.PartialTraceSelectRange(self.reg, (self.low, self.high)))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0


class Prob(Primitive):
    """Compute measurement probabilities for the current quantum state.

    Returns the probability distribution over basis states.
    T-count = 0 (classical post-processing).
    """
    __self_conjugate__ = True

    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(pysparq.Prob())
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0


class StatePrint(Primitive):
    """Print the current quantum state (for debugging).

    Display format controlled by the disp parameter:
      0 = Default
      1 = Binary
      2 = Detailed
      3 = Probabilities
      4 = StateVector
    T-count = 0 (I/O operation).
    """
    __self_conjugate__ = True

    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.disp = param_list[0] if param_list else 0

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(pysparq.StatePrint(self.disp))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0
