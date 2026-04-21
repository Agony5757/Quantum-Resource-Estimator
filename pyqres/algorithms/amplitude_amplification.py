import sympy as sp

from ..core.operation import AbstractComposite


class AmplitudeAmplification(AbstractComposite):
    def __init__(self, reg_list, param_list, submodules):
        super().__init__(reg_list=reg_list, param_list=param_list, submodules=submodules)
        self.amp_times = param_list[0]
        self.other_params = param_list[1:]
        module = submodules[0]
        self.program_list = [
            module(reg_list=reg_list, param_list=self.other_params)
        ]
        self.declare_program_list()

    def sum_t_count(self, t_count_list):
        t_count_single = sum(t_count_list)
        return t_count_single * self.amp_times
