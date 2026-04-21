import sympy as sp

from ..core.operation import AbstractComposite


class Tomography(AbstractComposite):
    def __init__(self, reg_list, param_list, submodules):
        super().__init__(
            reg_list=reg_list,
            param_list=param_list,
            temp_reg_list=[('_tmp_tomography_1', 1)],
            submodules=submodules
        )
        self.regs = reg_list
        self.epsilon = param_list[0]
        self.other_params = param_list[1:]
        module = submodules[0]
        self.program_list = [
            module(reg_list=self.regs, param_list=self.other_params)
        ]
        self.declare_program_list()

    def traverse_children(self, visitor, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = controllers_ctx or {}
        self.program_list[0].traverse(visitor, False, {})
        self.program_list[0].traverse(visitor, False, ['_tmp_tomography_1'])

    def sum_t_count(self, t_count_list):
        t_count_no_control = t_count_list[0]
        t_count_with_control = t_count_list[1]
        t_count_single = t_count_no_control + t_count_with_control
        tomo_times = 36 / self.epsilon / self.epsilon
        return t_count_single * tomo_times
