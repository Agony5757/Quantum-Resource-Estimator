# Generated from YAML definition

from ..core.operation import StandardComposite
from ..core.registry import OperationRegistry
from ..core.utils import merge_controllers
import math

class StatePrep_via_QRAM(StandardComposite):
    """Prepare quantum state from QRAM-stored probability amplitudes"""
    def __init__(self, reg_list, param_list=None, temp_reg_list=[('rotation', 1), ('data_tmp', 1)]):
        if param_list is None:
            param_list = []
        StandardComposite.__init__(self, reg_list=reg_list, param_list=param_list, temp_reg_list=temp_reg_list)
        self.work_qubit = reg_list[0]
        self.addr_size = param_list[0]
        self.data_size = param_list[1]
        # Store temp registers as instance attributes
        self._temp_reg_dict = {}
        self._temp_reg_dict['rotation'] = ('rotation', 1)
        self.rotation = 'rotation'
        self._temp_reg_dict['data_tmp'] = ('data_tmp', 1)
        self.data_tmp = 'data_tmp'
        # Complex implementation with loops/conditionals
        self._impl_structure = [{"_type": "op", "op": "ShiftRight", "qregs": ["work_qubit"], "params": [1]}, {"_type": "comment", "text": "Tree-based state preparation loop"}, {"_type": "op", "op": "ShiftRight", "qregs": ["work_qubit"], "params": [1]}, {"_type": "op", "op": "ClearZero", "qregs": []}]
        self._build_execute_method()

    def _build_execute_method(self):
        # Build program_list by expanding loops and conditionals
        self.program_list = []
        self.program_list.append(OperationRegistry.get_class("ShiftRight")(reg_list=[self.work_qubit], param_list=[1]))
        for i in range(self.addr_size):
                self.program_list.append(OperationRegistry.get_class("SplitRegister")(reg_list=[self.work_qubit], param_list=[self.rotation]))
                self.program_list.append(OperationRegistry.get_class("Hadamard")(reg_list=[self.rotation]))
                self.program_list.append(OperationRegistry.get_class("CombineRegister")(reg_list=[self.work_qubit, self.rotation]))
                self.program_list.append(OperationRegistry.get_class("ShiftLeft")(reg_list=[self.work_qubit], param_list=[1]))
        self.program_list.append(OperationRegistry.get_class("ShiftRight")(reg_list=[self.work_qubit], param_list=[1]))
        self.program_list.append(OperationRegistry.get_class("ClearZero")())
        self.declare_program_list()