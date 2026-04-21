# %%
import pysparq
from pyqres import *
from pyqres.primitives import SplitRegister, X, Rot_GeneralStatePrep as Rot_GeneralStatePrepOp


# Stage 1. define block_encoding tridiagonal
class BlockEncodingTridiagonal(Composite):
    def __init__(self, reg_list, param_list, temp_reg_list=[("overflow", 0),
                                                            ("other", 0)]):
        super().__init__(reg_list=reg_list, param_list=param_list, temp_reg_list=temp_reg_list)
        self.main_reg = reg_list[0]
        self.anc_UA = reg_list[1]
        self.alpha = param_list[0]
        self.beta = param_list[1]        

        self.n = 2 ** reg_sz(self.main_reg)
        self.sum = self.n * self.alpha * self.alpha + 2 * (self.n - 1) * self.beta * self.beta
        self.norm_F = sp.sqrt(self.sum)
        self.prep_state = [sp.sqrt(self.alpha / self.norm_F),
                           sp.sqrt(self.beta / self.norm_F),
                           sp.sqrt(self.beta / self.norm_F),
                           sp.sqrt(1 - (self.alpha + 2 * self.beta) / self.norm_F)]

        self.program_list = [
            SplitRegister([self.anc_UA, "overflow", "other"], [1, 1]),
            Rot_GeneralStatePrepOp([self.anc_UA], self.prep_state),

            X(["other"], [0]).control_by_all_ones([self.anc_UA]),

            Rot_GeneralStatePrepOp([self.anc_UA], self.prep_state).dagger(),
            SplitRegister([self.anc_UA, "overflow", "other"], [1, 1]).dagger(),
        ]
        self.declare_program_list()
    


n = Symbol("n")
alpha = Symbol("alpha")
beta = Symbol("beta")

n = 3
alpha = 0.5
beta = 0.25

# Declare registers
RegisterMetadata.add_registers([
    ("anc_UA", 4),
    ("main_reg", n),
])

prog = BlockEncodingTridiagonal(["main_reg", "anc_UA"], [alpha, beta])

print(program_metadata)

# exit(0)

simulator = SimulatorVisitor()
prog.traverse(simulator)
simulator.print_state()
