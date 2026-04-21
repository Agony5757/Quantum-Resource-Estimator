import sympy as sp
import numpy as np

from ..core.operation import AbstractComposite


class LinearSolver(AbstractComposite):
    def __init__(self, reg_list, param_list, submodules):
        super().__init__(reg_list=reg_list, param_list=param_list, submodules=submodules)
        self.reg_ancilla = reg_list[0]
        self.reg_b = reg_list[1]
        self.kappa = param_list[0]
        self.epsilon = param_list[1]
        encode_A = submodules[0]
        encode_b = submodules[1]
        self.program_list = [
            encode_A(reg_list=[self.reg_ancilla, self.reg_b],
                     param_list=[self.kappa, self.epsilon]),
            encode_b(reg_list=[self.reg_ancilla, self.reg_b],
                     param_list=[self.epsilon])
        ]
        self.declare_program_list()

    def sum_t_count(self, t_count_list):
        t_count_A = t_count_list[0]
        t_count_b = t_count_list[1]
        kappa, epsilon = self.kappa, self.epsilon
        Q = (56 * kappa +
             1.05 * kappa * sp.log(sp.sqrt(1 - epsilon**2) / epsilon) +
             2.78 * (sp.ceiling(np.log(kappa))**3) +
             3.17)
        return (t_count_A + t_count_b * 2) * Q
