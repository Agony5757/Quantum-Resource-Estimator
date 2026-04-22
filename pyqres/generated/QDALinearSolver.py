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
        self.kappa = param_list[0]
        self.epsilon = param_list[1]
        self.n_steps = int(math.ceil(math.log(self.kappa / self.epsilon)))
        self.program_list = [
            OperationRegistry.get_class("X")(reg_list=[self.main_reg], param_list=[0]),
        ]
        self.declare_program_list()