# Generated from YAML definition

from ..core.operation import AbstractComposite
from ..core.registry import OperationRegistry
from ..core.utils import merge_controllers
import math
from ..algorithms.cks_solver import ChebyshevPolynomialCoefficient

class CKSLinearSolver(AbstractComposite):
    """CKS quantum linear system solver using Chebyshev polynomial filtering"""
    def __init__(self, reg_list, param_list=None, temp_reg_list=[('b1', 1), ('b2', 1)], operations=None):
        if param_list is None:
            param_list = []
        AbstractComposite.__init__(self, reg_list=reg_list, param_list=param_list, temp_reg_list=temp_reg_list, operations=operations)
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
        if operations is None:
            operations = []
        self.encode_A = operations[0] if 0 < len(operations) else None
        self.encode_b = operations[1] if 1 < len(operations) else None
        # Complex implementation with loops/conditionals
        self._impl_structure = [{"_type": "comment", "text": "Block encoding of A \u2014 via encode_A (operation param)"}, {"_type": "comment", "text": "State preparation of |b\u27e9 \u2014 via encode_b (operation param)"}, {"_type": "comment", "text": "Chebyshev iteration: for j in range(j0+1)"}]
        self._build_execute_method()

    def _build_execute_method(self):
        # Build program_list by expanding loops and conditionals
        self.program_list = []
        if self.encode_A:
            self.program_list.append(self.encode_A)
        if self.encode_b:
            self.program_list.append(self.encode_b)
        from ..algorithms.cks_solver import ChebyshevPolynomialCoefficient
        cheb = ChebyshevPolynomialCoefficient(b=int(self.cheb_b))
        for j in range(self.j0 + 1):
            self.program_list.append(
                OperationRegistry.get_class("Hadamard")(
                    reg_list=[self.anc_reg], param_list=[]))
            for _ in range(cheb.step(j)):
                self.program_list.append(
                    OperationRegistry.get_class("ZeroConditionalPhaseFlip")(
                        reg_list=[self.anc_reg], param_list=[]))
                if self.encode_A:
                    self.program_list.append(self.encode_A)
                self.program_list.append(
                    OperationRegistry.get_class("Swap_General_General")(
                        reg_list=[self.main_reg, self.anc_reg], param_list=[]))
                if self.encode_A:
                    self.program_list.append(self.encode_A.dagger())
        self.declare_program_list()