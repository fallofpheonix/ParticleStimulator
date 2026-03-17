"""
detector — Full ATLAS/CMS-style cylindrical detector simulation.

Subsystem responsibilities:
  • detector_geometry: layer radii, acceptance, containment checks
  • silicon_tracker: hit generation with spatial smearing for charged tracks
  • electromagnetic_calorimeter: EM shower energy deposits
  • hadronic_calorimeter: hadronic shower energy deposits
  • muon_chamber: muon track hits
  • energy_deposition: ionisation and shower model
  • sensor_digitization: apply resolution smearing, noise, threshold cuts
"""

from __future__ import annotations

import math
import random
import itertools

import numpy as np

from simulation_core.core_models.models import (
    ParticleState,
    CollisionEvent,
    DetectorHit,
    Vec3,
    PARTICLE_PROPERTIES,
)

_hit_id_counter = itertools.count(1)



class DetectorGeometry:
    """
    ATLAS/CMS-inspired cylindrical barrel geometry.

    Layers (inner → outer):
      Beam pipe          r = 0.024 m
      Tracker (IBL)      r = 0.033 m
      Tracker B-layer    r = 0.050 m
      Tracker Layer 1    r = 0.088 m
      Tracker Layer 2    r = 0.122 m
      EM Calorimeter     r = 1.50–1.97 m
      Hadronic Cal.      r = 2.28–4.25 m
      Muon Chambers      r = 4.60–10.0 m

    All lengths in metres.  η coverage: |η| < 2.5 for tracker, |η| < 4.9 for cal.
    """

    # (name, r_inner_m, r_outer_m, z_half_m, type)
    LAYERS = [
        ("beam_pipe",    0.000, 0.024, 10.0,  "pipe"),
        ("tracker_0",    0.030, 0.036,  3.5,  "tracker"),
        ("tracker_1",    0.048, 0.055,  3.5,  "tracker"),
        ("tracker_2",    0.086, 0.094,  3.5,  "tracker"),
        ("tracker_3",    0.120, 0.128,  3.5,  "tracker"),
        ("em_cal",       1.500, 1.970,  6.0,  "em_cal"),
        ("had_cal",      2.280, 4.250,  6.0,  "had_cal"),
        ("muon_0",       4.600, 5.000, 10.0,  "muon"),
        ("muon_1",       7.000, 7.500, 10.0,  "muon"),
        ("muon_2",       9.500, 10.00, 10.0,  "muon"),
    ]

    @classmethod
    def layer_for_radius(cls, r: float, z: float) -> str | None:
        """Return the detector layer name for a given (r, z) position."""
        for name, r_in, r_out, z_half, _ in cls.LAYERS:
            if r_in <= r <= r_out and abs(z) <= z_half:
                return name
        return None

    @classmethod
    def tracker_layers(cls) -> list[tuple[str, float, float, float]]:
        """Return all tracker layer definitions: (name, r_mid, r_in, r_out)."""
        return [(n, (ri+ro)/2, ri, ro) for n, ri, ro, zh, t in cls.LAYERS if t == "tracker"]

    @classmethod
    def is_in_acceptance(cls, particle: ParticleState) -> bool:
        """Check if a particle's direction is within detector acceptance."""
        return abs(particle.eta) < 4.9

    @classmethod
    def radial_distance(cls, pos: Vec3) -> float:
        x, y, _ = pos
        return math.sqrt(x*x + y*y)



# EM-interacting species (shower in EM cal)
EM_SPECIES = {"electron", "positron", "photon"}

# Hadronically interacting species (shower in had cal)
HAD_SPECIES = {"proton", "antiproton", "pi+", "pi-", "K+", "K-"}

# Muons penetrate to the muon chambers
MUON_SPECIES = {"muon-", "muon+"}


def em_shower_fraction(particle: ParticleState) -> float:
    """Fraction of particle energy deposited in EM calorimeter (0–1)."""
    if particle.species in EM_SPECIES:
        return 0.95 + 0.05 * math.tanh(particle.energy_gev - 1.0)
    if particle.species in HAD_SPECIES:
        return 0.15   # EM fraction in hadronic shower (pi0 component)
    return 0.0


def had_shower_fraction(particle: ParticleState) -> float:
    """Fraction of particle energy deposited in hadronic calorimeter (0–1)."""
    if particle.species in HAD_SPECIES:
        return 0.80
    return 0.0



def smear_position(position: Vec3, sigma_m: float, rng: random.Random) -> Vec3:
    """Apply Gaussian position smearing with σ = sigma_m."""
    x, y, z = position
    return (
        x + rng.gauss(0.0, sigma_m),
        y + rng.gauss(0.0, sigma_m),
        z + rng.gauss(0.0, sigma_m),
    )


def smear_energy(energy_gev: float, sigma_stochastic: float, rng: random.Random) -> float:
    """
    Apply calorimeter energy resolution: σ_E/E = σ_stochastic / √E ⊕ σ_noise.
    """
    sigma_noise = 0.003  # 3 MeV constant term
    sigma_rel = math.sqrt((sigma_stochastic / math.sqrt(max(energy_gev, 0.01)))**2 + sigma_noise**2)
    return max(0.0, energy_gev * (1.0 + rng.gauss(0.0, sigma_rel)))


def _extrapolate_to_radius(p: ParticleState, r_target: float) -> Vec3 | None:
    """Straight-line extrapolation from particle origin to cylindrical radius r_target."""
    p_vec = np.array(p.momentum, dtype=np.float64)
    p_mag = float(np.linalg.norm(p_vec))
    if p_mag == 0:
        return None
    p_hat = p_vec / p_mag
    origin = np.array(p.position, dtype=np.float64)
    ox, oy, oz = origin
    dx, dy, dz = p_hat
    a = dx*dx + dy*dy
    b = 2*(ox*dx + oy*dy)
    c = ox*ox + oy*oy - r_target**2
    disc = b*b - 4*a*c
    if a < 1e-15 or disc < 0:
        return None
    t = (-b + math.sqrt(max(0, disc))) / (2*a)
    if t < 0:
        t = (-b - math.sqrt(max(0, disc))) / (2*a)
    if t < 0:
        return None
    pos = origin + t * p_hat
    return (float(pos[0]), float(pos[1]), float(pos[2]))



class SiliconTracker:
    """
    Silicon pixel and strip tracker.

    Generates a DetectorHit each time a charged particle passes through a
    tracker layer. Position is smeared with 10 μm resolution.
    """

    POSITION_RESOLUTION_M = 10.0e-6  # 10 μm

    def simulate(
        self,
        particles: list[ParticleState],
        rng: random.Random,
        seen: set = None,
    ) -> list[DetectorHit]:
        """
        Generate tracker hits for all charged particles.

        Propagates each particle radially outward through each tracker layer
        (simplified straight-line extrapolation from the IP).

        Returns:
            List of DetectorHit objects.
        """
        hits = []
        if seen is None:
            seen = set()

        layers = DetectorGeometry.tracker_layers()

        for p in particles:
            if not p.alive or p.charge == 0:
                continue
            if not DetectorGeometry.is_in_acceptance(p):
                continue

            # Extrapolate along momentum direction to each tracker layer radius
            p_vec = np.array(p.momentum, dtype=np.float64)
            p_mag = float(np.linalg.norm(p_vec))
            if p_mag == 0:
                continue
            p_hat = p_vec / p_mag

            # Transverse component determines how far the particle goes radially
            pt = p.pt_gev
            if pt < 0.1:   # Below 100 MeV pT — won't reach outer layers
                continue

            # Starting point: interaction vertex ≈ origin
            origin = np.array(p.position, dtype=np.float64)

            for layer_name, r_mid, r_in, r_out in layers:
                # Parametric intersection: find t where |origin + t*p_hat|_xy = r_mid
                ox, oy, oz = origin
                dx, dy, dz = p_hat
                # Solve: (ox + t*dx)² + (oy + t*dy)² = r_mid²
                a = dx*dx + dy*dy
                b = 2*(ox*dx + oy*dy)
                c = ox*ox + oy*oy - r_mid**2
                disc = b*b - 4*a*c
                if a < 1e-15 or disc < 0:
                    continue

                t = (-b + math.sqrt(disc)) / (2*a)
                if t < 0:
                    t = (-b - math.sqrt(disc)) / (2*a)
                if t < 0:
                    continue

                hit_pos_raw = origin + t * p_hat
                hit_pos: Vec3 = tuple(float(v) for v in hit_pos_raw)

                # Check z acceptance
                if abs(hit_pos[2]) > 3.5:
                    continue

                key = (p.id, layer_name)
                if key in seen:
                    continue
                seen.add(key)

                # Apply position smearing
                hit_pos_smeared = smear_position(hit_pos, self.POSITION_RESOLUTION_M, rng)

                hit = DetectorHit(
                    hit_id=next(_hit_id_counter),
                    detector_layer=layer_name,
                    position=hit_pos_smeared,
                    energy_gev=0.0,   # Tracker: position measurement only
                    time_ns=rng.gauss(t / 3e8 * 1e9, 0.2),  # ~200 ps resolution
                    particle_id=p.id,
                    smeared=True,
                )
                hits.append(hit)

        return hits



class EMCalorimeter:
    """
    Electromagnetic lead-LAr or PbWO₄ calorimeter.

    Energy resolution: σ_E/E = 10%/√E ⊕ 0.7% (ATLAS-like).
    Segmented in η-φ with cell size Δη × Δφ ≈ 0.025 × 0.025.
    """

    STOCHASTIC_TERM = 0.10   # 10%/√E
    R_MID_M = 1.735          # Mid-radius of EM calorimeter

    def simulate(
        self,
        particles: list[ParticleState],
        rng: random.Random,
    ) -> list[DetectorHit]:
        hits = []
        for p in particles:
            if not p.alive:
                continue
            frac = em_shower_fraction(p)
            if frac < 0.01:
                continue
            if not DetectorGeometry.is_in_acceptance(p):
                continue

            energy_deposited = p.energy_gev * frac
            energy_smeared = smear_energy(energy_deposited, self.STOCHASTIC_TERM, rng)

            # Extrapolate to EM cal radius
            pos = _extrapolate_to_radius(p, self.R_MID_M)
            if pos is None:
                continue

            hit = DetectorHit(
                hit_id=next(_hit_id_counter),
                detector_layer="em_cal",
                position=pos,
                energy_gev=energy_smeared,
                time_ns=rng.gauss(0.0, 0.3),
                particle_id=p.id,
                smeared=True,
            )
            hits.append(hit)
        return hits


class HadronicCalorimeter:
    """
    Hadronic iron-scintillator or copper-LAr calorimeter.

    Energy resolution: σ_E/E = 50%/√E ⊕ 3%.
    """

    STOCHASTIC_TERM = 0.50   # 50%/√E
    R_MID_M = 3.265          # Mid-radius

    def simulate(
        self,
        particles: list[ParticleState],
        rng: random.Random,
    ) -> list[DetectorHit]:
        hits = []
        for p in particles:
            if not p.alive:
                continue
            frac = had_shower_fraction(p)
            if frac < 0.01:
                continue
            if not DetectorGeometry.is_in_acceptance(p):
                continue

            energy_deposited = p.energy_gev * frac
            energy_smeared = smear_energy(energy_deposited, self.STOCHASTIC_TERM, rng)

            pos = _extrapolate_to_radius(p, self.R_MID_M)
            if pos is None:
                continue

            hit = DetectorHit(
                hit_id=next(_hit_id_counter),
                detector_layer="had_cal",
                position=pos,
                energy_gev=energy_smeared,
                time_ns=rng.gauss(0.0, 1.0),
                particle_id=p.id,
                smeared=True,
            )
            hits.append(hit)
        return hits


class MuonChamber:
    """
    Muon drift tube and RPC chambers.

    Position resolution: ~100 μm per station.
    Three concentric stations at r ≈ 4.8 m, 7.25 m, 9.75 m.
    """

    STATIONS = [
        ("muon_0", 4.800),
        ("muon_1", 7.250),
        ("muon_2", 9.750),
    ]
    POSITION_RESOLUTION_M = 100.0e-6  # 100 μm

    def simulate(
        self,
        particles: list[ParticleState],
        rng: random.Random,
    ) -> list[DetectorHit]:
        hits = []
        for p in particles:
            if not p.alive or p.species not in MUON_SPECIES:
                continue
            if not DetectorGeometry.is_in_acceptance(p):
                continue

            for station_name, r_station in self.STATIONS:
                pos = _extrapolate_to_radius(p, r_station)
                if pos is None:
                    continue
                if abs(pos[2]) > 10.0:
                    continue

                pos_smeared = smear_position(pos, self.POSITION_RESOLUTION_M, rng)
                hit = DetectorHit(
                    hit_id=next(_hit_id_counter),
                    detector_layer=station_name,
                    position=pos_smeared,
                    energy_gev=0.0,
                    time_ns=rng.gauss(0.0, 2.0),
                    particle_id=p.id,
                    smeared=True,
                )
                hits.append(hit)

        return hits


class DetectorSimulator:
    """
    Full detector simulation pipeline.

    Takes a list of final-state particles (from the collision engine) and
    returns all raw detector hits from tracker, calorimeters, and muon chambers.
    """

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)
        self.tracker = SiliconTracker()
        self.em_cal = EMCalorimeter()
        self.had_cal = HadronicCalorimeter()
        self.muon = MuonChamber()

    def simulate_detector(
        self,
        particles: list[ParticleState],
    ) -> list[DetectorHit]:
        """
        Simulate full detector response for a list of final-state particles.

        Returns:
            All DetectorHit objects from all sub-detectors combined.
        """
        seen_tracker = set()
        tracker_hits = self.tracker.simulate(particles, self._rng, seen_tracker)
        em_hits      = self.em_cal.simulate(particles, self._rng)
        had_hits     = self.had_cal.simulate(particles, self._rng)
        muon_hits    = self.muon.simulate(particles, self._rng)
        return tracker_hits + em_hits + had_hits + muon_hits
