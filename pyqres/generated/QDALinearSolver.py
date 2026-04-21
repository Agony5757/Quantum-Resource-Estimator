# Generated from YAML definition

from ..core.operation import AbstractComposite
from ..core.registry import OperationRegistry
from ..core.utils import merge_controllers
import math

class QDALinearSolver(AbstractComposite):
    """QDA quantum linear system solver using discrete adiabatic evolution"""
    def __init__(self, reg_list, param_list=None):
        if param_list is None:
            param_list = []
        AbstractComposite.__init__(self, reg_list=reg_list, param_list=param_list)
        self.main_reg = reg_list[0]
        self.anc_UA = reg_list[1]
        self.anc_1 = reg_list[2]
        self.anc_2 = reg_list[3]
        self.anc_3 = reg_list[4]
        self.anc_4 = reg_list[5]
        self.kappa = param_list[0]
        self.epsilon = param_list[1]
        self.adiab_steps = int(self.kappa + 1)
        # Complex implementation with loops/conditionals
        self._impl_structure = [{"_type": "op", "op": "X", "qregs": ["main_reg"], "params": [0]}, {"_type": "comment", "text": "Discrete adiabatic evolution with WalkS"}, {"_type": "op", "op": "X", "qregs": ["anc_1"], "params": [0]}]
        self._build_execute_method()

    def _build_execute_method(self):
        # Build program_list by expanding loops and conditionals
        self.program_list = []
        self.program_list.append(OperationRegistry.get_class("X")(reg_list=[self.main_reg], param_list=[0]))
        for i in range(self.adiab_steps):
                self.program_list.append(OperationRegistry.get_class("Hadamard")(reg_list=[self.anc_3]))
                self.program_list.append(OperationRegistry.get_class("Reflection_Bool")(reg_list=[self.anc_2], param_list=[False]))
        self.program_list.append(OperationRegistry.get_class("X")(reg_list=[self.anc_1], param_list=[0]))
        self.declare_program_list()