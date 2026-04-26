# Generated from YAML definition

from ..core.operation import AbstractComposite
from ..core.registry import OperationRegistry
from ..core.utils import merge_controllers
import math

class GroverSearch(AbstractComposite):
    """Grover search: Oracle (Compare+ZeroConditionalPhaseFlip) + Diffusion operator"""
    def __init__(self, reg_list, param_list=None, temp_reg_list=[('less_flag', 1), ('equal_flag', 1)]):
        if param_list is None:
            param_list = []
        AbstractComposite.__init__(self, reg_list=reg_list, param_list=param_list, temp_reg_list=temp_reg_list)
        self.search_reg = reg_list[0]
        self.target_reg = reg_list[1]
        self.n_qubits = param_list[0]
        self.n_repeats = param_list[1]
        self.target_value = param_list[2]
        # Store temp registers as instance attributes
        self._temp_reg_dict = {}
        self._temp_reg_dict['less_flag'] = ('less_flag', 1)
        self.less_flag = 'less_flag'
        self._temp_reg_dict['equal_flag'] = ('equal_flag', 1)
        self.equal_flag = 'equal_flag'
        # Complex implementation with loops/conditionals
        self._impl_structure = [{"_type": "op", "op": "Hadamard_NDigits", "qregs": ["search_reg"], "params": ["n_qubits"]}, {"_type": "op", "op": "Init_Unsafe", "qregs": ["target_reg"], "params": ["target_value"]}, {"_type": "comment", "text": "Grover iterations: Oracle + Diffusion"}]
        self._build_execute_method()

    def _build_execute_method(self):
        # Build program_list by expanding loops and conditionals
        self.program_list = []
        self.program_list.append(OperationRegistry.get_class("Hadamard_NDigits")(reg_list=[self.search_reg], param_list=[self.n_qubits]))
        self.program_list.append(OperationRegistry.get_class("Init_Unsafe")(reg_list=[self.target_reg], param_list=[self.target_value]))
        for i in range(self.n_repeats):
                self.program_list.append(OperationRegistry.get_class("Init_Unsafe")(reg_list=[self.less_flag], param_list=[0]))
                self.program_list.append(OperationRegistry.get_class("Init_Unsafe")(reg_list=[self.equal_flag], param_list=[0]))
                self.program_list.append(OperationRegistry.get_class("Compare_UInt_UInt")(reg_list=[self.search_reg, self.target_reg, self.less_flag, self.equal_flag]))
                self.program_list.append(OperationRegistry.get_class("ZeroConditionalPhaseFlip")(reg_list=[self.equal_flag]))
                self.program_list.append(OperationRegistry.get_class("Hadamard_NDigits")(reg_list=[self.search_reg], param_list=[self.n_qubits]))
                for i in range(self.n_qubits):
                        self.program_list.append(OperationRegistry.get_class("X")(reg_list=[self.search_reg], param_list=[i]))
                self.program_list.append(OperationRegistry.get_class("ZeroConditionalPhaseFlip")(reg_list=[self.search_reg]))
                for i in range(self.n_qubits):
                        self.program_list.append(OperationRegistry.get_class("X")(reg_list=[self.search_reg], param_list=[i]))
                self.program_list.append(OperationRegistry.get_class("Hadamard_NDigits")(reg_list=[self.search_reg], param_list=[self.n_qubits]))
        self.declare_program_list()