# Generated from YAML definition

from ..core.operation import AbstractComposite
from ..core.registry import OperationRegistry
from ..core.utils import merge_controllers
import math

class CKSLinearSolver(AbstractComposite):
    """CKS quantum linear system solver using Chebyshev polynomial filtering"""
    def __init__(self, reg_list, param_list=None, temp_reg_list=[('b1', 1), ('b2', 1)]):
        if param_list is None:
            param_list = []
        AbstractComposite.__init__(self, reg_list=reg_list, param_list=param_list, temp_reg_list=temp_reg_list)
        self.main_reg = reg_list[0]
        self.anc_reg = reg_list[1]
        self.kappa = param_list[0]
        self.epsilon = param_list[1]
        self.cheb_b = int((self.kappa * self.kappa) * (math.log(self.kappa) - math.log(self.epsilon)))
        self.j0 = int(math.sqrt((self.cheb_b) * (math.log(4 * self.cheb_b) - math.log(self.epsilon))))
        # Store temp registers as instance attributes
        self._temp_reg_dict = {}
        self._temp_reg_dict['b1'] = ('b1', 1)
        self.b1 = 'b1'
        self._temp_reg_dict['b2'] = ('b2', 1)
        self.b2 = 'b2'
        # Complex implementation with loops/conditionals
        self._impl_structure = [{"_type": "comment", "text": "Block encoding of A \u2014 via encode_A submodule (QRAM setup in Python)"}, {"_type": "comment", "text": "State preparation of |b\u27e9 \u2014 via encode_b submodule"}, {"_type": "comment", "text": "Chebyshev-filtered quantum walk iterations"}]
        self._build_execute_method()

    def _build_execute_method(self):
        # Build program_list by expanding loops and conditionals
        self.program_list = []
        # Python: self.encode_A is passed as a submodule
        # Program list entry created at construction time in _build_program_list
        pass
        # Python: self.encode_b is passed as a submodule
        pass
        for i in range(self.j0):
                self.program_list.append(OperationRegistry.get_class("Hadamard")(reg_list=[self.anc_reg]))
                for i in range(self.cheb_b):
                        self.program_list.append(OperationRegistry.get_class("ZeroConditionalPhaseFlip")(reg_list=[self.anc_reg]))
                        self.program_list.append(OperationRegistry.get_class("Swap_General_General")(reg_list=[self.main_reg, self.anc_reg]))
        self.declare_program_list()