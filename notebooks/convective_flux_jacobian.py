import numpy as np
from pyqres import *
from pyqres.primitives import SplitRegister, X, Ry, Hadamard
from sympy import *


class QRAM_Prerotate(AbstractComposite):
    def __init__(self, reg_list, param_list):
        temp_reg_list = [("Y", 1), ("tmp_ctrl", 1)]
        super().__init__(reg_list=reg_list, param_list=param_list, temp_reg_list=temp_reg_list)
        self.reg_addr = reg_list[0]
        self.reg_data = reg_list[1]
        self.n = reg_sz(self.reg_addr)
        self.N = 2 ** self.n
        self.epsilon = param_list[0]
        self.program_list = [
            X(["tmp_ctrl"]),
            Ry(["Y"], [0, self.epsilon]),
            X(["tmp_ctrl"]),
        ]

    def traverse_children(self, visitor, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = controllers_ctx or {}
        dagger_ctx = self.dagger_flag ^ dagger_ctx
        controllers_ctx = merge_controllers(controllers_ctx, self.controllers)
        ncontrols = get_control_qubit_count(controllers_ctx)
        if ncontrols == 0:
            raise NotImplementedError("T-count of QRAM_Prerotate is not implemented for ncontrols=0")
        elif ncontrols == 1:
            self.program_list[1].traverse(visitor, dagger_ctx=dagger_ctx, controllers_ctx={})
        else:
            self.program_list[0].traverse(visitor, dagger_ctx=dagger_ctx, controllers_ctx=controllers_ctx)
            self.program_list[1].traverse(visitor, dagger_ctx=dagger_ctx, controllers_ctx={})
            self.program_list[2].traverse(visitor, dagger_ctx=dagger_ctx, controllers_ctx=controllers_ctx)

    def sum_t_count(self, t_count_list):
        if len(t_count_list) == 1:
            t_count_ry = t_count_list[0]
            Toffoli_t_count = 0
        else:
            t_count_ry = t_count_list[1]
            Toffoli_t_count = t_count_list[0] + t_count_list[2]

        QRAM_t_count = (5 * t_count_ry + 23) * self.N - 5 * t_count_ry - 16 * (self.n + 2) + 5
        return QRAM_t_count + Toffoli_t_count


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

class ModularAdder(Primitive):
    def __init__(self, reg_list):
        super().__init__(reg_list)
        self.from_reg = reg_list[0]
        self.to_reg = reg_list[1]

    def t_count(self, dagger_ctx=False, controllers_ctx={}) -> int:       
        ncontrols = get_control_qubit_count(merge_controllers(self.controllers, controllers_ctx))
        if reg_sz(self.from_reg) == reg_sz(self.to_reg) and reg_sz(self.from_reg) == 2:
            return 6 * mcx_t_count(ncontrols + 2)
        else:
            raise NotImplementedError("Only reg_sz=2 is implemented.")


class TypeA(Composite):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list, param_list)
        self.block_diffusion = reg_list[0]
        self.block_index = reg_list[1]
        self.boundary_flag = reg_list[2]
        self.element_index = reg_list[3]
        self.element_diffusion = reg_list[4]
        self.group_flag = reg_list[5]
        self.data = reg_list[6]
        self.data_ratio = reg_list[7]

        self.nx = param_list[0]
        self.ny = param_list[1]
        self.eps_1 = param_list[2]
        self.eps_2 = param_list[3]

        self.program_list = list()

        for op in ["F+", "F-", "G+", "G-"]:
            for i in range(2):
                self.program_list.append(
                    Ry([self.data], [0, self.eps_1]).control_by_value([(self.block_diffusion, 0)])
                                                    .control_by_all_ones([self.boundary_flag])
                                                    .control_by_value([(self.element_index, 0)])
                                                    .control_by_value([(self.element_diffusion, 0)])
            )
        self.declare_program_list()

class TypeB(Composite):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list, param_list)
        self.block_diffusion = reg_list[0]
        self.block_index = reg_list[1]
        self.boundary_flag = reg_list[2]
        self.element_index = reg_list[3]
        self.element_diffusion = reg_list[4]
        self.group_flag = reg_list[5]
        self.data = reg_list[6]
        self.data_ratio = reg_list[7]

        self.nx = param_list[0]
        self.ny = param_list[1]
        self.eps_1 = param_list[2]
        self.eps_2 = param_list[3]

        self.program_list = list()
        
        # type b           
        for i in range(10):
            self.program_list.append(
                X([self.group_flag], [0]).control_by_value([(self.block_diffusion, 0)])
                                                .control_by_all_ones([self.boundary_flag])
                                                .control_by_value([(self.element_index, 0)])
                                                .control_by_value([(self.element_diffusion, 0)]))
            
            
        for i in range(1):
            self.program_list.append(
                QRAM_Prerotate([self.block_index, self.data], [self.eps_2]).control_by_bit([(self.group_flag, i)]))
            
        for i in range(8):
            self.program_list.append(
                Ry([self.data_ratio], [0, self.eps_1]).control_by_value([(self.block_diffusion, 0)])
                                                .control_by_all_ones([self.boundary_flag])
                                                .control_by_value([(self.element_index, 0)])
                                                .control_by_value([(self.element_diffusion, 0)]))

        for i in range(10):
            self.program_list.append(
                X([self.group_flag], [0]).control_by_value([(self.block_diffusion, 0)])
                                                .control_by_all_ones([self.boundary_flag])
                                                .control_by_value([(self.element_index, 0)])
                                                .control_by_value([(self.element_diffusion, 0)]))

        self.declare_program_list()

class TypeC(Composite):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list, param_list)
        self.block_diffusion = reg_list[0]
        self.block_index = reg_list[1]
        self.boundary_flag = reg_list[2]
        self.element_index = reg_list[3]
        self.element_diffusion = reg_list[4]
        self.group_flag = reg_list[5]
        self.data = reg_list[6]
        self.data_ratio = reg_list[7]

        self.nx = param_list[0]
        self.ny = param_list[1]
        self.eps_1 = param_list[2]
        self.eps_2 = param_list[3]

        self.program_list = list()
        
        # type b           
        for i in range(10):
            self.program_list.append(
                X([self.group_flag], [1]).control_by_value([(self.block_diffusion, 0)])
                                                .control_by_all_ones([self.boundary_flag])
                                                .control_by_value([(self.element_index, 0)])
                                                .control_by_value([(self.element_diffusion, 0)]))
            
            
        for i in range(1):
            self.program_list.append(
                QRAM_Prerotate([self.block_index, self.data], [self.eps_2]).control_by_bit([(self.group_flag, i)]))
            
        for i in range(8):
            self.program_list.append(
                Ry([self.data_ratio], [0, self.eps_1]).control_by_value([(self.block_diffusion, 0)])
                                                .control_by_all_ones([self.boundary_flag])
                                                .control_by_value([(self.element_index, 0)])
                                                .control_by_value([(self.element_diffusion, 0)]))

        for i in range(10):
            self.program_list.append(
                X([self.group_flag], [1]).control_by_value([(self.block_diffusion, 0)])
                                                .control_by_all_ones([self.boundary_flag])
                                                .control_by_value([(self.element_index, 0)])
                                                .control_by_value([(self.element_diffusion, 0)]))

        self.declare_program_list()

class TypeD(Composite):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list, param_list)
        self.block_diffusion = reg_list[0]
        self.block_index = reg_list[1]
        self.boundary_flag = reg_list[2]
        self.element_index = reg_list[3]
        self.element_diffusion = reg_list[4]
        self.group_flag = reg_list[5]
        self.data = reg_list[6]
        self.data_ratio = reg_list[7]

        self.nx = param_list[0]
        self.ny = param_list[1]
        self.eps_1 = param_list[2]
        self.eps_2 = param_list[3]

        self.program_list = list()
        
        # type D           
        for i in range(8):
            self.program_list.append(
                X([self.group_flag], [2]).control_by_value([(self.block_diffusion, 0)])
                                                .control_by_all_ones([self.boundary_flag])
                                                .control_by_value([(self.element_index, 0)])
                                                .control_by_value([(self.element_diffusion, 0)]))
            
            
        for i in range(1):
            self.program_list.append(
                QRAM_Prerotate([self.block_index, self.data], [self.eps_2]).control_by_bit([(self.group_flag, i)]))
            
        for i in range(6):
            self.program_list.append(
                Ry([self.data_ratio], [0, self.eps_1]).control_by_value([(self.block_diffusion, 0)])
                                                .control_by_all_ones([self.boundary_flag])
                                                .control_by_value([(self.element_index, 0)])
                                                .control_by_value([(self.element_diffusion, 0)]))

        for i in range(8):
            self.program_list.append(
                X([self.group_flag], [2]).control_by_value([(self.block_diffusion, 0)])
                                                .control_by_all_ones([self.boundary_flag])
                                                .control_by_value([(self.element_index, 0)])
                                                .control_by_value([(self.element_diffusion, 0)]))

        self.declare_program_list()


class TypeE(Composite):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list, param_list)
        self.block_diffusion = reg_list[0]
        self.block_index = reg_list[1]
        self.boundary_flag = reg_list[2]
        self.element_index = reg_list[3]
        self.element_diffusion = reg_list[4]
        self.group_flag = reg_list[5]
        self.data = reg_list[6]
        self.data_ratio = reg_list[7]

        self.nx = param_list[0]
        self.ny = param_list[1]
        self.eps_1 = param_list[2]
        self.eps_2 = param_list[3]

        self.program_list = list()
                                              
        for op in ["F+", "F-", "G+", "G-"]:
            self.program_list.append(
                QRAM_Prerotate([self.block_index, self.data], [self.eps_2]).control_by_value([(self.block_diffusion, 0)])
                                                .control_by_all_ones([self.boundary_flag])
                                                .control_by_value([(self.element_index, 0)])
                                                .control_by_value([(self.element_diffusion, 0)]),
            )

        self.declare_program_list()
            
class TypeF(Composite):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list, param_list)
        self.block_diffusion = reg_list[0]
        self.block_index = reg_list[1]
        self.boundary_flag = reg_list[2]
        self.element_index = reg_list[3]
        self.element_diffusion = reg_list[4]
        self.group_flag = reg_list[5]
        self.data = reg_list[6]
        self.data_ratio = reg_list[7]

        self.nx = param_list[0]
        self.ny = param_list[1]
        self.eps_1 = param_list[2]
        self.eps_2 = param_list[3]

        self.program_list = list()
                                              
        for op in ["F+", "F-", "G+", "G-"]:
            self.program_list.append(
                QRAM_Prerotate([self.block_index, self.data], [self.eps_2]).control_by_value([(self.block_diffusion, 0)])
                                                .control_by_all_ones([self.boundary_flag])
                                                .control_by_value([(self.element_index, 0)])
                                                .control_by_value([(self.element_diffusion, 0)]),
            )

        self.declare_program_list()

class TypeG(Composite):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list, param_list)
        self.block_diffusion = reg_list[0]
        self.block_index = reg_list[1]
        self.boundary_flag = reg_list[2]
        self.element_index = reg_list[3]
        self.element_diffusion = reg_list[4]
        self.group_flag = reg_list[5]
        self.data = reg_list[6]
        self.data_ratio = reg_list[7]

        self.nx = param_list[0]
        self.ny = param_list[1]
        self.eps_1 = param_list[2]
        self.eps_2 = param_list[3]

        self.program_list = list()
                                              
        for op in ["F+", "F-", "G+", "G-"]:
            self.program_list.append(
                QRAM_Prerotate([self.block_index, self.data], [self.eps_2]).control_by_value([(self.block_diffusion, 0)])
                                                .control_by_all_ones([self.boundary_flag])
                                                .control_by_value([(self.element_index, 0)])
                                                .control_by_value([(self.element_diffusion, 0)]),
            )

        self.declare_program_list()
            
class TypeH(Composite):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list, param_list)
        self.block_diffusion = reg_list[0]
        self.block_index = reg_list[1]
        self.boundary_flag = reg_list[2]
        self.element_index = reg_list[3]
        self.element_diffusion = reg_list[4]
        self.group_flag = reg_list[5]
        self.data = reg_list[6]
        self.data_ratio = reg_list[7]

        self.nx = param_list[0]
        self.ny = param_list[1]
        self.eps_1 = param_list[2]
        self.eps_2 = param_list[3]

        self.program_list = list()
                                              
        for op in ["F+", "F-", "G+", "G-"]:
            self.program_list.append(
                QRAM_Prerotate([self.block_index, self.data], [self.eps_2]).control_by_value([(self.block_diffusion, 0)])
                                                .control_by_all_ones([self.boundary_flag])
                                                .control_by_value([(self.element_index, 0)])
                                                .control_by_value([(self.element_diffusion, 0)]),
            )

        self.declare_program_list()
            
class TypeI(Composite):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list, param_list)
        self.block_diffusion = reg_list[0]
        self.block_index = reg_list[1]
        self.boundary_flag = reg_list[2]
        self.element_index = reg_list[3]
        self.element_diffusion = reg_list[4]
        self.group_flag = reg_list[5]
        self.data = reg_list[6]
        self.data_ratio = reg_list[7]

        self.nx = param_list[0]
        self.ny = param_list[1]
        self.eps_1 = param_list[2]
        self.eps_2 = param_list[3]

        self.program_list = list()
                                              
        for op in ["F+", "F-", "G+", "G-"]:
            self.program_list.append(
                QRAM_Prerotate([self.block_index, self.data], [self.eps_2]).control_by_value([(self.block_diffusion, 0)])
                                                .control_by_all_ones([self.boundary_flag])
                                                .control_by_value([(self.element_index, 0)])
                                                .control_by_value([(self.element_diffusion, 0)]),
            )

        self.declare_program_list()

class TypeJ(Composite):
    def __init__(self, reg_list, param_list):
        super().__init__(reg_list, param_list)
        self.block_diffusion = reg_list[0]
        self.block_index = reg_list[1]
        self.boundary_flag = reg_list[2]
        self.element_index = reg_list[3]
        self.element_diffusion = reg_list[4]
        self.group_flag = reg_list[5]
        self.data = reg_list[6]
        self.data_ratio = reg_list[7]

        self.nx = param_list[0]
        self.ny = param_list[1]
        self.eps_1 = param_list[2]
        self.eps_2 = param_list[3]

        self.program_list = list()
                                              
        for op in ["F+", "F-", "G+", "G-"]:
            self.program_list.append(
                QRAM_Prerotate([self.block_index, self.data], [self.eps_2]).control_by_value([(self.block_diffusion, 0)])
                                                .control_by_all_ones([self.boundary_flag])
                                                .control_by_value([(self.element_index, 0)])
                                                .control_by_value([(self.element_diffusion, 0)]),
            )
        self.declare_program_list()

class ConvectiveFluxJacobian(Composite):
    def __init__(self, reg_list, param_list, **kwargs):
        super().__init__(reg_list, param_list)

        self.block_diffusion = reg_list[0]
        self.block_index = reg_list[1]
        self.boundary_flag = reg_list[2]
        self.element_index = reg_list[3]
        self.element_diffusion = reg_list[4]
        self.group_flag = reg_list[5]
        self.data = reg_list[6]
        self.data_ratio = reg_list[7]

        self.nx = param_list[0]
        self.ny = param_list[1]
        self.eps_1 = param_list[2]
        self.eps_2 = param_list[3]

        # self.aperiodic_boundary = kwargs.get("aperiodic_boundary", False)
        self.program_list = list()

        # Preparing boundary conditions
        self.program_list.append(Hadamard([self.block_diffusion]))
        self.program_list.append(Hadamard([self.element_diffusion]))

        self.program_list.append(BoundaryOperator(reg_list=[self.boundary_flag, self.block_index], param_list=[self.nx, self.ny]))

        self.program_list.append(
            LocationOperator([self.block_index, self.block_diffusion], param_list=[self.nx, self.ny])
        )

        # Data loading
        self.program_list.append(
            ModularAdder([self.element_diffusion, self.element_index])
        )

        # type a
        self.program_list.extend([
            TypeA(self.reg_list, self.param_list),
            TypeB(self.reg_list, self.param_list),
            TypeC(self.reg_list, self.param_list),
            TypeD(self.reg_list, self.param_list),
            TypeE(self.reg_list, self.param_list),
            TypeF(self.reg_list, self.param_list),
            TypeG(self.reg_list, self.param_list),
            TypeE(self.reg_list, self.param_list).dagger(),
            TypeF(self.reg_list, self.param_list).dagger(),
            TypeG(self.reg_list, self.param_list).dagger(),
            TypeH(self.reg_list, self.param_list),
            TypeI(self.reg_list, self.param_list),
            TypeJ(self.reg_list, self.param_list),
            TypeH(self.reg_list, self.param_list).dagger(),
            TypeI(self.reg_list, self.param_list).dagger(),
            TypeJ(self.reg_list, self.param_list).dagger(),
        ]) 

        self.program_list.append(
            Swap([self.element_index, self.element_diffusion])
        )

        self.program_list.append(
            ModularAdder([self.element_diffusion, self.element_index]).dagger()
        )
        self.program_list.append(BoundaryOperator(reg_list=[self.boundary_flag, self.block_index], param_list=[self.nx, self.ny]).dagger())
        self.program_list.append(Hadamard([self.block_diffusion]))
        self.program_list.append(Hadamard([self.element_diffusion]))

        self.declare_program_list()
        
    def sum_t_count(self, t_count_list):
        for t in t_count_list:
            print(t)
        return sum(t_count_list)
    

if __name__ == '__main__':
    nx = Symbol('nx')
    n = Symbol('n')
    ny = n - nx
    
    RegisterMetadata.add_registers(
        [
            ('block_diffusion', 2),
            ('block_index', n),
            ('boundary_flag', 4),
            ('element_index', 2),
            ('element_diffusion', 2),
            ('group_flag', 3),
            ('data', 1),
            ('data_ratio', 1),
        ]
    )

    eps_3 = Symbol('epsilon_3')
    eps_4 = Symbol('epsilon_4')

    prog = ConvectiveFluxJacobian(
        reg_list=[
            'block_diffusion',
            'block_index',
            'boundary_flag',
            'element_index',
            'element_diffusion',
            'group_flag',
            'data',
            'data_ratio',
        ],
        param_list=[nx, ny, eps_3, eps_4],
    )
    
    t_counter = TCounter()
    prog.traverse(t_counter)
    print(t_counter.get_count())
    print(expand(t_counter.get_count()))
    
    path = Path('convective_flux_jacobian')
    
    with open(path / 'DSL.txt', 'w') as fp:
        print(program_metadata, file=fp)

    program_metadata.quantikz('convective_flux_jacobian')