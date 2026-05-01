# Generated from YAML definition

from ..core.operation import AbstractComposite
from ..core.registry import OperationRegistry
from ..core.utils import merge_controllers
import math

class QuantumPhaseEstimation(AbstractComposite):
    """Quantum phase estimation for finding eigenvalues"""
    def __init__(self, reg_list, param_list=None, operations=None):
        if param_list is None:
            param_list = []
        AbstractComposite.__init__(self, reg_list=reg_list, param_list=param_list, operations=operations)
        self.precision_reg = reg_list[0]
        self.eigenstate_reg = reg_list[1]
        self.n_precision = param_list[0]
        self.unitary_name = param_list[1]
        # Complex implementation with loops/conditionals
        self._impl_structure = [{"_type": "op", "op": "Hadamard", "qregs": ["precision_reg"]}, {"_type": "comment", "text": "Controlled unitary iterations (unitary omitted for generic template)"}, {"_type": "op", "op": "InverseQFT", "qregs": ["precision_reg"]}]
        self._build_execute_method()

    def _build_execute_method(self):
        # Build program_list by expanding loops and conditionals
        self.program_list = []
        self.program_list.append(OperationRegistry.get_class("Hadamard")(reg_list=[self.precision_reg]))
        for i in range(self.n_precision):
                self.program_list.append(OperationRegistry.get_class("Init_Unsafe")(reg_list=[self.eigenstate_reg], param_list=[0]).control_by_all_ones([self.precision_reg]))
                self.program_list.append(OperationRegistry.get_class("PhaseGate")(reg_list=[self.precision_reg], param_list=[0.785398, 0.01]))
        self.program_list.append(OperationRegistry.get_class("InverseQFT")(reg_list=[self.precision_reg]))
        self.declare_program_list()