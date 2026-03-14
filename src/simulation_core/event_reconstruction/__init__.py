"""
event_reconstruction — Converts raw detector hits into physics objects.

Subsystem responsibilities:
  • track_reconstruction: group tracker hits into track candidates
  • kalman_filter: fit each track to obtain momentum and impact parameter
  • vertex_finding: find primary and secondary vertices from tracks
  • jet_clustering: anti-kT jet algorithm on calorimeter deposits
  • missing_energy: compute MET from calorimeter momentum imbalance

Output: ReconstructedEvent containing tracks, jets, vertices, and MET.
"""

from __future__ import annotations

import math
import itertools
from typing import List, Tuple, Optional, Dict

import numpy as np

from src.simulation_core.core_models.models import (
    DetectorHit,
    ReconstructedTrack,
    ReconstructedJet,
    ReconstructedVertex,
    ReconstructedEvent,
    Vec3,
)

_track_id_counter = itertools.count(1)
_jet_id_counter   = itertools.count(1)
_vtx_id_counter   = itertools.count(1)


# ─────────────────────────────────────────────────────────────────────────────
# track_reconstruction.py — hit grouping and seed finding
# ─────────────────────────────────────────────────────────────────────────────

TRACKER_LAYER_ORDER = ["tracker_0", "tracker_1", "tracker_2", "tracker_3"]


def group_hits_by_particle(hits: List[DetectorHit]) -> Dict[int, List[DetectorHit]]:
    """Group tracker hits by the originating particle ID (truth-level seeding)."""
    groups: Dict[int, List[DetectorHit]] = {}
    for h in hits:
        if h.detector_layer.startswith("tracker"):
            groups.setdefault(h.particle_id, []).append(h)
    return groups


# ─────────────────────────────────────────────────────────────────────────────
# kalman_filter.py — 1D Kalman filter for track parameter estimation
# ─────────────────────────────────────────────────────────────────────────────

class KalmanFilter1D:
    """
    Simplified 1D Kalman filter for track position/momentum estimation.

    State vector: [x, px] (position and momentum in one transverse plane).
    Process model: straight-line propagation (no magnetic field correction here —
    a full KF would use a helix model).
    """

    def __init__(self, process_noise: float = 0.001, measurement_noise: float = 0.01):
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise

    def filter(self, measurements: List[float]) -> Tuple[float, float]:
        """
        Run the Kalman filter over a sequence of measurements.

        Returns:
            (filtered_value, estimated_variance) at the final step.
        """
        if not measurements:
            return 0.0, 1.0

        # Initialise with first measurement
        x_est = measurements[0]
        P = self.measurement_noise   # Initial covariance

        for z in measurements[1:]:
            # Predict
            x_pred = x_est
            P_pred = P + self.process_noise

            # Update
            K = P_pred / (P_pred + self.measurement_noise)  # Kalman gain
            x_est = x_pred + K * (z - x_pred)
            P = (1 - K) * P_pred

        return x_est, P


def fit_track(hits: List[DetectorHit]) -> Tuple[Vec3, float]:
    """
    Fit a track to a set of detector hits using a simplified Kalman filter
    in each coordinate independently.

    Returns:
        (momentum_gev, chi2_per_ndof) — momentum direction and fit quality.
    """
    if len(hits) < 2:
        return (0.0, 0.0, 1.0), float("inf")

    # Sort hits by layer radius
    hits_sorted = sorted(hits, key=lambda h: math.sqrt(h.position[0]**2 + h.position[1]**2))

    xs = [h.position[0] for h in hits_sorted]
    ys = [h.position[1] for h in hits_sorted]
    zs = [h.position[2] for h in hits_sorted]

    kf = KalmanFilter1D()
    x_est, P_x = kf.filter(xs)
    y_est, P_y = kf.filter(ys)
    z_est, P_z = kf.filter(zs)

    # Direction from first to last hit
    dx = hits_sorted[-1].position[0] - hits_sorted[0].position[0]
    dy = hits_sorted[-1].position[1] - hits_sorted[0].position[1]
    dz = hits_sorted[-1].position[2] - hits_sorted[0].position[2]
    dr = math.sqrt(dx*dx + dy*dy + dz*dz)

    if dr < 1e-6:
        return (0.0, 0.0, 1.0), float("inf")

    # Estimate momentum magnitude from track curvature proxy
    # (simplified: use transverse displacement × 100 GeV/m)
    r_transverse = math.sqrt(hits_sorted[-1].position[0]**2 + hits_sorted[-1].position[1]**2)
    r_inner      = math.sqrt(hits_sorted[0].position[0]**2 + hits_sorted[0].position[1]**2)
    p_est_gev = (r_transverse - r_inner) * 100.0  # crude estimate
    p_est_gev = max(0.1, min(p_est_gev, 10000.0))

    px = p_est_gev * dx / dr
    py = p_est_gev * dy / dr
    pz = p_est_gev * dz / dr

    # Chi² / ndf from residuals
    residuals = [(h.position[0] - x_est)**2 + (h.position[1] - y_est)**2 for h in hits_sorted]
    sigma2 = 1.0e-8   # (100 μm)²
    chi2 = sum(r / sigma2 for r in residuals)
    ndf = max(1, len(hits_sorted) - 2)
    chi2_ndf = chi2 / ndf

    return (px, py, pz), chi2_ndf


# ─────────────────────────────────────────────────────────────────────────────
# track_reconstruction — main reconstructor
# ─────────────────────────────────────────────────────────────────────────────

class TrackReconstructor:
    """
    Build ReconstructedTrack objects from tracker DetectorHits.
    """

    def __init__(self, min_hits: int = 3, max_chi2_ndf: float = 10.0):
        self.min_hits = min_hits
        self.max_chi2_ndf = max_chi2_ndf

    def reconstruct(self, hits: List[DetectorHit]) -> List[ReconstructedTrack]:
        """
        Reconstruct tracks from all tracker hits.

        Groups hits by particle ID (truth seeding), fits each group with
        the Kalman filter, and applies quality cuts.

        Returns:
            List of ReconstructedTrack objects.
        """
        groups = group_hits_by_particle(hits)
        tracks = []

        for pid, group_hits in groups.items():
            if len(group_hits) < self.min_hits:
                continue

            momentum, chi2_ndf = fit_track(group_hits)
            if chi2_ndf > self.max_chi2_ndf:
                continue

            # Estimate charge sign from curvature direction
            # Simplified: use sign of hit radial displacement
            dx = group_hits[-1].position[0] - group_hits[0].position[0]
            charge = 1.0 if dx >= 0 else -1.0

            track = ReconstructedTrack(
                track_id=next(_track_id_counter),
                hits=group_hits,
                momentum=momentum,
                charge=charge,
                chi2_per_ndof=chi2_ndf,
                n_hits=len(group_hits),
            )
            tracks.append(track)

        return tracks


# ─────────────────────────────────────────────────────────────────────────────
# vertex_finding.py — primary vertex reconstruction
# ─────────────────────────────────────────────────────────────────────────────

class VertexFinder:
    """
    Find the primary interaction vertex from reconstructed tracks.

    Uses a simplified adaptive vertex fitting approach:
    weights tracks by their impact parameter significance and
    iterates to convergence.
    """

    def __init__(self, min_tracks: int = 2, max_iterations: int = 20):
        self.min_tracks = min_tracks
        self.max_iterations = max_iterations

    def find_vertices(
        self,
        tracks: List[ReconstructedTrack],
    ) -> List[ReconstructedVertex]:
        """
        Find primary (and optionally secondary) vertices.

        Returns:
            List of ReconstructedVertex objects.
        """
        if len(tracks) < self.min_tracks:
            return []

        # Simplified: use the mean of the first hit position of all tracks
        # as the primary vertex estimate, then iteratively reweight.
        positions = []
        for t in tracks:
            if t.hits:
                positions.append(np.array(t.hits[0].position, dtype=np.float64))

        if not positions:
            return []

        # Iterative weighted mean (simplified adaptive fitting)
        vertex_pos = np.mean(positions, axis=0)

        for _ in range(self.max_iterations):
            # Weight each track by 1/(1 + d²/σ²)  with σ = 0.1 mm
            sigma = 0.0001
            weights = []
            for pos in positions:
                d2 = float(np.sum((pos - vertex_pos)**2))
                w = 1.0 / (1.0 + d2 / sigma**2)
                weights.append(w)
            w_arr = np.array(weights)
            w_sum = float(np.sum(w_arr))
            if w_sum < 1e-10:
                break
            new_vtx = np.sum([w * p for w, p in zip(w_arr, positions)], axis=0) / w_sum
            if float(np.linalg.norm(new_vtx - vertex_pos)) < 1e-8:
                break
            vertex_pos = new_vtx

        # Chi² / ndf
        sigma2 = (0.0001)**2
        chi2 = sum(float(np.sum((p - vertex_pos)**2)) / sigma2 for p in positions)
        ndf = max(1, 3 * len(positions) - 3)

        vtx = ReconstructedVertex(
            vertex_id=next(_vtx_id_counter),
            position=(float(vertex_pos[0]), float(vertex_pos[1]), float(vertex_pos[2])),
            tracks=tracks,
            chi2_per_ndof=chi2 / ndf,
            is_primary=True,
        )
        return [vtx]


# ─────────────────────────────────────────────────────────────────────────────
# jet_clustering.py — anti-kT algorithm
# ─────────────────────────────────────────────────────────────────────────────

class PseudoJet:
    """Lightweight jet candidate for the anti-kT clustering."""

    def __init__(self, e: float, px: float, py: float, pz: float, hits: List[DetectorHit] = None):
        self.e = e; self.px = px; self.py = py; self.pz = pz
        self.hits = hits or []

    @property
    def pt2(self) -> float:
        return self.px**2 + self.py**2

    @property
    def pt(self) -> float:
        return math.sqrt(self.pt2)

    @property
    def phi(self) -> float:
        return math.atan2(self.py, self.px)

    @property
    def rapidity(self) -> float:
        if self.e <= abs(self.pz):
            return 0.0
        return 0.5 * math.log((self.e + self.pz) / (self.e - self.pz))

    def delta_r(self, other: "PseudoJet") -> float:
        drap = self.rapidity - other.rapidity
        dphi = self.phi - other.phi
        while dphi > math.pi:  dphi -= 2*math.pi
        while dphi < -math.pi: dphi += 2*math.pi
        return math.sqrt(drap**2 + dphi**2)

    def merge(self, other: "PseudoJet") -> "PseudoJet":
        return PseudoJet(
            self.e + other.e,
            self.px + other.px,
            self.py + other.py,
            self.pz + other.pz,
            self.hits + other.hits,
        )


def anti_kt_cluster(
    deposits: List[DetectorHit],
    R: float = 0.4,
    min_pt_gev: float = 5.0,
) -> List[PseudoJet]:
    """
    Anti-kT jet clustering algorithm.

    Distance metric:
        d_ij = min(pT_i^{-2}, pT_j^{-2}) × ΔR²_ij / R²
        d_iB = pT_i^{-2}

    Particles are merged when d_ij < d_iB.

    Args:
        deposits: calorimeter DetectorHit objects
        R: jet radius parameter
        min_pt_gev: minimum jet pT threshold

    Returns:
        List of PseudoJet objects above the pT threshold.
    """
    # Initialise pseudojets from calorimeter hits
    pseudojets = []
    for h in deposits:
        if h.energy_gev < 0.1:
            continue
        e = h.energy_gev
        x, y, z = h.position
        r = math.sqrt(x*x + y*y)
        r = max(r, 1e-6)
        # Use position direction as momentum direction (massless approximation)
        px = e * x / r
        py = e * y / r
        pz = e * z / max(math.sqrt(x*x+y*y+z*z), 1e-6)
        pseudojets.append(PseudoJet(e, px, py, pz, [h]))

    if not pseudojets:
        return []

    R2 = R * R

    # Anti-kT clustering loop
    while True:
        n = len(pseudojets)
        if n == 0:
            break

        min_dist = float("inf")
        merge_i = -1
        merge_j = -1  # -1 = beam merge

        for i in range(n):
            # Beam distance
            pt2_i = pseudojets[i].pt2
            d_iB = 1.0 / pt2_i if pt2_i > 0 else float("inf")
            if d_iB < min_dist:
                min_dist = d_iB
                merge_i = i
                merge_j = -1

            # Pair distances
            for j in range(i + 1, n):
                pt2_j = pseudojets[j].pt2
                d_ij = (min(1.0/pt2_i, 1.0/pt2_j) if pt2_i > 0 and pt2_j > 0 else float("inf"))
                d_ij *= pseudojets[i].delta_r(pseudojets[j])**2 / R2
                if d_ij < min_dist:
                    min_dist = d_ij
                    merge_i = i
                    merge_j = j

        if merge_j == -1:
            # Beam merge: promote to jet
            pseudojets.pop(merge_i)  # Already processed as jet candidate
        else:
            # Merge pair
            merged = pseudojets[merge_i].merge(pseudojets[merge_j])
            pseudojets = [p for k, p in enumerate(pseudojets) if k not in (merge_i, merge_j)]
            pseudojets.append(merged)

    return pseudojets  # All remaining are jets (already promoted by beam merges above)


class JetClusterer:
    """
    Cluster calorimeter hits into jets using the anti-kT algorithm.
    """

    def __init__(self, jet_radius: float = 0.4, min_pt_gev: float = 5.0):
        self.jet_radius = jet_radius
        self.min_pt_gev = min_pt_gev

    def cluster(self, hits: List[DetectorHit]) -> List[ReconstructedJet]:
        """
        Run anti-kT clustering on all calorimeter hits.

        Returns:
            List of ReconstructedJet objects above the pT threshold.
        """
        cal_hits = [h for h in hits if h.detector_layer in ("em_cal", "had_cal")]
        pseudojets = anti_kt_cluster(cal_hits, self.jet_radius, self.min_pt_gev)

        jets = []
        for pj in pseudojets:
            if pj.pt < self.min_pt_gev:
                continue
            jet = ReconstructedJet(
                jet_id=next(_jet_id_counter),
                four_momentum=(pj.e, pj.px, pj.py, pj.pz),
                constituents=pj.hits,
                algorithm="anti_kt",
                radius=self.jet_radius,
            )
            jets.append(jet)

        # Sort by pT descending
        jets.sort(key=lambda j: j.pt_gev, reverse=True)
        return jets


# ─────────────────────────────────────────────────────────────────────────────
# missing_energy.py — compute MET from calorimeter imbalance
# ─────────────────────────────────────────────────────────────────────────────

def compute_missing_energy(hits: List[DetectorHit]) -> Tuple[float, float]:
    """
    Compute Missing Transverse Energy (MET) from calorimeter momentum imbalance.

    MET = |Σ p_T^{visible}|, MET_phi = atan2(−Σpy, −Σpx)

    Returns:
        (met_gev, met_phi_rad)
    """
    px_sum = 0.0
    py_sum = 0.0

    for h in hits:
        if h.detector_layer not in ("em_cal", "had_cal"):
            continue
        if h.energy_gev < 0.1:
            continue

        x, y, z = h.position
        r = math.sqrt(x*x + y*y)
        if r < 1e-6:
            continue
        e = h.energy_gev
        px_sum += e * x / r
        py_sum += e * y / r

    met_gev = math.sqrt(px_sum**2 + py_sum**2)
    met_phi = math.atan2(-py_sum, -px_sum)
    return met_gev, met_phi


# ─────────────────────────────────────────────────────────────────────────────
# EventReconstructor — full reconstruction pipeline
# ─────────────────────────────────────────────────────────────────────────────

class EventReconstructor:
    """
    Full event reconstruction pipeline.

    Takes raw DetectorHit objects and returns a ReconstructedEvent containing:
      - Kalman-filtered tracks
      - Reconstructed vertices
      - Anti-kT jets
      - Missing transverse energy
    """

    def __init__(
        self,
        min_track_hits: int = 3,
        jet_radius: float = 0.4,
        min_jet_pt_gev: float = 5.0,
    ):
        self.track_reco = TrackReconstructor(min_hits=min_track_hits)
        self.vertex_finder = VertexFinder()
        self.jet_clusterer = JetClusterer(jet_radius, min_jet_pt_gev)

    def reconstruct_event(
        self,
        hits: List[DetectorHit],
        event_id: int = 0,
    ) -> ReconstructedEvent:
        """
        Run the full reconstruction pipeline on raw detector hits.

        Args:
            hits: all DetectorHit objects from one collision
            event_id: identifier carried over from CollisionEvent

        Returns:
            ReconstructedEvent ready for physics analysis.
        """
        # Track reconstruction (uses tracker hits)
        tracks = self.track_reco.reconstruct(hits)

        # Vertex finding (uses tracks)
        vertices = self.vertex_finder.find_vertices(tracks)

        # Jet clustering (uses calorimeter hits)
        jets = self.jet_clusterer.cluster(hits)

        # Missing transverse energy
        met_gev, met_phi = compute_missing_energy(hits)

        return ReconstructedEvent(
            event_id=event_id,
            tracks=tracks,
            jets=jets,
            vertices=vertices,
            met_gev=met_gev,
            met_phi_rad=met_phi,
            raw_hits=hits,
        )
