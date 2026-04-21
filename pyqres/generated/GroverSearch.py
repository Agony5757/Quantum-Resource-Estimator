# Generated from YAML definition

from ..core.operation import StandardComposite
from ..core.registry import OperationRegistry
from ..core.utils import merge_controllers
import math

class GroverSearch(StandardComposite):
    """Grover search with oracle and diffusion operator"""
    def __init__(self, reg_list, param_list=None, temp_reg_list=[('flag', 1)]):
        if param_list is None:
            param_list = []
        StandardComposite.__init__(self, reg_list=reg_list, param_list=param_list, temp_reg_list=temp_reg_list)
        self.addr_reg = reg_list[0]
        self.data_reg = reg_list[1]
        self.search_data_reg = reg_list[2]
        self.n_qubits = param_list[0]
        self.n_repeats = param_list[1]
        self.addr_size = self.n_qubits
        # Store temp registers as instance attributes
        self._temp_reg_dict = {}
        self._temp_reg_dict['flag'] = ('flag', 1)
        self.flag = 'flag'
        # Complex implementation with loops/conditionals
        self._impl_structure = [{"_type": "op", "op": "Hadamard_NDigits", "qregs": ["addr_reg"], "params": ["n_qubits"]}, {"_type": "comment", "text": "Oracle application - QRAM-based oracle marks target"}]
        self._build_execute_method()

    def _build_execute_method(self):
        # Build program_list by expanding loops and conditionals
        self.program_list = []
        self.program_list.append(OperationRegistry.get_class("Hadamard_NDigits")(reg_list=[self.addr_reg], param_list=[self.n_qubits]))
        for i in range(self.n_repeats):
                self.program_list.append(OperationRegistry.get_class("QRAM")(reg_list=[self.addr_reg, self.data_reg], param_list=[0]))
                self.program_list.append(OperationRegistry.get_class("Hadamard_NDigits")(reg_list=[self.addr_reg], param_list=[self.n_qubits]))
                self.program_list.append(OperationRegistry.get_class("X")(reg_list=[self.addr_reg]))
                self.program_list.append(OperationRegistry.get_class("CNOT")(reg_list=[self.addr_reg, self.flag]))
                self.program_list.append(OperationRegistry.get_class("X")(reg_list=[self.addr_reg]))
                self.program_list.append(OperationRegistry.get_class("Hadamard_NDigits")(reg_list=[self.addr_reg], param_list=[self.n_qubits]))
                self.program_list.append(OperationRegistry.get_class("QRAM")(reg_list=[self.addr_reg, self.data_reg], param_list=[0]).dagger())
        self.declare_program_list()