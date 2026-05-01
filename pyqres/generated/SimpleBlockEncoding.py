# Generated from YAML definition

from ..core.operation import AbstractComposite
from ..core.registry import OperationRegistry
from ..core.utils import merge_controllers
import math

class SimpleBlockEncoding(AbstractComposite):
    """Minimal block encoding placeholder for basic resource estimation"""
    def __init__(self, reg_list, param_list=None, operations=None):
        if param_list is None:
            param_list = []
        AbstractComposite.__init__(self, reg_list=reg_list, param_list=param_list, operations=operations)
        self.main_reg = reg_list[0]
        self.anc_reg = reg_list[1]
        self.alpha = param_list[0]
        self.beta = param_list[1]
        self.program_list = [
            OperationRegistry.get_class("Hadamard")(reg_list=[self.anc_reg]),
            OperationRegistry.get_class("Reflection_Bool")(reg_list=[self.anc_reg], param_list=[True]),
        ]
        self.declare_program_list()