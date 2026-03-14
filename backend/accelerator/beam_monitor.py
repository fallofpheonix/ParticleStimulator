"""Beam monitor — beam position and intensity diagnostics.

Provides beam position monitors (BPMs) and intensity measurements
for tracking beam quality during acceleration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from backend.core_math.vector3 import Vector3
from backend.physics_engine.particle_model import Particle


@dataclass(frozen=True, slots=True)
class BeamMeasurement:
    """Snapshot of beam properties at a monitor location."""
    timestamp_s: float
    centroid: Vector3
    rms_x: float
    rms_y: float
    intensity: int  # alive particle count
    mean_speed: float


@dataclass(slots=True)
class BeamMonitor:
    """Records beam position and size at a fixed location.

    Attributes:
        location: longitudinal position along the ring.
        history: recorded measurements.
    """

    location: Vector3 = Vector3()
    history: list[BeamMeasurement] = field(default_factory=list)

    def measure(self, particles: list[Particle], time_s: float) -> BeamMeasurement:
        """Take a beam measurement from the current particle ensemble."""
        alive = [p for p in particles if p.alive]
        n = len(alive)
        if n == 0:
            m = BeamMeasurement(time_s, Vector3(), 0.0, 0.0, 0, 0.0)
            self.history.append(m)
            return m

        cx = sum(p.position.x for p in alive) / n
        cy = sum(p.position.y for p in alive) / n
        cz = sum(p.position.z for p in alive) / n
        centroid = Vector3(cx, cy, cz)

        rms_x = math.sqrt(sum((p.position.x - cx) ** 2 for p in alive) / n)
        rms_y = math.sqrt(sum((p.position.y - cy) ** 2 for p in alive) / n)
        mean_speed = sum(p.speed() for p in alive) / n

        m = BeamMeasurement(time_s, centroid, rms_x, rms_y, n, mean_speed)
        self.history.append(m)
        return m
