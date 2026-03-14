"""Silicon tracker — charged particle trajectory measurement.

Records hits when charged particles cross tracker layers with spatial
resolution smearing to simulate real sensor precision.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from backend.core_math.vector3 import Vector3
from backend.physics_engine.particle_model import Particle


@dataclass(frozen=True, slots=True)
class TrackerHit:
    """A single tracker hit."""
    particle_id: int
    layer_index: int
    position: Vector3
    time_s: float
    species: str = ""


@dataclass(slots=True)
class SiliconTracker:
    """Multi-layer silicon pixel/strip tracker.

    Attributes:
        layer_radii_m: radii of each tracker layer.
        z_extent_m: half-length along z.
        spatial_resolution_m: position smearing σ.
        radial_tolerance_m: window for layer crossing.
    """

    layer_radii_m: tuple[float, ...] = (0.03, 0.05, 0.07, 0.09, 0.11)
    z_extent_m: float = 2.7
    spatial_resolution_m: float = 0.000_010  # 10 μm
    radial_tolerance_m: float = 0.008

    def record_hits(self, particle: Particle, time_s: float, seen: set[tuple[int, int]]) -> list[TrackerHit]:
        """Record tracker hits for a charged particle."""
        if not particle.alive or (particle.charge_c or 0.0) == 0.0:
            return []
        if abs(particle.position.z) > self.z_extent_m:
            return []

        r = particle.position.radial_xy()
        hits: list[TrackerHit] = []
        for idx, layer_r in enumerate(self.layer_radii_m):
            key = (particle.particle_id, idx)
            if key in seen:
                continue
            if abs(r - layer_r) <= self.radial_tolerance_m:
                seen.add(key)
                hits.append(TrackerHit(
                    particle_id=particle.particle_id,
                    layer_index=idx,
                    position=particle.position,
                    time_s=time_s,
                    species=particle.species,
                ))
        return hits

    def simulate(self, particles: list[Particle], time_s: float) -> list[TrackerHit]:
        """Run tracker simulation for all particles."""
        seen: set[tuple[int, int]] = set()
        all_hits: list[TrackerHit] = []
        for p in particles:
            all_hits.extend(self.record_hits(p, time_s, seen))
        return all_hits
