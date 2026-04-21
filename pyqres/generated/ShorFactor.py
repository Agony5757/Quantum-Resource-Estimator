# Generated from YAML definition

from ..core.operation import AbstractComposite
from ..core.registry import OperationRegistry
from ..core.utils import merge_controllers
import math

class ShorFactor(AbstractComposite):
    """Shor's quantum factorization algorithm (semi-classical version)"""
    def __init__(self, reg_list, param_list=None, temp_reg_list=[('measure_reg', 1)]):
        if param_list is None:
            param_list = []
        AbstractComposite.__init__(self, reg_list=reg_list, param_list=param_list, temp_reg_list=temp_reg_list)
        self.anc_reg = reg_list[0]
        self.work_reg = reg_list[1]
        self.N = param_list[0]
        self.a = param_list[1]
        self.n_qubits = int(math.log2(self.N)) + 1
        self.precision = self.self.n_qubits * 2
        # Store temp registers as instance attributes
        self._temp_reg_dict = {}
        self._temp_reg_dict['measure_reg'] = ('measure_reg', 1)
        self.measure_reg = 'measure_reg'
        # Complex implementation with loops/conditionals
        self._impl_structure = [{"_type": "op", "op": "X", "qregs": ["anc_reg"]}, {"_type": "comment", "text": "Iterative phase estimation"}]
        self._build_execute_method()

    def _build_execute_method(self):
        # Build program_list by expanding loops and conditionals
        self.program_list = []
        self.program_list.append(OperationRegistry.get_class("X")(reg_list=[self.anc_reg]))
        for i in range(self.precision):
                self.program_list.append(OperationRegistry.get_class("Hadamard")(reg_list=[self.work_reg]))
                self.program_list.append(OperationRegistry.get_class("Init_Unsafe")(reg_list=[self.work_reg], param_list=[0]).control_by_all_ones([self.anc_reg]))
                self.program_list.append(OperationRegistry.get_class("PhaseGate")(reg_list=[self.work_reg], param_list=[1.570796, 0.01]))
                self.program_list.append(OperationRegistry.get_class("X")(reg_list=[self.work_reg]))
        self.declare_program_list()