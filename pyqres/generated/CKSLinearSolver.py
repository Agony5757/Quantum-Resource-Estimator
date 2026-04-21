# Generated from YAML definition

from ..core.operation import AbstractComposite
from ..core.registry import OperationRegistry
from ..core.utils import merge_controllers
import math

class CKSLinearSolver(AbstractComposite):
    """CKS quantum linear system solver using Chebyshev filtering and quantum walks"""
    def __init__(self, reg_list, param_list=None):
        if param_list is None:
            param_list = []
        AbstractComposite.__init__(self, reg_list=reg_list, param_list=param_list)
        self.main_reg = reg_list[0]
        self.anc_reg = reg_list[1]
        self.kappa = param_list[0]
        self.epsilon = param_list[1]
        self.cheb_b = int(self.kappa * self.kappa * (math.log(self.kappa) - math.log(self.epsilon)))
        self.j0 = int(math.sqrt(self.cheb_b * (math.log(4 * self.cheb_b) - math.log(self.epsilon))))
        # Complex implementation with loops/conditionals
        self._impl_structure = [{"_type": "op", "op": "Hadamard", "qregs": ["anc_reg"]}, {"_type": "op", "op": "Hadamard", "qregs": ["main_reg"]}, {"_type": "comment", "text": "Chebyshev-weighted quantum walk iterations"}]
        self._build_execute_method()

    def _build_execute_method(self):
        # Build program_list by expanding loops and conditionals
        self.program_list = []
        self.program_list.append(OperationRegistry.get_class("Hadamard")(reg_list=[self.anc_reg]))
        self.program_list.append(OperationRegistry.get_class("Hadamard")(reg_list=[self.main_reg]))
        for i in range(5):
                self.program_list.append(OperationRegistry.get_class("Hadamard")(reg_list=[self.anc_reg]))
                self.program_list.append(OperationRegistry.get_class("Reflection_Bool")(reg_list=[self.anc_reg], param_list=[True]))
        self.declare_program_list()