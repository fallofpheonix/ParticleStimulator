from __future__ import annotations

from dataclasses import dataclass

from src.core.particle import Particle
from src.core.vector import Vector3


@dataclass(frozen=True, slots=True)
class TrackerHit:
    particle_id: int
    layer_index: int
    position: Vector3
    time_s: float


@dataclass(slots=True)
class SiliconTracker:
    layer_radii_m: tuple[float, ...] = (0.01, 0.03, 0.06)
    z_extent_m: float = 1.0
    radial_tolerance_m: float = 0.008

    def record_hits(self, particle: Particle, time_s: float, seen_layers: set[tuple[int, int]]) -> list[TrackerHit]:
        if particle.charge_c == 0.0 or not particle.alive:
            return []
        if abs(particle.position.z) > self.z_extent_m:
            return []

        radial = particle.position.radial_xy()
        hits: list[TrackerHit] = []
        for index, radius in enumerate(self.layer_radii_m):
            key = (particle.particle_id, index)
            if key in seen_layers:
                continue
            if abs(radial - radius) <= self.radial_tolerance_m:
                seen_layers.add(key)
                hits.append(TrackerHit(particle.particle_id, index, particle.position, time_s))
        return hits
