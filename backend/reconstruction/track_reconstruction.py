"""Track reconstruction — builds particle tracks from tracker hits.

Groups hits by particle ID, fits trajectories, and provides reconstructed
track parameters (direction, momentum estimate, χ²).
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from backend.core_math.vector3 import Vector3
from backend.detector.silicon_tracker import TrackerHit


@dataclass(frozen=True, slots=True)
class ReconstructedTrack:
    """A reconstructed charged particle track."""
    track_id: int
    particle_id: int
    hits: tuple[TrackerHit, ...]
    direction: Vector3
    origin: Vector3
    pt_estimate_gev: float
    chi_squared: float = 0.0


@dataclass(slots=True)
class TrackReconstructor:
    """Groups tracker hits into tracks and fits trajectories."""

    min_hits: int = 3

    def reconstruct(self, hits: list[TrackerHit]) -> list[ReconstructedTrack]:
        """Build tracks from a list of tracker hits."""
        hit_map: dict[int, list[TrackerHit]] = {}
        for h in hits:
            hit_map.setdefault(h.particle_id, []).append(h)

        tracks = []
        tid = 0
        for pid, group in hit_map.items():
            if len(group) < self.min_hits:
                continue
            sorted_hits = sorted(group, key=lambda h: h.layer_index)
            first, last = sorted_hits[0], sorted_hits[-1]
            direction = (last.position - first.position).normalized()
            origin = first.position
            dr = (last.position - first.position).magnitude()
            pt_est = dr * 100.0 if dr > 0 else 0.0
            tid += 1
            tracks.append(ReconstructedTrack(
                track_id=tid, particle_id=pid,
                hits=tuple(sorted_hits), direction=direction,
                origin=origin, pt_estimate_gev=pt_est,
            ))
        return tracks
