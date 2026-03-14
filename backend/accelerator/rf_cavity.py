"""RF cavity — radiofrequency acceleration of charged particles.

An RF cavity provides a time-varying (or simplified static) electric field
along the beam direction, boosting particle energy each traversal.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from backend.core_math.vector3 import Vector3


@dataclass(frozen=True, slots=True)
class RFCavity:
    """Radio-frequency acceleration cavity.

    Attributes:
        center: 3D position of the cavity centre.
        half_width_m: spatial extent around centre where field is active.
        voltage_v: peak accelerating voltage per passage.
        frequency_hz: RF oscillation frequency.
        phase_rad: synchronous phase (0 = on-crest acceleration).
    """

    center: Vector3 = Vector3()
    half_width_m: float = 0.15
    voltage_v: float = 2.0e6
    frequency_hz: float = 400.789e6
    phase_rad: float = 0.0

    def field_at(self, position: Vector3, time_s: float = 0.0) -> Vector3:
        """Electric field inside the cavity gap.

        Returns a y-directed E-field when the particle is within the gap,
        modulated by the RF oscillation.
        """
        if abs(position.x - self.center.x) > self.half_width_m:
            return Vector3()
        if abs(position.y - self.center.y) > self.half_width_m:
            return Vector3()

        gap = 2.0 * self.half_width_m
        e_peak = self.voltage_v / max(gap, 1.0e-6)
        phase = 2.0 * math.pi * self.frequency_hz * time_s + self.phase_rad
        return Vector3(0.0, e_peak * math.cos(phase), 0.0)

    def energy_gain_per_turn(self) -> float:
        """Maximum energy gain per traversal (eV) = qV·cos(φ)."""
        return self.voltage_v * math.cos(self.phase_rad)
