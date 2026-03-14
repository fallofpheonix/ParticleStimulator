"""Vertex finding — reconstruct the primary interaction vertex from tracks."""

from __future__ import annotations
from dataclasses import dataclass
from backend.core_math.vector3 import Vector3
from backend.reconstruction.track_reconstruction import ReconstructedTrack


@dataclass(frozen=True, slots=True)
class ReconstructedVertex:
    """A reconstructed interaction vertex."""
    vertex_id: int
    position: Vector3
    n_tracks: int
    chi_squared: float = 0.0


@dataclass(slots=True)
class VertexFinder:
    """Finds the primary vertex as the mean origin of reconstructed tracks."""

    min_tracks: int = 2

    def find_vertices(self, tracks: list[ReconstructedTrack]) -> list[ReconstructedVertex]:
        if len(tracks) < self.min_tracks:
            return []
        sx = sum(t.origin.x for t in tracks)
        sy = sum(t.origin.y for t in tracks)
        sz = sum(t.origin.z for t in tracks)
        n = len(tracks)
        mean_pos = Vector3(sx / n, sy / n, sz / n)
        return [ReconstructedVertex(vertex_id=1, position=mean_pos, n_tracks=n)]
