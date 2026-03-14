"""Three-dimensional Euclidean vector.

Provides a lightweight, immutable 3-vector with standard operations used
throughout the physics simulation: addition, scalar multiplication, dot
product, cross product, rotation, and coordinate conversions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Vector3:
    """Immutable 3-component vector in Cartesian coordinates."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    # -- arithmetic ---------------------------------------------------------

    def __add__(self, other: Vector3) -> Vector3:
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vector3) -> Vector3:
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> Vector3:
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> Vector3:
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> Vector3:
        if scalar == 0.0:
            raise ZeroDivisionError("cannot divide Vector3 by zero")
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)

    def __neg__(self) -> Vector3:
        return Vector3(-self.x, -self.y, -self.z)

    # -- products -----------------------------------------------------------

    def dot(self, other: Vector3) -> float:
        """Euclidean dot product."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: Vector3) -> Vector3:
        """Euclidean cross product."""
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    # -- magnitude ----------------------------------------------------------

    def magnitude_squared(self) -> float:
        return self.dot(self)

    def magnitude(self) -> float:
        return math.sqrt(self.magnitude_squared())

    def normalized(self) -> Vector3:
        """Unit vector in the same direction (zero vector returns zero)."""
        mag = self.magnitude()
        if mag == 0.0:
            return Vector3()
        return self / mag

    def limit(self, max_magnitude: float) -> Vector3:
        """Clamp magnitude to *max_magnitude*."""
        mag = self.magnitude()
        if mag <= max_magnitude or mag == 0.0:
            return self
        return self * (max_magnitude / mag)

    # -- coordinate helpers -------------------------------------------------

    def radial_xy(self) -> float:
        """Transverse distance from the z-axis."""
        return math.hypot(self.x, self.y)

    def phi(self) -> float:
        """Azimuthal angle in the x-y plane."""
        return math.atan2(self.y, self.x)

    def theta(self) -> float:
        """Polar angle from the z-axis."""
        return math.atan2(self.radial_xy(), self.z)

    def eta(self) -> float:
        """Pseudorapidity η = −ln[tan(θ/2)]."""
        th = self.theta()
        if th <= 0.0 or th >= math.pi:
            return float("inf") if th <= 0.0 else float("-inf")
        return -math.log(math.tan(th / 2.0))

    # -- rotation -----------------------------------------------------------

    def rotate_z(self, angle_rad: float) -> Vector3:
        """Rotate around the z-axis by *angle_rad*."""
        c, s = math.cos(angle_rad), math.sin(angle_rad)
        return Vector3(c * self.x - s * self.y, s * self.x + c * self.y, self.z)

    def rotate_y(self, angle_rad: float) -> Vector3:
        """Rotate around the y-axis by *angle_rad*."""
        c, s = math.cos(angle_rad), math.sin(angle_rad)
        return Vector3(c * self.x + s * self.z, self.y, -s * self.x + c * self.z)

    # -- serialisation ------------------------------------------------------

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def as_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y, "z": self.z}
