"""Debug primitives: only run in debug mode, excluded from resource estimation."""

import pysparq

from ..core.operation import Primitive
from ..core.utils import merge_controllers


class DebugPrimitive(Primitive):
    """Base class for debug-only primitives.

    In debug mode (default), these primitives execute normally via the pysparq
    simulator and contribute to simulation results. In release mode, they are
    silently skipped (no-op) so they do not affect resource counts.

    Subclasses must implement:
    - pysparq_op() — the pysparq operator to call
    - t_count() — resource cost when in release mode (typically 0)
    """

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        """Execute the debug operation via pysparq.

        Only called in debug mode. In release mode, return a no-op.
        """
        from ..core.simulator import PyQSparseOperationWrapper
        op = self.pysparq_op()
        return PyQSparseOperationWrapper(op)

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        """Release-mode T-count is always 0 — debug ops are excluded from estimates."""
        return 0

    def pysparq_op(self):
        """Return the pysparq operator instance. Override in subclass."""
        raise NotImplementedError


class CheckNan(DebugPrimitive):
    """Check for NaN (Not-a-Number) values in the quantum state amplitudes.

    Inspects the internal sparse state representation and raises an error if any
    amplitude is NaN. Used for debugging numerical stability of arithmetic circuits.

    In release mode: silently skips (no-op).

    See Also:
        CheckNormalization: checks that amplitudes are normalized
    """

    def pysparq_op(self):
        return pysparq.CheckNan()


class CheckNormalization(DebugPrimitive):
    """Check that the quantum state is properly normalized (sum of |amplitudes|^2 = 1).

    Optionally checks against a threshold for numerical precision.

    In release mode: silently skips (no-op).

    Args:
        threshold: Maximum allowed deviation from unit norm. Defaults to 1e-9.

    See Also:
        CheckNan: checks for NaN amplitudes
    """

    def __init__(self, reg_list=None, param_list=None, threshold: float = 1e-9):
        super().__init__(reg_list=reg_list or [], param_list=param_list or [])
        self.threshold = threshold

    def pysparq_op(self):
        return pysparq.CheckNormalization(self.threshold)
