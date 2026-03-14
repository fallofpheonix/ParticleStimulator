from __future__ import annotations

from dataclasses import dataclass

from src.core.vector import Vector3


@dataclass(frozen=True, slots=True)
class DipoleMagnet:
    magnetic_field_t: float

    def field_at(self, _position: Vector3) -> Vector3:
        return Vector3(0.0, 0.0, self.magnetic_field_t)


@dataclass(frozen=True, slots=True)
class QuadrupoleMagnet:
    gradient_t_per_m: float

    def field_at(self, position: Vector3) -> Vector3:
        return Vector3(self.gradient_t_per_m * position.y, self.gradient_t_per_m * position.x, 0.0)
