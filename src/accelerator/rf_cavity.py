from __future__ import annotations

from dataclasses import dataclass

from core.vector import Vector3


@dataclass(frozen=True, slots=True)
class RFCavity:
    center: Vector3
    half_width_m: float
    electric_field_v_m: float

    def field_at(self, position: Vector3) -> Vector3:
        if abs(position.x - self.center.x) > self.half_width_m:
            return Vector3()
        if abs(position.y - self.center.y) > self.half_width_m:
            return Vector3()
        return Vector3(0.0, self.electric_field_v_m, 0.0)
