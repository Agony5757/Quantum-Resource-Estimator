# %%
# CKS Linear Solver - direct PySparQ usage
# This notebook uses the raw pysparq API rather than the pyqres Operation framework.
# It serves as a reference implementation for comparison with pyqres-based algorithms.

import numpy as np
import pysparq


class Block_Encoding_Hs:
    """Block encoding of H_s = (1-f_s)|0><0| + f_s|1><1| using pysparq directly."""

    def __init__(self, enc_A, enc_b, main_reg, anc_UA, anc_1, anc_2, anc_3, anc_4, fs):
        self.fs = fs
        self.main_reg = main_reg
        self.anc_UA = anc_UA
        self.anc_1 = anc_1
        self.anc_2 = anc_2
        self.anc_3 = anc_3
        self.anc_4 = anc_4
        self.enc_A = enc_A
        self.enc_b = enc_b

        sqrt_N = 1.0 / np.sqrt((1 - fs)**2 + fs**2)
        u00 = sqrt_N * (1 - fs)
        u01 = sqrt_N * fs
        u10 = sqrt_N * fs
        u11 = sqrt_N * (fs - 1)
        self.R_s = np.array([[u00, u01], [u10, u11]])

        self.condition_variable_all_ones = []
        self.condition_variable_by_bit = []

    def __call__(self, state):
        flag = False
        unconditioned_state = []

        if not self.condition_variable_all_ones and not self.condition_variable_by_bit:
            flag = True
        else:
            splitter = pysparq.SplitSystems()
            splitter.conditioned_by_all_ones(self.condition_variable_all_ones)
            splitter.conditioned_by_bit(self.condition_variable_by_bit)
            unconditioned_state = splitter(state)
            if state:
                flag = True

        if flag and state:
            pysparq.Hadamard_Bool(self.anc_3)(state)

            ref_conds = [self.anc_1, self.anc_3, self.anc_4]
            self.enc_b.dag(state)
            pysparq.Xgate_Bool(self.anc_1, 0)(state)
            pysparq.Reflection_Bool(self.main_reg, True).conditioned_by_all_ones(ref_conds)(state)
            pysparq.Xgate_Bool(self.anc_1, 0)(state)
            self.enc_b(state)

            pysparq.Xgate_Bool(self.anc_4, 0)(state)
            pysparq.Rot_Bool(self.anc_2, self.R_s).conditioned_by_all_ones([self.anc_4])(state)
            pysparq.Xgate_Bool(self.anc_4, 0)(state)
            pysparq.Hadamard_Bool(self.anc_2).conditioned_by_all_ones([self.anc_4])(state)

            self.enc_A.conditioned_by_all_ones([self.anc_1, self.anc_2])
            self.enc_A(state)

            pysparq.Xgate_Bool(self.anc_1, 0).conditioned_by_all_ones([self.anc_2])(state)
            pysparq.Reflection_Bool(self.anc_2, True).conditioned_by_all_ones([self.anc_1])(state)

            self.enc_A.dag(state)

            pysparq.Xgate_Bool(self.anc_4, 0)(state)
            pysparq.Hadamard_Bool(self.anc_2).conditioned_by_all_ones([self.anc_4])(state)
            pysparq.Xgate_Bool(self.anc_4, 0)(state)
            pysparq.Rot_Bool(self.anc_2, self.R_s).conditioned_by_all_ones([self.anc_4])(state)
            pysparq.Xgate_Bool(self.anc_4, 0)(state)

            self.enc_b.dag(state)
            pysparq.Xgate_Bool(self.anc_1, 0)(state)
            pysparq.Reflection_Bool(self.main_reg, True).conditioned_by_all_ones(ref_conds)(state)
            pysparq.Xgate_Bool(self.anc_1, 0)(state)
            self.enc_b(state)

            pysparq.Hadamard_Bool(self.anc_3)(state)

        if unconditioned_state:
            combiner = pysparq.CombineSystems()
            combiner(state, unconditioned_state)

    def dag(self, state):
        raise NotImplementedError("CKS dag not implemented")

    def conditioned_by_all_ones(self, registers):
        self.condition_variable_all_ones = registers
        return self

    def conditioned_by_bit(self, conditions):
        self.condition_variable_by_bit = conditions
        return self
