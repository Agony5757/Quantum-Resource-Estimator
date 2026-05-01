# Generated from YAML definition

from ..core.operation import StandardComposite
from ..core.registry import OperationRegistry
from ..core.utils import merge_controllers
import math

class QuantumBinarySearch(StandardComposite):
    """Quantum binary search using QRAM for database lookup"""
    def __init__(self, reg_list, param_list=None, temp_reg_list=[('flag', 1), ('left_register', 10), ('right_register', 10), ('mid_register', 10), ('midval_register', 10), ('compare_less', 1), ('compare_equal', 1)]):
        if param_list is None:
            param_list = []
        StandardComposite.__init__(self, reg_list=reg_list, param_list=param_list, temp_reg_list=temp_reg_list)
        self.address_offset = reg_list[0]
        self.target = reg_list[1]
        self.result = reg_list[2]
        self.total_length = param_list[0]
        self.max_step = param_list[1]
        self.addr_size = self.total_length.bit_length()
        # Store temp registers as instance attributes
        self._temp_reg_dict = {}
        self._temp_reg_dict['flag'] = ('flag', 1)
        self.flag = 'flag'
        self._temp_reg_dict['left_register'] = ('left_register', 10)
        self.left_register = 'left_register'
        self._temp_reg_dict['right_register'] = ('right_register', 10)
        self.right_register = 'right_register'
        self._temp_reg_dict['mid_register'] = ('mid_register', 10)
        self.mid_register = 'mid_register'
        self._temp_reg_dict['midval_register'] = ('midval_register', 10)
        self.midval_register = 'midval_register'
        self._temp_reg_dict['compare_less'] = ('compare_less', 1)
        self.compare_less = 'compare_less'
        self._temp_reg_dict['compare_equal'] = ('compare_equal', 1)
        self.compare_equal = 'compare_equal'
        # Complex implementation with loops/conditionals
        self._impl_structure = [{"_type": "op", "op": "X", "qregs": ["flag"]}, {"_type": "op", "op": "Assign", "qregs": ["address_offset", "left_register"]}, {"_type": "op", "op": "Add_ConstUInt", "qregs": ["left_register", "left_register"], "params": ["total_length"]}, {"_type": "comment", "text": "Binary search loop"}, {"_type": "op", "op": "X", "qregs": ["flag"]}]
        self._build_execute_method()

    def _build_execute_method(self):
        # Build program_list by expanding loops and conditionals
        self.program_list = []
        self.program_list.append(OperationRegistry.get_class("X")(reg_list=[self.flag]))
        self.program_list.append(OperationRegistry.get_class("Assign")(reg_list=[self.address_offset, self.left_register]))
        self.program_list.append(OperationRegistry.get_class("Add_ConstUInt")(reg_list=[self.left_register, self.left_register], param_list=[self.total_length]))
        for i in range(self.max_step):
                self.program_list.append(OperationRegistry.get_class("GetMid_UInt_UInt")(reg_list=[self.left_register, self.right_register, self.mid_register]))
                self.program_list.append(OperationRegistry.get_class("QRAM")(reg_list=[self.mid_register, self.midval_register], param_list=[0]))
                self.program_list.append(OperationRegistry.get_class("Compare_UInt_UInt")(reg_list=[self.midval_register, self.target, self.compare_less, self.compare_equal]))
                self.program_list.append(OperationRegistry.get_class("Assign")(reg_list=[self.mid_register, self.result]))
        self.program_list.append(OperationRegistry.get_class("X")(reg_list=[self.flag]))
        self.declare_program_list()