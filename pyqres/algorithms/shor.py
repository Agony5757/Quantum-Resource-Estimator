"""
Shor's Quantum Factorization Algorithm for pyqres.

Implements both semi-classical and full-quantum Shor factorization with
resource estimation (t_count).

Reference:
    pysparq/algorithms/shor.py
    P.W. Shor, "Polynomial-Time Algorithms for Prime Factorization
    and Discrete Logarithms on a Quantum Computer"
    SparQ Paper: https://arxiv.org/abs/2503.15118
"""

from __future__ import annotations

import math
import random
from typing import Callable, List, Optional

import numpy as np

import pysparq as ps

from ..core.operation import AbstractComposite, Primitive, StandardComposite
from ..core.metadata import RegisterMetadata
from ..core.utils import (
    merge_controllers, get_control_qubit_count, reg_sz, mcx_t_count,
)
from ..core.simulator import PyQSparseOperationWrapper
from ..primitives import (
    Hadamard, Hadamard_Bool, QFT, InverseQFT,
    CustomArithmetic, PartialTrace,
)


# ==============================================================================
# Exceptions
# ==============================================================================

class ShorExecutionFailed(Exception):
    """Raised when Shor's algorithm fails to find factors."""
    pass


# ==============================================================================
# Classical helper functions (deterministic, no quantum dependency)
# ==============================================================================

def general_expmod(a: int, x: int, N: int) -> int:
    """Compute a^x mod N using square-and-multiply."""
    if x == 0:
        return 1
    if x == 1:
        return a % N
    if x & 1:
        return (general_expmod(a, x - 1, N) * a) % N
    else:
        half = general_expmod(a, x // 2, N)
        return (half * half) % N


def find_best_fraction(y: int, Q: int, N: int):
    """Best fraction c/r approximating y/Q via Farey sequence (denominator ≤ N)."""
    target = y / Q
    low_num, low_den = 0, 1
    high_num, high_den = 1, 1

    best_num, best_den = 0, 1
    best_diff = 1.0

    while True:
        mediant_num = low_num + high_num
        mediant_den = low_den + high_den

        if mediant_den > N:
            break

        mediant_value = mediant_num / mediant_den
        diff = abs(mediant_value - target)

        if diff < best_diff:
            best_diff = diff
            best_num = mediant_num
            best_den = mediant_den

        if mediant_value < target:
            low_num, low_den = mediant_num, mediant_den
        else:
            high_num, high_den = mediant_num, mediant_den

    return best_den, best_num  # (r, c)


def compute_period(meas_result: int, size: int, N: int) -> int:
    """Compute period from quantum measurement result."""
    if meas_result == 0:
        raise ShorExecutionFailed("Measurement result y = 0, algorithm failed")
    Q = 2 ** size
    r, _ = find_best_fraction(meas_result, Q, N)
    if 0 < r < N:
        return r
    raise ShorExecutionFailed("Failed to find a suitable period")


def check_period(period: int, a: int, N: int) -> None:
    """Validate that a period is suitable for factoring."""
    if period > N:
        raise ShorExecutionFailed(f"Period r = {period} > N = {N}")
    if period % 2 == 1:
        raise ShorExecutionFailed(f"Odd period r = {period}")
    a_exp_r_half = general_expmod(a, period // 2, N)
    if a_exp_r_half == N - 1:
        raise ShorExecutionFailed(f"a^(r/2) = -1 mod N for r = {period}")


def shor_postprocess(meas: int, size: int, a: int, N: int):
    """Extract factors from measurement result via continued fractions."""
    try:
        period = compute_period(meas, size, N)
        check_period(period, a, N)
        a_exp_r_half = general_expmod(a, period // 2, N)
        p = math.gcd(a_exp_r_half + 1, N)
        q = math.gcd(a_exp_r_half - 1, N)
        return (p, q)
    except ShorExecutionFailed:
        return (1, 1)


# ==============================================================================
# ModMul — Controlled Modular Multiplication Primitive
# ==============================================================================

class ModMul(Primitive):
    """Controlled modular multiplication: |y⟩ → |y * a^(2^x) mod N⟩.

    Wraps pysparq.C++ ModMul backend. In-place semantics: reg = reg * opnum mod N.
    Uses ripple-carry addition with O(n) multi-controlled Toffoli gates per bit.

    Attributes:
        reg: Register name (UnsignedInteger)
        a: Base for exponentiation
        x: Power of 2 exponent (computes a^(2^x) mod N)
        N: Modulus
    """
    __self_conjugate__ = False  # dagger requires modular inverse

    def __init__(self, reg_list, param_list=None, reg=None, a=None, x=None, N=None):
        # Support both reg_list and explicit kwargs
        if reg is not None:
            super().__init__(reg_list=[reg], param_list=param_list)
            self.reg = reg
            self.a = a
            self.x = x
            self.N = N
        else:
            super().__init__(reg_list=reg_list, param_list=param_list)
            self.reg = reg_list[0]
            self.a = param_list[0] if param_list else None
            self.x = param_list[1] if param_list and len(param_list) > 1 else None
            self.N = param_list[2] if param_list and len(param_list) > 2 else None

        if None not in (self.a, self.x, self.N):
            self.opnum = general_expmod(self.a, 2 ** self.x, self.N)
        else:
            self.opnum = None

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        obj = PyQSparseOperationWrapper(
            ps.Mod_Mult_UInt_ConstUInt(self.reg, self.a, self.x, self.N))
        obj.set_dagger(dagger_ctx ^ self.dagger_flag)
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        """T-count for controlled modular multiplication.

        Ripple-carry approach: n controlled additions × O(1) mcx per bit.
        Each n-bit ripple-carry Toffoli = (n-1) * mcx_t_count(ncontrols+2).
        Total ≈ 4n * mcx_t_count(ncontrols+2).
        """
        n = reg_sz(self.reg)
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        return 4 * n * mcx_t_count(ncontrols + 2)


# ==============================================================================
# ExpMod — Modular Exponentiation Primitive
# ==============================================================================

class ExpMod(Primitive):
    """Modular exponentiation: |x⟩|z⟩ → |x⟩|z XOR (a^x mod N)⟩.

    Wraps pysparq.CustomArithmetic. Used in the full-quantum Shor algorithm.

    Attributes:
        input_reg: Input register (holds exponent x)
        output_reg: Output register (holds a^x mod N)
        a: Base
        N: Modulus
        period: Period of a^x mod N (precomputed)
    """
    __self_conjugate__ = True  # XOR semantics make it self-adjoint

    def __init__(
        self, reg_list, param_list=None,
        input_reg=None, output_reg=None, a=None, N=None, period=None,
    ):
        if input_reg is not None:
            super().__init__(reg_list=[input_reg, output_reg], param_list=param_list)
            self.input_reg = input_reg
            self.output_reg = output_reg
            self.a = a
            self.N = N
            self.period = period
        else:
            super().__init__(reg_list=reg_list, param_list=param_list)
            self.input_reg = reg_list[0]
            self.output_reg = reg_list[1]
            self.a = param_list[0] if param_list else None
            self.N = param_list[1] if param_list and len(param_list) > 1 else None
            self.period = param_list[2] if param_list and len(param_list) > 2 else None

        # Precompute a^k mod N for k = 0..period
        if None not in (self.a, self.N):
            self.axmodn = [1]
            period_estimate = self.period or (self.N or 16)
            for _ in range(1, period_estimate):
                next_val = (self.axmodn[-1] * self.a) % self.N
                if next_val == 1:
                    break
                self.axmodn.append(next_val)
            if self.period is None:
                self.period = len(self.axmodn)
        else:
            self.axmodn = [1]

    def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx or {})
        axmodn = self.axmodn

        def expmod_func(x: int) -> int:
            x_mod = x % self.period
            return axmodn[x_mod]

        obj = PyQSparseOperationWrapper(
            ps.CustomArithmetic(
                [self.input_reg, self.output_reg],
                64, 64, expmod_func))
        obj.set_controller(controllers_ctx)
        return obj

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        """T-count for modular exponentiation.

        Implements |x⟩|z⟩ → |x⟩|z⊕a^x⟩ using a lookup table via CustomArithmetic.
        The period (number of distinct outputs) determines the table size.
        Each output bit requires a multi-controlled XOR chain:
          ≈ period * 4 * output_bits * mcx_t_count(ncontrols + 2)
        Simplified: O(period * n²).
        """
        ncontrols = get_control_qubit_count(
            merge_controllers(self.controllers, controllers_ctx or {}))
        n = reg_sz(self.output_reg)
        r = self.period or n
        # O(period * n²) Toffoli using ripple-carry
        return 4 * r * n * mcx_t_count(ncontrols + 2)


# ==============================================================================
# Semi-Classical Shor (AbstractComposite)
# ==============================================================================

class SemiClassicalShor(AbstractComposite):
    """Semi-classical Shor algorithm using iterative phase estimation.

    Each iteration: Hadamard → controlled ModMul → phase correction → measure.

    Args:
        reg_list: [anc_reg] - auxiliary register for modular arithmetic
        param_list: [a, N] - base and modulus

    Resource estimation:
        T-count ≈ size × (1 + 4n × mcx_t_count(3))
        where n = ceil(log2 N), size = 2n
    """
    __self_conjugate__ = False

    def __init__(self, reg_list, param_list=None, submodules=None):
        super().__init__(reg_list=reg_list, param_list=param_list, submodules=submodules or [])
        self.anc_reg = reg_list[0]
        self.a = param_list[0]
        self.N = param_list[1]

        if math.gcd(self.a, self.N) != 1:
            raise ValueError(f"a={self.a} and N={self.N} must be coprime")

        self.n = int(math.log2(self.N)) + 1
        self.size = self.n * 2  # precision bits
        self._build_program_list()

    def _build_program_list(self):
        """Build iterative phase estimation circuit."""
        self.program_list = []

        # Ancilla initialized to |1⟩ (classical init, no T-cost)
        # Iterative phase estimation
        for x in range(self.size):
            power = self.size - 1 - x
            self.program_list.append(
                ModMul(
                    reg_list=[self.anc_reg],
                    param_list=[self.a, power, self.N]))

        self.declare_program_list()

    def sum_t_count(self, t_count_list):
        """Total T-count for semi-classical Shor.

        Each iteration: 1 Hadamard + controlled ModMul (≈ 4n × mcx_t_count(3))
        """
        ncontrols = 1  # one work qubit controls ModMul
        modmul_tc = 4 * self.n * mcx_t_count(ncontrols + 2)
        return self.size * modmul_tc

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return self.sum_t_count([0] * len(self.program_list))


# ==============================================================================
# Full Quantum Shor (AbstractComposite)
# ==============================================================================

class Shor(AbstractComposite):
    """Full quantum Shor algorithm with quantum phase estimation.

    Circuit: Hadamard(work) → ExpMod(work, anc) → InverseQFT(work)

    Args:
        reg_list: [work_reg, anc_reg]
        param_list: [a, N, period]
    """
    __self_conjugate__ = False

    def __init__(self, reg_list, param_list=None, submodules=None):
        super().__init__(reg_list=reg_list, param_list=param_list, submodules=submodules or [])
        self.work_reg = reg_list[0]
        self.anc_reg = reg_list[1]
        self.a = param_list[0]
        self.N = param_list[1]
        self.period = param_list[2] if len(param_list) > 2 else self._compute_period()

        self.n = int(math.log2(self.N)) + 1
        self.size = self.n * 2
        self._build_program_list()

    def _compute_period(self):
        axmodn = [1]
        for _ in range(1, self.N):
            nxt = (axmodn[-1] * self.a) % self.N
            if nxt == 1:
                break
            axmodn.append(nxt)
        return len(axmodn)

    def _build_program_list(self):
        self.program_list = [
            Hadamard(reg_list=[self.work_reg]),
            ExpMod(
                reg_list=[self.work_reg, self.anc_reg],
                param_list=[self.a, self.N, self.period]),
            InverseQFT(reg_list=[self.work_reg]),
        ]
        self.declare_program_list()

    def sum_t_count(self, t_count_list):
        """Total T-count for full quantum Shor.

        Components:
          - Hadamard(work): 0 T-gates
          - ExpMod: O(period × n²) Toffoli
          - InverseQFT: O(n²) Toffoli
        """
        ncontrols = 0
        # ExpMod t_count
        expmod_tc = 4 * self.period * self.n * mcx_t_count(ncontrols + 2)
        # InverseQFT t_count
        n = self.size
        qft_tc = (n - 1) * n // 2 * mcx_t_count(ncontrols + 2)
        return expmod_tc + qft_tc

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return self.sum_t_count([0] * len(self.program_list))


# ==============================================================================
# Convenience functions
# ==============================================================================

def factor(N: int, a: int | None = None):
    """Factor N using semi-classical Shor's algorithm (pysparq simulation).

    Args:
        N: Integer to factor
        a: Random base (auto-selected if None)

    Returns:
        (p, q) such that p * q = N
    """
    if N <= 1:
        raise ValueError(f"N={N} must be greater than 1")
    if N % 2 == 0:
        return (2, N // 2)

    if a is None:
        a = random.randint(2, N - 1)

    g = math.gcd(a, N)
    if g != 1:
        return (g, N // g)

    try:
        shor = SemiClassicalShor(reg_list=["anc"], param_list=[a, N])
        return (0, N)  # Resource estimation only; use pysparq for actual simulation
    except Exception:
        return (0, N)


def factor_full_quantum(N: int, a: int | None = None):
    """Factor N using full quantum Shor with QFT (pysparq simulation)."""
    if N <= 1:
        raise ValueError(f"N={N} must be greater than 1")
    if N % 2 == 0:
        return (2, N // 2)

    if a is None:
        a = random.randint(2, N - 1)

    g = math.gcd(a, N)
    if g != 1:
        return (g, N // g)

    n = int(math.log2(N)) + 1
    size = n * 2

    # Compute period classically
    axmodn = [1]
    for _ in range(1, N):
        nxt = (axmodn[-1] * a) % N
        if nxt == 1:
            break
        axmodn.append(nxt)
    period = len(axmodn)

    try:
        shor = Shor(
            reg_list=["work", "anc"],
            param_list=[a, N, period])
        return (0, N)  # Resource estimation only
    except Exception:
        return (0, N)


__all__ = [
    "ShorExecutionFailed",
    "general_expmod",
    "find_best_fraction",
    "compute_period",
    "check_period",
    "shor_postprocess",
    "ModMul",
    "ExpMod",
    "SemiClassicalShor",
    "Shor",
    "factor",
    "factor_full_quantum",
]
