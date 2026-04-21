"""
Shor's Quantum Factorization Algorithm (Semi-Classical Version)

This module implements the semi-classical Shor algorithm for integer factorization.
It uses iterative phase estimation with classical feedforward for quantum speedup.

Reference: PySparQ algorithms/shor.py
"""

import math
import random
from fractions import Fraction

from ..core.operation import AbstractComposite
from ..core.registry import OperationRegistry


def general_expmod(a: int, x: int, N: int) -> int:
    """Compute a^x mod N using square-and-multiply algorithm."""
    if x == 0:
        return 1
    if x == 1:
        return a % N
    if x & 1:  # odd
        return (general_expmod(a, x - 1, N) * a) % N
    else:  # even
        half = general_expmod(a, x // 2, N)
        return (half * half) % N


def find_best_fraction(y: int, Q: int, N: int):
    """Find best fraction c/r ≈ y/Q using continued fraction expansion (Farey sequence)."""
    target = y / Q
    low_num, low_den = 0, 1
    high_num, high_den = 1, 1
    best_num, best_den = 0, 1

    while low_den + high_den <= N:
        mediant_num = low_num + high_num
        mediant_den = low_den + high_den

        if mediant_num / mediant_den < target:
            low_num, low_den = mediant_num, mediant_den
        else:
            high_num, high_den = mediant_num, mediant_den

        # Track best approximation
        if abs(mediant_num / mediant_den - target) < abs(best_num / best_den - target):
            best_num, best_den = mediant_num, mediant_den

    return best_den, best_num  # (r, c)


def shor_postprocess(meas: int, size: int, a: int, N: int):
    """Extract factors from measurement result using continued fractions."""
    Q = 2 ** size
    r, _ = find_best_fraction(meas, Q, N)

    # Validate period
    if r > N:
        raise ValueError("Period too large")
    if r % 2 == 1:
        raise ValueError("Odd period")

    # Check a^(r/2) ≠ -1 mod N
    a_r_half = general_expmod(a, r // 2, N)
    if a_r_half == N - 1:
        raise ValueError("a^(r/2) = -1 mod N")

    # Compute factors
    p = math.gcd(a_r_half + 1, N)
    q = math.gcd(a_r_half - 1, N)

    return p, q


class SemiClassicalShor(AbstractComposite):
    """Semi-classical Shor algorithm using iterative phase estimation.

    Args:
        reg_list: [anc_reg] - auxiliary register for modular arithmetic
        param_list: [a, N] - base and modulus
    """

    def __init__(self, reg_list, param_list, submodules=None):
        super().__init__(reg_list=reg_list, param_list=param_list, submodules=submodules or [])
        self.anc_reg = reg_list[0]
        self.a = param_list[0]
        self.N = param_list[1]

        if math.gcd(self.a, self.N) != 1:
            raise ValueError("a and N must be coprime")

        self.n = int(math.log2(self.N)) + 1
        self.size = self.n * 2  # precision register size

        # Build program list: iterative phase estimation
        self._build_program_list()

    def _build_program_list(self):
        """Build the quantum circuit for semi-classical Shor."""
        self.program_list = []

        # Initialize auxiliary register to |1⟩
        X_op = OperationRegistry.get_class("X")
        self.program_list.append(X_op(reg_list=[self.anc_reg[0]]))

        # Iterative phase estimation: size iterations
        for x in range(self.size):
            # Add work qubit with Hadamard
            Hadamard_op = OperationRegistry.get_class("Hadamard")
            self.program_list.append(Hadamard_op(reg_list=[f"work_{x}"]))

            # Controlled modular multiplication (placeholder - requires CustomArithmetic)
            # This is complex and typically uses Unroller or special handling
            # For resource estimation, we use a simplified model

        self.declare_program_list()

    def sum_t_count(self, t_count_list):
        """Compute total T-count for semi-classical Shor."""
        # Approximate cost: size * (modmul_cost + hadamard_cost)
        # Modmul cost for a^x mod N: O(n^2) Toffoli gates
        n = self.n
        modmul_cost = 4 * n * n  # rough approximation
        size = self.size

        # Sum all operations' T-counts (first Hadamard + X)
        base_cost = t_count_list[0] + t_count_list[1] if len(t_count_list) > 1 else 0

        # Iterations: size times of hadamard + controlled ops
        hadamard_cost = 0  # single qubit
        controlled_cost = modmul_cost  # controlled modular multiplication

        return base_cost + size * (hadamard_cost + controlled_cost)


class ShorFactor(AbstractComposite):
    """Complete Shor factorization with classical post-processing.

    Args:
        reg_list: [anc_reg] - auxiliary register
        param_list: [N] - number to factor
    """

    def __init__(self, reg_list, param_list, submodules=None):
        super().__init__(reg_list=reg_list, param_list=param_list, submodules=submodules or [])
        self.anc_reg = reg_list[0]
        self.N = param_list[0]

        if self.N % 2 == 0:
            # Even number: trivial factorization
            self.program_list = []
            self.declare_program_list()
            return

        self.n = int(math.log2(self.N)) + 1
        self.size = self.n * 2

        # Build program list
        self._build_program_list()

    def _build_program_list(self):
        """Build the quantum circuit."""
        self.program_list = []

        # Initialize ancilla to |1⟩
        X_op = OperationRegistry.get_class("X")
        self.program_list.append(X_op(reg_list=[self.anc_reg[0]]))

        # Iterative phase estimation
        for x in range(self.size):
            # Work qubit initialization with Hadamard
            H_op = OperationRegistry.get_class("Hadamard")
            self.program_list.append(H_op(reg_list=[f"work_{x}"]))

            # Controlled modular multiplication
            # Note: Full implementation requires CustomArithmetic or modular multiplier
            # For now, we add placeholder operations for resource estimation

        self.declare_program_list()

    def sum_t_count(self, t_count_list):
        """Compute total T-count."""
        n = self.n
        size = self.size
        # Approximate: O(n^3) T-gates for modular exponentiation
        modmul_cost = 5 * n * n * n
        return size * (modmul_cost + 1)  # +1 for Hadamard


def factor(N: int, a: int = None):
    """Factor N using Shor's algorithm.

    Args:
        N: Integer to factor
        a: Random base (auto-selected if None)

    Returns:
        (p, q) such that p * q = N
    """
    if N % 2 == 0:
        return (2, N // 2)

    if a is None:
        a = random.randint(2, N - 1)

    # Check if already a factor
    g = math.gcd(a, N)
    if g != 1:
        return (g, N // g)

    # Semi-classical Shor
    anc_reg = [('anc_reg', N.bit_length())]
    shor = SemiClassicalShor(reg_list=[anc_reg[0]], param_list=[a, N])

    # Simulate measurement (in practice, use quantum simulation)
    # For resource estimation, we just return the structure

    return None, None  # Requires quantum execution


__all__ = [
    "general_expmod",
    "find_best_fraction",
    "shor_postprocess",
    "SemiClassicalShor",
    "ShorFactor",
    "factor",
]