import pysparq
import numpy as np

from ..core.operation import Primitive
from ..core.utils import merge_controllers
from ..core.simulator import PyQSparseOperationWrapper


def _make_memory(data_id):
    import warnings
    warnings.warn("Using a dummy memory for QRAM. This is not a realistic implementation.")
    return np.zeros(2 ** 3)


class QRAM(Primitive):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg_addr = reg_list[0]
        self.reg_data = reg_list[1]
        self.data_id = param_list[0]
        self.memory = _make_memory(self.data_id)

        # Get register sizes from metadata
        from ..core.metadata import RegisterMetadata
        meta = RegisterMetadata.get_register_metadata()
        addr_size = meta.registers.get(self.reg_addr, {}).get('size', 3)
        data_size = meta.registers.get(self.reg_data, {}).get('size', 64)

        self.qram = pysparq.QRAMCircuit_qutrit(
            addr_size=int(addr_size),
            data_size=int(data_size),
            memory=[int(x) for x in self.memory]
        )

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        return pysparq.QRAMLoad(self.qram, self.reg_addr, self.reg_data)

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        raise NotImplementedError("QRAM t_count not yet parameterized")


class QRAMFast(Primitive):
    """Fast QRAM loading using the bucket-brigade protocol.

    Loads data from a QRAM circuit at the address in addr_reg into data_reg.
    Self-conjugate: loading the same address twice doesn't cancel (not self-adjoint
    in general), but the operation itself is the same forward/inverse.
    """
    __self_conjugate__ = True

    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.qram = param_list[0]  # pysparq.QRAMCircuit_qutrit
        self.addr_reg = reg_list[0]
        self.data_reg = reg_list[1]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            pysparq.QRAMLoadFast(self.qram, self.addr_reg, self.data_reg))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        raise NotImplementedError("QRAMFast t_count not yet parameterized")
