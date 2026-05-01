# Generated from YAML definition

from ..core.operation import AbstractComposite
from ..core.registry import OperationRegistry
from ..core.utils import merge_controllers
import math

class QuantumWalkStep(AbstractComposite):
    """One CKS quantum walk half-step: T† · PhaseFlip · T · SWAPs"""
    def __init__(self, reg_list, param_list=None, temp_reg_list=[('b1', 1), ('b2', 1), ('j_comp', 10), ('k_comp', 10)]):
        if param_list is None:
            param_list = []
        AbstractComposite.__init__(self, reg_list=reg_list, param_list=param_list, temp_reg_list=temp_reg_list)
        self.main_reg = reg_list[0]
        self.anc_reg = reg_list[1]
        self.n_qubits = param_list[0]
        # Store temp registers as instance attributes
        self._temp_reg_dict = {}
        self._temp_reg_dict['b1'] = ('b1', 1)
        self.b1 = 'b1'
        self._temp_reg_dict['b2'] = ('b2', 1)
        self.b2 = 'b2'
        self._temp_reg_dict['j_comp'] = ('j_comp', 10)
        self.j_comp = 'j_comp'
        self._temp_reg_dict['k_comp'] = ('k_comp', 10)
        self.k_comp = 'k_comp'
        # Complex implementation with loops/conditionals
        self._impl_structure = [{"_type": "op", "op": "Hadamard", "qregs": ["anc_reg"]}, {"_type": "comment", "text": "TOperator forward \u2014 requires QRAM + sparse matrix (Python submodule)"}, {"_type": "op", "op": "ZeroConditionalPhaseFlip", "qregs": ["anc_reg"]}, {"_type": "op", "op": "Swap_General_General", "qregs": ["main_reg", "anc_reg"]}, {"_type": "op", "op": "Swap_General_General", "qregs": ["b1", "b2"]}, {"_type": "op", "op": "Swap_General_General", "qregs": ["j_comp", "k_comp"]}, {"_type": "comment", "text": "TOperator dagger (reverse of forward \u2014 requires Python)"}, {"_type": "op", "op": "CheckNan", "qregs": []}]
        self._build_execute_method()

    def _build_execute_method(self):
        # Build program_list by expanding loops and conditionals
        self.program_list = []
        self.program_list.append(OperationRegistry.get_class("Hadamard")(reg_list=[self.anc_reg]))
        # TOperator forward: Hadamard(k) → QRAMLoad → SortExceptKey → CondRot → SortExceptKey → QRAMLoad(uncompute)
        # This requires the sparse matrix QRAM object, handled by the TOperator_Primitive Python submodule
        pass
        self.program_list.append(OperationRegistry.get_class("ZeroConditionalPhaseFlip")(reg_list=[self.anc_reg]))
        self.program_list.append(OperationRegistry.get_class("Swap_General_General")(reg_list=[self.main_reg, self.anc_reg]))
        self.program_list.append(OperationRegistry.get_class("Swap_General_General")(reg_list=[self.b1, self.b2]))
        self.program_list.append(OperationRegistry.get_class("Swap_General_General")(reg_list=[self.j_comp, self.k_comp]))
        # TOperator dagger: reverse column find → uncompute QRAMLoad → reverse → uncompute QRAMLoad → Hadamard(k)
        pass
        self.program_list.append(OperationRegistry.get_class("CheckNan")())
        self.declare_program_list()