import pysparq
from .utils import merge_controllers
from .metadata import RegisterMetadata


class PyQSparseOperationWrapper:
    """Wrapper for pysparq operations with controller and dagger support."""

    def __init__(self, op):
        self.op = op
        self.dagger = False

    def set_controller(self, controllers_ctx):
        if 'conditioned_by_nonzero' in controllers_ctx:
            self.op.conditioned_by_nonzeros(controllers_ctx['conditioned_by_nonzero'])
        if 'conditioned_by_all_ones' in controllers_ctx:
            self.op.conditioned_by_all_ones(controllers_ctx['conditioned_by_all_ones'])
        if 'conditioned_by_bit' in controllers_ctx:
            self.op.conditioned_by_bit(controllers_ctx['conditioned_by_bit'])
        if 'conditioned_by_value' in controllers_ctx:
            self.op.conditioned_by_value(controllers_ctx['conditioned_by_value'])

    def set_dagger(self, dagger_ctx):
        self.dagger = dagger_ctx

    def __call__(self, sparse_state):
        if self.dagger:
            return self.op.dag(sparse_state)
        else:
            return self.op(sparse_state)


_TYPE_MAP = {
    "General": pysparq.StateStorageType.General,
    "UnsignedInteger": pysparq.StateStorageType.UnsignedInteger,
    "SignedInteger": pysparq.StateStorageType.SignedInteger,
    "Boolean": pysparq.StateStorageType.Boolean,
    "Rational": pysparq.StateStorageType.Rational,
}


class SimulatorVisitor:
    """Visitor that executes operations on a pysparq sparse state."""

    def __init__(self, verbose=False):
        registers = RegisterMetadata.get_registers()
        register_types = RegisterMetadata.get_register_types()
        for reg_name, reg_size in registers.items():
            if not isinstance(reg_size, int):
                raise ValueError(
                    f"Register size must be integer. Got: {reg_name}: {reg_size}")
            reg_type_name = register_types.get(reg_name, "General")
            storage_type = _TYPE_MAP.get(reg_type_name, pysparq.StateStorageType.General)
            pysparq.System.add_register(reg_name, storage_type, reg_size)

        self.state = pysparq.SparseState()
        self.skip = None
        self.verbose = verbose

    def enter(self, node):
        if self.skip:
            return

    def exit(self, node):
        if node == self.skip:
            self.skip = None

    def visit(self, node, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = controllers_ctx or {}
        if hasattr(node, "pyqsparse_object"):
            obj = node.pyqsparse_object(dagger_ctx, controllers_ctx)
            if isinstance(obj, list):
                for op in obj:
                    op(self.state)
                    if self.verbose:
                        pysparq.StatePrint(pysparq.StatePrintDisplay.Detail)(self.state)
            else:
                obj(self.state)
                if self.verbose:
                    pysparq.StatePrint(pysparq.StatePrintDisplay.Detail)(self.state)
            self.skip = id(node)
        elif len(node.program_list) == 0:
            raise NotImplementedError(
                f"Node missing pyqsparse_object method: {type(node)}")

    def print_state(self, option=None, precision=None):
        option = option or pysparq.StatePrintDisplay.Default
        if precision:
            pysparq.StatePrint(option, precision)(self.state)
        else:
            pysparq.StatePrint(option)(self.state)
