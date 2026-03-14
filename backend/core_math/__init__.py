"""Core Math Engine — foundational numerical and vector math for the simulator."""

from backend.core_math.vector3 import Vector3
from backend.core_math.vector4 import FourVector
from backend.core_math.matrix import Matrix3, Matrix4, lorentz_boost_matrix
from backend.core_math.constants import (
    SPEED_OF_LIGHT,
    ELEMENTARY_CHARGE,
    PLANCK_CONSTANT,
    PARTICLE_MASSES,
    PARTICLE_CHARGES,
)

__all__ = [
    "Vector3",
    "FourVector",
    "Matrix3",
    "Matrix4",
    "lorentz_boost_matrix",
    "SPEED_OF_LIGHT",
    "ELEMENTARY_CHARGE",
    "PLANCK_CONSTANT",
    "PARTICLE_MASSES",
    "PARTICLE_CHARGES",
]
