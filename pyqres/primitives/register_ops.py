import pysparq

from ..core.operation import Primitive
from ..core.metadata import RegisterMetadata
from ..core.utils import merge_controllers
from ..core.simulator import PyQSparseOperationWrapper


class SplitRegister(Primitive):
    """Split a register into sub-registers, or merge them back on dagger."""

    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)

    def render_this(self, indent=0, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = controllers_ctx or {}
        dagger_ctx = self.dagger_flag ^ dagger_ctx
        split_str = ", ".join(
            f"{reg}({size})"
            for reg, size in zip(self.reg_list[1:], self.param_list))
        action = "MergeRegister" if dagger_ctx else "SplitRegister"
        return f"{' ' * indent}{action}: {self.reg_list[0]} {'<-' if dagger_ctx else '->'} {split_str}"

    def enter(self, dagger_ctx=False, controllers_ctx=None):
        register_metadata_ = RegisterMetadata.get_register_metadata()
        dagger_ctx = self.dagger_flag ^ dagger_ctx
        if not dagger_ctx:
            register_metadata_.split_register(
                self.reg_list[0],
                list(zip(self.reg_list[1:], self.param_list)))

    def exit(self, dagger_ctx=False, controllers_ctx=None):
        register_metadata_ = RegisterMetadata.get_register_metadata()
        dagger_ctx = self.dagger_flag ^ dagger_ctx
        if dagger_ctx:
            register_metadata_.merge_register(
                self.reg_list[0], list(self.reg_list[1:]))

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        dagger_ctx = self.dagger_flag ^ dagger_ctx
        if not dagger_ctx:
            return [
                PyQSparseOperationWrapper(
                    pysparq.SplitRegister(self.reg_list[0], reg, size))
                for reg, size in zip(self.reg_list[1:], self.param_list)]
        else:
            return [
                PyQSparseOperationWrapper(
                    pysparq.CombineRegister(self.reg_list[0], reg))
                for reg in self.reg_list[1:]]


class CombineRegister(Primitive):
    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.first = reg_list[0]
        self.second = reg_list[1]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.CombineRegister(self.first, self.second))
        obj.set_dagger(dagger_ctx ^ self.dagger_flag)
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0


class Push(Primitive):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg = reg_list[0]
        self.garbage = param_list[0]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(pysparq.Push(self.reg, self.garbage))
        obj.set_dagger(dagger_ctx ^ self.dagger_flag)
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0


class Pop(Primitive):
    def __init__(self, reg_list, param_list=None):
        super().__init__(reg_list, param_list)
        self.reg = reg_list[0]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(pysparq.Pop(self.reg))
        obj.set_dagger(dagger_ctx ^ self.dagger_flag)
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0


class AddRegister(Primitive):
    """Add a new register to the quantum state.

    This is a meta-operation that extends the state space.
    Used in state preparation and block encoding algorithms.
    """

    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg_name = param_list[0]
        self.reg_type = param_list[1]  # e.g., 'UnsignedInteger', 'SignedInteger', 'Boolean', 'Rational'
        self.reg_size = param_list[2]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        # Map string type to pysparq StateStorageType
        type_map = {
            'UnsignedInteger': pysparq.UnsignedInteger,
            'SignedInteger': pysparq.SignedInteger,
            'Boolean': pysparq.Boolean,
            'Rational': pysparq.Rational,
            'General': pysparq.General,
        }
        reg_type = type_map.get(self.reg_type, pysparq.General)
        return PyQSparseOperationWrapper(
            pysparq.AddRegister(self.reg_name, reg_type, self.reg_size))

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0


class RemoveRegister(Primitive):
    """Remove a register from the quantum state.

    This is a meta-operation that shrinks the state space.
    Used for cleaning up temporary registers.
    """

    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg_name = param_list[0]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        return PyQSparseOperationWrapper(pysparq.RemoveRegister(self.reg_name))

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return 0
