"""QRAM utility functions for state preparation and block encoding.

These functions are used for computing rotation angles and building
binary trees for QRAM-based quantum operations.

Ported from QRAM-Simulator/PySparQ/pysparq/algorithms/qram_utils.py
"""

from __future__ import annotations

import math
from typing import Union, List

import numpy as np


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PI: float = math.pi
"""Pi constant."""


# ---------------------------------------------------------------------------
# Bit helpers
# ---------------------------------------------------------------------------

def pow2(n: int) -> int:
    """Return 2**n using a left shift."""
    return 1 << n


# ---------------------------------------------------------------------------
# Two's-complement helpers
# ---------------------------------------------------------------------------

def make_complement(data: int, data_sz: int) -> int:
    """Convert a signed integer to its two's-complement representation.

    For negative data with data_sz < 64 bits, the result is
    2**data_sz + data (i.e. the unsigned encoding of the negative value
    in data_sz bits). For non-negative data, or when data_sz == 64,
    data is returned unchanged.
    """
    if data_sz == 64 or data >= 0:
        return data
    return pow2(data_sz) + data


def get_complement(data: int, data_sz: int) -> int:
    """Reverse two's-complement: sign-extend an unsigned value to a signed int."""
    if data_sz == 0:
        return 0
    if data_sz == 64:
        if data >= (1 << 63):
            return data - (1 << 64)
        return data
    sign_bit = 1 << (data_sz - 1)
    if data & sign_bit:
        return data - pow2(data_sz)
    return data


# ---------------------------------------------------------------------------
# Matrix / vector helpers for QRAM data preparation
# ---------------------------------------------------------------------------

def column_flatten(row_vec: List[float]) -> List[float]:
    """Transpose a flat row-major square-matrix representation to column-major."""
    size = len(row_vec)
    n = int(math.isqrt(size))
    if n * n != size:
        raise ValueError(
            f"Input length {size} is not a perfect square; "
            "expected a flat square-matrix representation."
        )
    col_vec = [0.0] * size
    for i in range(n):
        for j in range(n):
            col_vec[j * n + i] = row_vec[i * n + j]
    return col_vec


def scale_and_convert_vector(
    input_vec: Union[List[float], np.ndarray],
    exponent: int,
    data_size: int,
    from_matrix: bool = True,
) -> List[int]:
    """Scale floating-point values and convert to two's-complement integers."""
    if isinstance(input_vec, np.ndarray):
        input_vec = input_vec.tolist()
    if from_matrix:
        col_vec = column_flatten(input_vec)
    else:
        col_vec = list(input_vec)
    scale = 2.0 ** exponent
    output: List[int] = []
    for value in col_vec:
        scaled = int(round(value * scale))
        output.append(make_complement(scaled, data_size))
    return output


def make_vector_tree(dist: List[int], data_size: int) -> List[int]:
    """Build a binary tree from leaf distribution data for QRAM circuits.

    The algorithm iteratively pairs adjacent entries in dist:
    - Leaf level (first iteration): each pair is squared after sign-extension
    - Inner levels (subsequent iterations): pairs are summed directly

    After pairing, the current layer is appended, producing a breadth-first
    tree ordering. A trailing 0 is appended to match the C++ behaviour.
    """
    dist_sz = len(dist)
    temp_tree = list(dist)

    current_sz = dist_sz
    is_first = True

    while True:
        temp: List[int] = []
        i = 0
        while i < current_sz:
            if i + 1 < current_sz:
                if is_first:
                    a = get_complement(temp_tree[i], data_size)
                    b = get_complement(temp_tree[i + 1], data_size)
                    temp.append(a * a + b * b)
                else:
                    temp.append(temp_tree[i] + temp_tree[i + 1])
            i += 2

        temp.extend(temp_tree)
        temp_tree = temp

        current_sz = (current_sz + 1) // 2
        is_first = False

        if current_sz <= 1:
            break

    temp_tree.append(0)
    return temp_tree


# ---------------------------------------------------------------------------
# Rotation-matrix helpers (conditional rotations)
# ---------------------------------------------------------------------------

def make_func(value: int, n_digit: int) -> List[complex]:
    """Compute a 2x2 rotation matrix from a rational register value.

    The rotation angle is:
    theta = value / 2**n_digit * 2 * pi

    Returns [cos(theta), -sin(theta), sin(theta), cos(theta)] (row-major).
    """
    if n_digit == 64:
        theta = value * 1.0 / 2 / pow2(63)
    else:
        theta = value * 1.0 / pow2(n_digit)

    theta *= 2 * PI

    u00 = complex(math.cos(theta), 0.0)
    u01 = complex(-math.sin(theta), 0.0)
    u10 = complex(math.sin(theta), 0.0)
    u11 = complex(math.cos(theta), 0.0)

    return [u00, u01, u10, u11]


def make_func_inv(value: int, n_digit: int) -> List[complex]:
    """Compute the inverse 2x2 rotation matrix from a rational register value.

    Same as make_func but the off-diagonal signs are flipped:
    [cos(theta), sin(theta), -sin(theta), cos(theta)].
    """
    if n_digit == 64:
        theta = value * 1.0 / 2 / pow2(63)
    else:
        theta = value * 1.0 / pow2(n_digit)

    theta *= 2 * PI

    u00 = complex(math.cos(theta), 0.0)
    u01 = complex(math.sin(theta), 0.0)
    u10 = complex(-math.sin(theta), 0.0)
    u11 = complex(math.cos(theta), 0.0)

    return [u00, u01, u10, u11]


__all__ = [
    "PI",
    "pow2",
    "make_complement",
    "get_complement",
    "column_flatten",
    "scale_and_convert_vector",
    "make_vector_tree",
    "make_func",
    "make_func_inv",
]
