"""
models.py — Canonical shared data structures for the full simulation pipeline.

Design principles:
  • All models are frozen dataclasses — immutable after creation.
  • All 3-vectors are plain tuples (x, y, z) of floats for zero-dependency portability.
  • NumPy arrays are used only inside engine kernels, never in model fields.
  • Every model carries a minimal set of fields; derived quantities are computed on access.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# Type aliases
Vec3 = tuple[float, float, float]

# Physical constants (SI)
C = 299_792_458.0          # m/s
GEV_TO_J = 1.602_176_634e-10  # 1 GeV = 1e9 × e joules



PARTICLE_PROPERTIES: dict[str, dict] = {
    "proton":     {"mass_gev": 0.938272,  "charge": +1, "stable": True},
    "antiproton": {"mass_gev": 0.938272,  "charge": -1, "stable": True},
    "electron":   {"mass_gev": 0.000511,  "charge": -1, "stable": True},
    "positron":   {"mass_gev": 0.000511,  "charge": +1, "stable": True},
    "muon-":      {"mass_gev": 0.105658,  "charge": -1, "stable": False},
    "muon+":      {"mass_gev": 0.105658,  "charge": +1, "stable": False},
    "photon":     {"mass_gev": 0.0,       "charge":  0, "stable": True},
    "neutrino":   {"mass_gev": 0.0,       "charge":  0, "stable": True},
    "pi+":        {"mass_gev": 0.139570,  "charge": +1, "stable": False},
    "pi-":        {"mass_gev": 0.139570,  "charge": -1, "stable": False},
    "pi0":        {"mass_gev": 0.134977,  "charge":  0, "stable": False},
    "K+":         {"mass_gev": 0.493677,  "charge": +1, "stable": False},
    "K-":         {"mass_gev": 0.493677,  "charge": -1, "stable": False},
    "gluon":      {"mass_gev": 0.0,       "charge":  0, "stable": False},
    "u":          {"mass_gev": 0.0022,    "charge": +2/3, "stable": False},
    "d":          {"mass_gev": 0.0047,    "charge": -1/3, "stable": False},
    "s":          {"mass_gev": 0.096,     "charge": -1/3, "stable": False},
    "c":          {"mass_gev": 1.27,      "charge": +2/3, "stable": False},
    "b":          {"mass_gev": 4.18,      "charge": -1/3, "stable": False},
    "W+":         {"mass_gev": 80.377,    "charge": +1, "stable": False},
    "W-":         {"mass_gev": 80.377,    "charge": -1, "stable": False},
    "Z0":         {"mass_gev": 91.188,    "charge":  0, "stable": False},
    "higgs":      {"mass_gev": 125.10,    "charge":  0, "stable": False},
}



@dataclass(frozen=True)
class ParticleState:
    """
    Complete kinematic state of a single particle at one point in time.

    Momentum is stored in GeV/c; position in metres.
    All derived quantities (speed, gamma, etc.) are computed from these.
    """
    id: int                          # Unique particle identifier
    species: str                     # e.g. "proton", "electron", "pi+"
    position: Vec3                   # (x, y, z) metres
    momentum: Vec3                   # (px, py, pz) GeV/c
    mass_gev: float                  # Rest mass in GeV/c²
    charge: float                    # Electric charge in units of e
    alive: bool = True               # False = absorbed, decayed, or lost
    parent_id: int | None = None  # ID of creating particle (None = primary)
    generation: int = 0              # 0 = beam, 1 = collision product, 2+ = decay


    @property
    def p_mag(self) -> float:
        """Magnitude of 3-momentum |p| in GeV/c."""
        px, py, pz = self.momentum
        return math.sqrt(px*px + py*py + pz*pz)

    @property
    def energy_gev(self) -> float:
        """Total relativistic energy E = √(p²c² + m²c⁴) in GeV."""
        return math.sqrt(self.p_mag**2 + self.mass_gev**2)

    @property
    def kinetic_energy_gev(self) -> float:
        """Kinetic energy T = E − m in GeV."""
        return self.energy_gev - self.mass_gev

    @property
    def gamma(self) -> float:
        """Lorentz factor γ = E / (mc²)."""
        if self.mass_gev == 0.0:
            return float("inf")
        return self.energy_gev / self.mass_gev

    @property
    def beta(self) -> float:
        """Velocity as fraction of c: β = |p| / E."""
        if self.energy_gev == 0.0:
            return 0.0
        return self.p_mag / self.energy_gev

    @property
    def velocity_ms(self) -> Vec3:
        """3-velocity vector in m/s."""
        if self.energy_gev == 0.0:
            return (0.0, 0.0, 0.0)
        scale = C * self.p_mag / self.energy_gev / self.p_mag if self.p_mag > 0 else 0.0
        px, py, pz = self.momentum
        return (px * scale, py * scale, pz * scale)

    @property
    def pt_gev(self) -> float:
        """Transverse momentum pT = √(px² + py²) in GeV/c."""
        px, py, _ = self.momentum
        return math.sqrt(px*px + py*py)

    @property
    def eta(self) -> float:
        """Pseudorapidity η = −ln[tan(θ/2)]."""
        p = self.p_mag
        if p == 0.0:
            return 0.0
        _, _, pz = self.momentum
        cos_theta = pz / p
        cos_theta = max(-0.9999999, min(0.9999999, cos_theta))
        theta = math.acos(cos_theta)
        if theta <= 0.0:
            return float("inf")
        if theta >= math.pi:
            return float("-inf")
        return -math.log(math.tan(theta / 2.0))

    @property
    def phi_rad(self) -> float:
        """Azimuthal angle φ in radians."""
        px, py, _ = self.momentum
        return math.atan2(py, px)

    def with_position(self, pos: Vec3) -> "ParticleState":
        """Return a new ParticleState with updated position."""
        return ParticleState(
            id=self.id, species=self.species,
            position=pos, momentum=self.momentum,
            mass_gev=self.mass_gev, charge=self.charge,
            alive=self.alive, parent_id=self.parent_id,
            generation=self.generation,
        )

    def with_momentum(self, mom: Vec3) -> "ParticleState":
        """Return a new ParticleState with updated momentum."""
        return ParticleState(
            id=self.id, species=self.species,
            position=self.position, momentum=mom,
            mass_gev=self.mass_gev, charge=self.charge,
            alive=self.alive, parent_id=self.parent_id,
            generation=self.generation,
        )

    def killed(self) -> "ParticleState":
        """Return a copy of this particle with alive=False."""
        return ParticleState(
            id=self.id, species=self.species,
            position=self.position, momentum=self.momentum,
            mass_gev=self.mass_gev, charge=self.charge,
            alive=False, parent_id=self.parent_id,
            generation=self.generation,
        )

    def as_dict(self) -> dict:
        return {
            "id": self.id, "species": self.species,
            "position": self.position, "momentum": self.momentum,
            "mass_gev": self.mass_gev, "charge": self.charge,
            "energy_gev": self.energy_gev, "alive": self.alive,
            "parent_id": self.parent_id, "generation": self.generation,
        }



@dataclass(frozen=True)
class CollisionEvent:
    """
    Complete record of a single hard-scattering collision event.
    """
    event_id: int
    vertex: Vec3                           # Interaction point (metres)
    sqrt_s_gev: float                      # Centre-of-mass energy √s (GeV)
    incoming: tuple[ParticleState, ParticleState]  # The two colliding particles
    final_state: list[ParticleState]       # All post-collision particles
    process: str = "pp"                    # e.g. "pp", "gg→gg", "qq→qq"
    parton_x1: float = 0.0                 # Momentum fraction of parton 1
    parton_x2: float = 0.0                 # Momentum fraction of parton 2
    weight: float = 1.0                    # Monte Carlo event weight

    @property
    def charged_particles(self) -> list[ParticleState]:
        return [p for p in self.final_state if p.charge != 0]

    @property
    def neutral_particles(self) -> list[ParticleState]:
        return [p for p in self.final_state if p.charge == 0]

    @property
    def total_final_energy_gev(self) -> float:
        return sum(p.energy_gev for p in self.final_state)

    def as_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "vertex": self.vertex,
            "sqrt_s_gev": self.sqrt_s_gev,
            "process": self.process,
            "n_final_state": len(self.final_state),
            "parton_x1": self.parton_x1,
            "parton_x2": self.parton_x2,
            "weight": self.weight,
            "total_final_energy_gev": self.total_final_energy_gev,
        }



@dataclass(frozen=True)
class DetectorHit:
    """
    A single detector signal: one charged-particle crossing or energy deposit.
    """
    hit_id: int
    detector_layer: str      # e.g. "tracker_0", "em_cal", "had_cal", "muon_0"
    position: Vec3           # Global hit position in metres
    energy_gev: float        # Deposited energy in GeV (0 for tracker hits)
    time_ns: float           # Hit time in nanoseconds
    particle_id: int         # ID of the originating particle (truth info)
    smeared: bool = True     # Whether detector resolution was applied

    def as_dict(self) -> dict:
        return {
            "hit_id": self.hit_id,
            "detector_layer": self.detector_layer,
            "position": self.position,
            "energy_gev": self.energy_gev,
            "time_ns": self.time_ns,
            "particle_id": self.particle_id,
        }



@dataclass(frozen=True)
class ReconstructedTrack:
    """A charged particle track built from tracker hits by the Kalman filter."""
    track_id: int
    hits: list[DetectorHit]         # Ordered list of tracker hits
    momentum: Vec3                  # Reconstructed 3-momentum (GeV/c) at vertex
    charge: float                   # Reconstructed charge
    chi2_per_ndof: float            # Track fit quality
    n_hits: int = 0                 # Number of hits used

    @property
    def pt_gev(self) -> float:
        px, py, _ = self.momentum
        return math.sqrt(px*px + py*py)

    @property
    def p_mag(self) -> float:
        px, py, pz = self.momentum
        return math.sqrt(px*px + py*py + pz*pz)

    def as_dict(self) -> dict:
        return {
            "track_id": self.track_id,
            "momentum": self.momentum,
            "charge": self.charge,
            "pt_gev": self.pt_gev,
            "chi2_per_ndof": self.chi2_per_ndof,
            "n_hits": self.n_hits,
        }


@dataclass(frozen=True)
class ReconstructedJet:
    """A jet cluster built from calorimeter deposits by the anti-kT algorithm."""
    jet_id: int
    four_momentum: tuple[float, float, float, float]  # (E, px, py, pz) GeV
    constituents: list[DetectorHit]
    algorithm: str = "anti_kt"
    radius: float = 0.4

    @property
    def energy_gev(self) -> float:
        return self.four_momentum[0]

    @property
    def momentum(self) -> Vec3:
        _, px, py, pz = self.four_momentum
        return (px, py, pz)

    @property
    def pt_gev(self) -> float:
        _, px, py, _ = self.four_momentum
        return math.sqrt(px*px + py*py)

    @property
    def eta(self) -> float:
        _, px, py, pz = self.four_momentum
        p = math.sqrt(px*px + py*py + pz*pz)
        if p == 0:
            return 0.0
        cos_theta = pz / p
        cos_theta = max(-0.9999999, min(0.9999999, cos_theta))
        theta = math.acos(cos_theta)
        if theta <= 0 or theta >= math.pi:
            return 0.0
        return -math.log(math.tan(theta / 2.0))

    @property
    def phi_rad(self) -> float:
        _, px, py, _ = self.four_momentum
        return math.atan2(py, px)

    def mass_gev(self) -> float:
        e, px, py, pz = self.four_momentum
        m2 = e*e - px*px - py*py - pz*pz
        return math.sqrt(max(0.0, m2))

    def as_dict(self) -> dict:
        return {
            "jet_id": self.jet_id,
            "energy_gev": self.energy_gev,
            "pt_gev": self.pt_gev,
            "eta": self.eta,
            "phi_rad": self.phi_rad,
            "mass_gev": self.mass_gev(),
            "n_constituents": len(self.constituents),
            "algorithm": self.algorithm,
        }


@dataclass(frozen=True)
class ReconstructedVertex:
    """A primary or secondary interaction vertex found from tracks."""
    vertex_id: int
    position: Vec3
    tracks: list[ReconstructedTrack]
    chi2_per_ndof: float
    is_primary: bool = True

    def as_dict(self) -> dict:
        return {
            "vertex_id": self.vertex_id,
            "position": self.position,
            "n_tracks": len(self.tracks),
            "chi2_per_ndof": self.chi2_per_ndof,
            "is_primary": self.is_primary,
        }


@dataclass(frozen=True)
class ReconstructedEvent:
    """
    Fully reconstructed physics event — output of the reconstruction pipeline.
    This is the primary input to the analysis stage.
    """
    event_id: int
    tracks: list[ReconstructedTrack]
    jets: list[ReconstructedJet]
    vertices: list[ReconstructedVertex]
    met_gev: float                   # Missing transverse energy
    met_phi_rad: float               # MET azimuthal angle
    raw_hits: list[DetectorHit]      # All detector hits for reference

    @property
    def primary_vertex(self) -> ReconstructedVertex | None:
        for v in self.vertices:
            if v.is_primary:
                return v
        return self.vertices[0] if self.vertices else None

    @property
    def n_jets(self) -> int:
        return len(self.jets)

    @property
    def n_tracks(self) -> int:
        return len(self.tracks)

    @property
    def ht_gev(self) -> float:
        """Scalar sum of jet pT values."""
        return sum(j.pt_gev for j in self.jets)

    def as_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "n_tracks": self.n_tracks,
            "n_jets": self.n_jets,
            "n_vertices": len(self.vertices),
            "met_gev": self.met_gev,
            "met_phi_rad": self.met_phi_rad,
            "ht_gev": self.ht_gev,
        }



@dataclass(frozen=True)
class AnalysisResult:
    """
    Statistical physics analysis result for one or many events.
    """
    result_id: str
    analysis_type: str                     # e.g. "invariant_mass", "significance"
    value: float                           # Primary result value
    uncertainty: float                     # Statistical uncertainty (1σ)
    units: str                             # e.g. "GeV", "sigma", "pb"
    histogram_bins: list[float] | None = None  # Bin edges
    histogram_counts: list[float] | None = None  # Bin counts
    significance_sigma: float = 0.0
    metadata: dict = field(default_factory=dict)

    @property
    def is_discovery(self) -> bool:
        """5σ discovery threshold."""
        return self.significance_sigma >= 5.0

    @property
    def is_evidence(self) -> bool:
        """3σ evidence threshold."""
        return self.significance_sigma >= 3.0

    def as_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "analysis_type": self.analysis_type,
            "value": self.value,
            "uncertainty": self.uncertainty,
            "units": self.units,
            "significance_sigma": self.significance_sigma,
            "is_discovery": self.is_discovery,
        }



@dataclass(frozen=True)
class BeamParameters:
    """Configuration for the accelerator beam source."""
    species: str = "proton"
    energy_gev: float = 6500.0       # Kinetic energy per beam (LHC: 6500 GeV)
    n_particles: int = 10
    emittance_nm: float = 3.75       # Normalised transverse emittance
    bunch_spread_m: float = 0.016    # Transverse Gaussian σ
    longitudinal_spread_m: float = 0.076  # Longitudinal σ
    seed: int = 42


@dataclass(frozen=True)
class FieldPoint:
    """Electromagnetic field evaluated at a point in space."""
    position: Vec3
    electric_field: Vec3   # V/m
    magnetic_field: Vec3   # T


@dataclass(frozen=True)
class SimulationConfig:
    """Top-level configuration for one simulation run."""
    run_id: str = "run_001"
    n_events: int = 100
    beam: BeamParameters = field(default_factory=BeamParameters)
    dt_s: float = 1.0e-11            # Integration timestep
    max_steps: int = 500
    magnetic_field_t: float = 3.8    # Dipole field strength
    rf_voltage_v: float = 2.0e6      # RF cavity peak voltage
    interaction_radius_m: float = 0.05
    jet_radius: float = 0.4
    min_jet_pt_gev: float = 5.0
    random_seed: int = 42
