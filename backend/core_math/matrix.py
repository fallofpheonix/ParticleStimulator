"""3×3 and 4×4 matrix operations for rotations and Lorentz transformations.

Matrices are stored as flat tuples for immutability and performance.
Provides rotation matrices (Euler, axis-angle), Lorentz boost matrices,
and standard linear-algebra operations (multiplication, transpose, determinant).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from backend.core_math.vector3 import Vector3
from backend.core_math.vector4 import FourVector


# ---------------------------------------------------------------------------
# 3×3 Matrix
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Matrix3:
    """3×3 matrix stored in row-major order."""

    elements: tuple[float, ...] = (
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
        0.0, 0.0, 1.0,
    )

    def __post_init__(self) -> None:
        if len(self.elements) != 9:
            raise ValueError("Matrix3 requires exactly 9 elements")

    def __getitem__(self, index: tuple[int, int]) -> float:
        row, col = index
        return self.elements[row * 3 + col]

    def __matmul__(self, other: Matrix3) -> Matrix3:
        a, b = self.elements, other.elements
        result = []
        for r in range(3):
            for c in range(3):
                result.append(sum(a[r * 3 + k] * b[k * 3 + c] for k in range(3)))
        return Matrix3(tuple(result))

    def transform(self, v: Vector3) -> Vector3:
        """Multiply matrix × vector."""
        e = self.elements
        return Vector3(
            e[0] * v.x + e[1] * v.y + e[2] * v.z,
            e[3] * v.x + e[4] * v.y + e[5] * v.z,
            e[6] * v.x + e[7] * v.y + e[8] * v.z,
        )

    def transpose(self) -> Matrix3:
        e = self.elements
        return Matrix3((
            e[0], e[3], e[6],
            e[1], e[4], e[7],
            e[2], e[5], e[8],
        ))

    def determinant(self) -> float:
        e = self.elements
        return (
            e[0] * (e[4] * e[8] - e[5] * e[7])
            - e[1] * (e[3] * e[8] - e[5] * e[6])
            + e[2] * (e[3] * e[7] - e[4] * e[6])
        )

    @classmethod
    def identity(cls) -> Matrix3:
        return cls()

    @classmethod
    def rotation_x(cls, angle: float) -> Matrix3:
        c, s = math.cos(angle), math.sin(angle)
        return cls((1.0, 0.0, 0.0, 0.0, c, -s, 0.0, s, c))

    @classmethod
    def rotation_y(cls, angle: float) -> Matrix3:
        c, s = math.cos(angle), math.sin(angle)
        return cls((c, 0.0, s, 0.0, 1.0, 0.0, -s, 0.0, c))

    @classmethod
    def rotation_z(cls, angle: float) -> Matrix3:
        c, s = math.cos(angle), math.sin(angle)
        return cls((c, -s, 0.0, s, c, 0.0, 0.0, 0.0, 1.0))


# ---------------------------------------------------------------------------
# 4×4 Matrix
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Matrix4:
    """4×4 matrix stored in row-major order, used for Lorentz transformations."""

    elements: tuple[float, ...] = (
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    )

    def __post_init__(self) -> None:
        if len(self.elements) != 16:
            raise ValueError("Matrix4 requires exactly 16 elements")

    def __getitem__(self, index: tuple[int, int]) -> float:
        row, col = index
        return self.elements[row * 4 + col]

    def __matmul__(self, other: Matrix4) -> Matrix4:
        a, b = self.elements, other.elements
        result = []
        for r in range(4):
            for c in range(4):
                result.append(sum(a[r * 4 + k] * b[k * 4 + c] for k in range(4)))
        return Matrix4(tuple(result))

    def transform(self, v: FourVector) -> FourVector:
        """Multiply matrix × four-vector."""
        e = self.elements
        comps = (v.t, v.x, v.y, v.z)
        result = [sum(e[r * 4 + c] * comps[c] for c in range(4)) for r in range(4)]
        return FourVector(*result)

    def transpose(self) -> Matrix4:
        e = self.elements
        return Matrix4(tuple(e[c * 4 + r] for r in range(4) for c in range(4)))

    @classmethod
    def identity(cls) -> Matrix4:
        return cls()


# ---------------------------------------------------------------------------
# Lorentz boost matrix factory
# ---------------------------------------------------------------------------


def lorentz_boost_matrix(beta_vec: Vector3) -> Matrix4:
    """Build a 4×4 Lorentz boost matrix for velocity β⃗ = v⃗/c.

    Uses the general formula for an arbitrary-direction boost.
    Metric signature: (+, −, −, −).
    """
    beta_sq = beta_vec.magnitude_squared()
    if beta_sq == 0.0:
        return Matrix4.identity()
    if beta_sq >= 1.0:
        raise ValueError("β² must be < 1 for a valid Lorentz boost")

    gamma = 1.0 / math.sqrt(1.0 - beta_sq)
    bx, by, bz = beta_vec.x, beta_vec.y, beta_vec.z
    g1 = (gamma - 1.0) / beta_sq

    return Matrix4((
        gamma,        -gamma * bx,            -gamma * by,            -gamma * bz,
        -gamma * bx,  1.0 + g1 * bx * bx,    g1 * bx * by,           g1 * bx * bz,
        -gamma * by,  g1 * by * bx,           1.0 + g1 * by * by,    g1 * by * bz,
        -gamma * bz,  g1 * bz * bx,           g1 * bz * by,          1.0 + g1 * bz * bz,
    ))
