# Generated from YAML definition

from ..core.operation import AbstractComposite
from ..core.registry import OperationRegistry
from ..core.utils import merge_controllers
import math

class ShorFactor(AbstractComposite):
    """Shor factorization stub — see notes: ExpMod/ModMul require Python (not DSL-expressible)"""
    def __init__(self, reg_list, param_list=None, temp_reg_list=[('measure_flag', 1)]):
        if param_list is None:
            param_list = []
        AbstractComposite.__init__(self, reg_list=reg_list, param_list=param_list, temp_reg_list=temp_reg_list)
        self.work_reg = reg_list[0]
        self.anc_reg = reg_list[1]
        self.N = param_list[0]
        self.a = param_list[1]
        self.n_qubits = int(math.log2(self.N)) + 1
        self.precision = self.n_qubits * 2
        # Store temp registers as instance attributes
        self._temp_reg_dict = {}
        self._temp_reg_dict['measure_flag'] = ('measure_flag', 1)
        self.measure_flag = 'measure_flag'
        # Complex implementation with loops/conditionals
        self._impl_structure = [{"_type": "op", "op": "Init_Unsafe", "qregs": ["anc_reg"], "params": [1]}, {"_type": "op", "op": "Hadamard_NDigits", "qregs": ["work_reg"], "params": ["precision"]}, {"_type": "op", "op": "Init_Unsafe", "qregs": ["anc_reg"], "params": [0], "controllers": {"all_ones": ["work_reg"]}}, {"_type": "op", "op": "InverseQFT", "qregs": ["work_reg"]}]
        self._build_execute_method()

    def _build_execute_method(self):
        # Build program_list by expanding loops and conditionals
        self.program_list = []
        self.program_list.append(OperationRegistry.get_class("Init_Unsafe")(reg_list=[self.anc_reg], param_list=[1]))
        self.program_list.append(OperationRegistry.get_class("Hadamard_NDigits")(reg_list=[self.work_reg], param_list=[self.precision]))
        self.program_list.append(OperationRegistry.get_class("Init_Unsafe")(reg_list=[self.anc_reg], param_list=[0]).control_by_all_ones([self.work_reg]))
        self.program_list.append(OperationRegistry.get_class("InverseQFT")(reg_list=[self.work_reg]))
        self.declare_program_list()