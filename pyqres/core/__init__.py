# Core module exports
from .operation import (
    Operation, Primitive, Composite,
    StandardComposite, AbstractComposite, mock_submodule
)
from .registry import OperationRegistry, NodeRegistry
from .metadata import (
    RegisterMetadata, ProgramMetadata, FunctionDeclaration, program_metadata
)
from .utils import (
    merge_controllers, controller2str, reg_sz, get_control_qubit_count, mcx_t_count
)
from .visitor import (
    TCounter, TDepthCounter, ToffoliCounter,
    TreeRenderer, PlainRenderer,
    tree_renderer, plain_renderer,
    get_depth, sync_t_depth, forward_t_depth
)
from .lowering import (
    LoweringEngine, ResourceEstimator,
    TCountEstimator, TDepthEstimator, ToffoliCountEstimator
)
from .simulator import SimulatorVisitor, PyQSparseOperationWrapper
