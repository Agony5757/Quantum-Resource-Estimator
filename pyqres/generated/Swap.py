# Generated from YAML definition

from ..core.operation import StandardComposite
from ..core.registry import OperationRegistry
from ..core.utils import merge_controllers
import math

class Swap(StandardComposite):
    __self_conjugate__ = True
    """Swap two registers via 3 CNOTs"""
    def __init__(self, reg_list, operations=None):
        StandardComposite.__init__(self, reg_list=reg_list, operations=operations)
        self.reg1 = reg_list[0]
        self.reg2 = reg_list[1]
        self.program_list = [
            OperationRegistry.get_class("CNOT")(reg_list=[self.reg1, self.reg2]),
            OperationRegistry.get_class("CNOT")(reg_list=[self.reg2, self.reg1]),
            OperationRegistry.get_class("CNOT")(reg_list=[self.reg1, self.reg2]),
        ]
        self.declare_program_list()
    def traverse_children(self, visitor, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = controllers_ctx or {}
        controllers = merge_controllers(self.controllers, controllers_ctx)
        self.program_list[0].traverse(visitor, False, {})
        self.program_list[1].traverse(visitor, False, controllers)
        self.program_list[2].traverse(visitor, False, {})