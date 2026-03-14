from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vector3":
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> "Vector3":
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> "Vector3":
        if scalar == 0.0:
            raise ZeroDivisionError("cannot divide Vector3 by zero")
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)

    def dot(self, other: "Vector3") -> float:
        return (self.x * other.x) + (self.y * other.y) + (self.z * other.z)

    def cross(self, other: "Vector3") -> "Vector3":
        return Vector3(
            (self.y * other.z) - (self.z * other.y),
            (self.z * other.x) - (self.x * other.z),
            (self.x * other.y) - (self.y * other.x),
        )

    def magnitude_squared(self) -> float:
        return self.dot(self)

    def magnitude(self) -> float:
        return math.sqrt(self.magnitude_squared())

    def normalized(self) -> "Vector3":
        mag = self.magnitude()
        if mag == 0.0:
            return Vector3()
        return self / mag

    def limit(self, max_magnitude: float) -> "Vector3":
        mag = self.magnitude()
        if mag <= max_magnitude or mag == 0.0:
            return self
        return self * (max_magnitude / mag)

    def radial_xy(self) -> float:
        return math.hypot(self.x, self.y)

    def phi(self) -> float:
        return math.atan2(self.y, self.x)

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)
