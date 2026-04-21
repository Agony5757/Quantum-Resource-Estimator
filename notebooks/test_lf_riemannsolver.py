# %%
import numpy as np
from pyqres import *
from pyqres.primitives import SplitRegister, X, Ry
from sympy import *


class P_L(AbstractComposite):
    """P_L操作节点类"""
    def __init__(self, reg_list, param_list, temp_reg_list=[("_tmp_ry", 1)]):
        super().__init__(reg_list=reg_list, param_list=param_list, temp_reg_list=temp_reg_list)
        self.reg_spp = reg_list[0]
        self.eps_1 = param_list[0]
        self.program_list = [
            Ry(reg_list=["_tmp_ry"], param_list=[0, self.eps_1]),
        ]
        self.declare_program_list()

    def sum_t_count(self, t_count_list):
        t_count_ry = t_count_list[0]
        return 2 * t_count_ry + 40


class LocationOperatorDirection(Primitive):
    def __init__(self, reg_list):
        super().__init__(reg_list)
        self.block_index_x = reg_list[0]

    def t_count(self, dagger_ctx=False, controllers_ctx={}):
        ncontrols = get_control_qubit_count(merge_controllers(self.controllers, controllers_ctx))
        return mcx_t_count(ncontrols + 1) * (reg_sz(self.block_index_x) - 1)


class LocationOperator(Composite):
    def __init__(self, reg_list, param_list, temp_reg_list = [('temp_BI_x', 0), 
                                                              ('temp_BI_y', 0)]):
        super().__init__(reg_list, param_list, temp_reg_list)
        self.block_index = reg_list[0]
        self.block_diffusion = reg_list[1]
        self.n = reg_sz(self.block_index)        
        self.nx = param_list[0]
        self.ny = param_list[1]
        
        # assert self.n == self.nx + self.ny, "Block size must be equal to nx + ny"

        self.program_list = [
            SplitRegister([self.block_index, 'temp_BI_x', 'temp_BI_y'], [self.nx, self.ny]),
            LocationOperatorDirection(['temp_BI_x']).control_by_value((self.block_diffusion, 0)),
            LocationOperatorDirection(['temp_BI_x']).control_by_value((self.block_diffusion, 1)).dagger(),
            LocationOperatorDirection(['temp_BI_y']).control_by_value((self.block_diffusion, 2)),
            LocationOperatorDirection(['temp_BI_y']).control_by_value((self.block_diffusion, 3)).dagger(),
            SplitRegister([self.block_index, 'temp_BI_x', 'temp_BI_y'], [self.nx, self.ny]).dagger(),
        ]   

        self.declare_program_list()

class BoundaryOperator(Composite):
    def __init__(self, reg_list, param_list, temp_reg_list = [('temp_BF_U', 0), 
                                                              ('temp_BF_D', 0), 
                                                              ('temp_BF_L', 0), 
                                                              ('temp_BF_R', 0), 
                                                              ('temp_BI_x', 0), 
                                                              ('temp_BI_y', 0)], **kwargs):
        super().__init__(reg_list, param_list, temp_reg_list)
        
        self.boundary_flag = reg_list[0]
        self.block_index = reg_list[1]
        self.n = reg_sz(self.block_index)
        self.nx = param_list[0]
        self.ny = param_list[1]
        
        # assert reg_sz(self.boundary_flag) == 4
        # assert self.n == self.nx + self.ny, "Block size must be equal to nx + ny"

        self.program_list = [
            SplitRegister([self.block_index, 'temp_BF_U', 'temp_BF_D', 'temp_BF_L', 'temp_BF_R'], [1, 1, 1, 1]),
            SplitRegister([self.block_index, 'temp_BI_x', 'temp_BI_y'], [self.nx, self.ny]),

            X(['temp_BI_x']),
            X(['temp_BF_U']).control_by_all_ones(['temp_BI_x']), # zero control
            X(['temp_BI_x']),

            X(['temp_BF_D']).control_by_all_ones(['temp_BI_x']),

            X(['temp_BI_y']),
            X(['temp_BF_L']).control_by_all_ones(['temp_BI_y']), # zero control
            X(['temp_BI_y']),

            X(['temp_BF_R']).control_by_all_ones(['temp_BI_y']),

            SplitRegister([self.block_index, 'temp_BF_U', 'temp_BF_D', 'temp_BF_L', 'temp_BF_R'], [1, 1, 1, 1]).dagger(),
            SplitRegister([self.block_index, 'temp_BI_x', 'temp_BI_y'], [self.nx, self.ny]).dagger(),
        ]

        self.declare_program_list()

class LF_RiemannSolver(Composite):
    """LF-Riemann Solver操作节点类"""
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list=reg_list, param_list=param_list)
        self.reg_SPP = reg_list[0]
        self.reg_BI = reg_list[1]
        self.reg_BF = reg_list[2]

        self.eps_1 = param_list[0]
        self.eps_2 = param_list[1]

        self.program_list = [
            P_L(reg_list=[self.reg_SPP], param_list=[self.eps_1]),
        ]
        self.program_list.extend([
            BoundaryOperator(reg_list=[self.reg_BI, self.reg_BF], param_list=[direction]) for direction in ['L','R','U','D']
        ])
        self.program_list.extend([
            QRAM(reg_list=[self.reg_BI], param_list=[self.eps_2, 'F'], submodules=[QRAM_Prerotate]),
            QRAM(reg_list=[self.reg_BI], param_list=[self.eps_2, 'W'], submodules=[QRAM_Prerotate])
        ])

        self.program_list.extend([
            LocationOperator(reg_list=[self.reg_BI], param_list=[direction]).control(self.reg_SPP) for direction in ['L','R','U','D']
        ])
        self.program_list.extend([
            P_L(reg_list=[self.reg_SPP], param_list=[self.eps_1]).dagger(),
        ])
        self.declare_program_list()


class Prog2(Composite):
    def __init__(self, reg_list):
        super().__init__(reg_list=reg_list)
        self.q0 = reg_list[0]
        self.q1 = reg_list[1]
        self.q2 = reg_list[2]
        self.program_list = [
            Swap([self.q0, self.q1]).control(self.q2)
        ]
        self.declare_program_list()


RegisterMetadata.add_registers(
    [("SPP", 4),
    ("BI", Symbol("n")),
    ("BF", 4)]
)

regs = [("SPP"), ("BI"), ("BF")]
params = [Symbol("epsilon_1"), Symbol("epsilon_2")]

prog = LF_RiemannSolver(reg_list=regs, param_list=params)

t_counter = TCounter()
prog.traverse(t_counter)
print(t_counter.get_count())
expand(t_counter.get_count())

# %%
print(program_metadata)