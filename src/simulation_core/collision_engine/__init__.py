"""
collision_engine — Monte Carlo collision simulation pipeline.

Subsystem responsibilities:
  1. collision_detector: find pairs of particles within interaction radius
  2. parton_distribution: sample quark/gluon momentum fractions (PDFs)
  3. scattering_engine: QCD 2→2 hard scattering
  4. particle_shower: DGLAP parton cascade
  5. hadronization: string fragmentation → observable hadrons
  6. particle_decay: unstable particle decay chains

Pipeline flow:
  beam particles → find_collisions → parton_sample → scatter →
  shower → hadronize → decay_all → final state particles
"""

from __future__ import annotations

import math
import random
import itertools

import numpy as np

from simulation_core.core_models.models import (
    ParticleState,
    CollisionEvent,
    Vec3,
    PARTICLE_PROPERTIES,
    C,
)
from simulation_core.physics_engine import (
    make_particle,
    new_particle_id,
    sqrt_s,
    invariant_mass_pair,
    speed_from_momentum_gev,
)

_event_id_counter = itertools.count(1)



def find_collisions(
    particles: list[ParticleState],
    interaction_radius_m: float = 0.05,
) -> list[tuple[ParticleState, ParticleState]]:
    """
    Identify all pairs of alive particles within the interaction radius
    that are converging (negative closing rate).

    Returns:
        List of (particle_A, particle_B) pairs eligible for collision.
    """
    alive = [p for p in particles if p.alive]
    pairs = []
    for i in range(len(alive)):
        for j in range(i + 1, len(alive)):
            a, b = alive[i], alive[j]
            # Separation vector
            dx = b.position[0] - a.position[0]
            dy = b.position[1] - a.position[1]
            dz = b.position[2] - a.position[2]
            sep = math.sqrt(dx*dx + dy*dy + dz*dz)

            if sep > interaction_radius_m:
                continue

            # Closing rate: v_rel · r̂  (negative = converging)
            va = a.velocity_ms
            vb = b.velocity_ms
            dvx = vb[0] - va[0]
            dvy = vb[1] - va[1]
            dvz = vb[2] - va[2]
            if sep > 0:
                closing = (dvx*dx + dvy*dy + dvz*dz) / sep
            else:
                closing = -1.0  # Treat overlapping particles as converging

            if closing < 0:
                pairs.append((a, b))

    return pairs



# Parton flavour labels with approximate valence/sea/gluon probabilities
_PARTON_TABLE = [
    ("u",       0.28),  # valence up
    ("d",       0.18),  # valence down
    ("gluon",   0.30),  # gluons (dominant at low x)
    ("anti_u",  0.07),
    ("anti_d",  0.07),
    ("s",       0.04),
    ("anti_s",  0.03),
    ("c",       0.02),
    ("anti_c",  0.01),
]
_PARTON_FLAVOURS  = [row[0] for row in _PARTON_TABLE]
_PARTON_WEIGHTS   = [row[1] for row in _PARTON_TABLE]
_PARTON_CUMULATIVE = []
_acc = 0.0
for w in _PARTON_WEIGHTS:
    _acc += w
    _PARTON_CUMULATIVE.append(_acc)
_PARTON_TOTAL = _acc


def sample_parton(rng: random.Random) -> tuple[str, float]:
    """
    Sample a parton flavour and momentum fraction x.

    x distribution: power-law p(x) ∝ x^{-α} (approximate CTEQ/MRST inspired).
    Valence quarks: peaked at x ≈ 0.2; gluons/sea: peaked at low x.

    Returns:
        (flavour, x) where x ∈ (0.01, 0.95)
    """
    # Flavour
    r = rng.random() * _PARTON_TOTAL
    flavour = _PARTON_FLAVOURS[-1]
    for i, cum in enumerate(_PARTON_CUMULATIVE):
        if r <= cum:
            flavour = _PARTON_FLAVOURS[i]
            break

    # Momentum fraction x via power-law sampling
    is_valence = flavour in ("u", "d")
    alpha = 1.5 if is_valence else 2.5
    x_min, x_max = 0.01, 0.95
    # Inverse CDF sampling for power law x^{-alpha}
    exp = 1.0 - alpha
    u = rng.random()
    x = (u * (x_max**exp - x_min**exp) + x_min**exp) ** (1.0 / exp)
    x = max(x_min, min(x_max, x))

    return flavour, x



def qcd_scatter(
    parton1: str,
    parton2: str,
    sqrt_s_hat_gev: float,
    rng: random.Random,
) -> list[tuple[str, float, float, float]]:
    """
    Simplified QCD 2→2 scattering.

    Returns a list of (flavour, energy_gev, theta_rad, phi_rad) for each output parton.
    Cross-section weights are approximate; full matrix element not required.
    """
    if sqrt_s_hat_gev < 0.5:
        return []

    # Determine process
    both_gluon = parton1 == "gluon" and parton2 == "gluon"
    one_gluon  = (parton1 == "gluon") != (parton2 == "gluon")
    is_qq_bar  = (parton1.startswith("anti_") != parton2.startswith("anti_")) and \
                  parton1.replace("anti_", "") == parton2.replace("anti_", "")

    if both_gluon:
        # gg → gg  (60%)  or  gg → qq̄  (40%)
        if rng.random() < 0.6:
            out_flavours = ["gluon", "gluon"]
        else:
            q = rng.choice(["u", "d", "s"])
            out_flavours = [q, "anti_" + q]
    elif one_gluon:
        # qg → qg (Compton-like)
        quark = parton1 if parton2 == "gluon" else parton2
        out_flavours = [quark, "gluon"]
    elif is_qq_bar:
        # qq̄ → gg  (30%)  or  qq̄ → qq̄  (70%)
        if rng.random() < 0.3:
            out_flavours = ["gluon", "gluon"]
        else:
            out_flavours = [parton1, parton2]
    else:
        # qq → qq
        out_flavours = [parton1, parton2]

    # Kinematics: split energy, sample scattering angle
    results = []
    e_each = sqrt_s_hat_gev / 2.0
    for flav in out_flavours:
        # Rutherford-inspired θ distribution: forward peaked
        cos_theta_max = 0.9999
        u = rng.random()
        cos_theta = 1.0 - (1.0 - cos_theta_max) * (u ** 0.3)  # forward-peaked
        cos_theta *= rng.choice([-1, 1])  # symmetrise
        cos_theta = max(-1.0, min(1.0, cos_theta))
        theta = math.acos(cos_theta)
        phi = rng.uniform(0, 2 * math.pi)
        energy = e_each * rng.uniform(0.7, 1.3)
        results.append((flav, energy, theta, phi))

    return results



def generate_shower(
    flavour: str,
    energy_gev: float,
    theta_rad: float,
    phi_rad: float,
    rng: random.Random,
    cutoff_gev: float = 1.0,
    max_depth: int = 6,
    alpha_s: float = 0.118,
) -> list[tuple[str, float, float, float]]:
    """
    Simplified DGLAP parton shower via recursive splitting.

    Each parton above the cutoff_gev may split into two daughters.
    The splitting probability is proportional to alpha_s.

    Returns:
        List of (flavour, energy_gev, theta_rad, phi_rad) for all shower partons.
    """
    # Queue: (flavour, energy, theta, phi, depth)
    queue = [(flavour, energy_gev, theta_rad, phi_rad, 0)]
    result = []

    while queue:
        flav, e, th, ph, depth = queue.pop(0)
        result.append((flav, e, th, ph))

        if depth >= max_depth or e < cutoff_gev:
            continue

        # Splitting probability ~ alpha_s × log(E/cutoff)
        p_split = min(0.9, alpha_s * math.log(max(1.01, e / cutoff_gev)))
        if rng.random() > p_split:
            continue

        # Momentum fraction z for the splitting
        z = rng.uniform(0.2, 0.8)

        # Angular opening
        delta_theta = rng.gauss(0.0, 0.1 / math.sqrt(e))  # collinear limit

        # Daughter flavours
        if flav == "gluon":
            if rng.random() < 0.5:
                f1, f2 = "gluon", "gluon"          # g → gg
            else:
                q = rng.choice(["u", "d", "s"])
                f1, f2 = q, "anti_" + q             # g → qq̄
        else:
            f1, f2 = flav, "gluon"                  # q → qg

        phi2 = ph + math.pi + rng.gauss(0.0, 0.05)
        queue.append((f1, e * z,       th + delta_theta, ph,   depth + 1))
        queue.append((f2, e * (1 - z), th - delta_theta, phi2, depth + 1))

    return result



# Simplified Lund string fragmentation: map parton flavours to hadron species
_HADRON_TABLE = {
    "u":     [("pi+", 0.45), ("pi0", 0.25), ("K+", 0.15), ("proton", 0.15)],
    "d":     [("pi-", 0.45), ("pi0", 0.25), ("K-", 0.15), ("proton", 0.15)],
    "s":     [("K+",  0.35), ("K-",  0.35), ("pi+", 0.15), ("pi-", 0.15)],
    "c":     [("K+",  0.5),  ("pi+", 0.3),  ("pi0", 0.2)],
    "b":     [("K+",  0.4),  ("pi+", 0.35), ("proton", 0.25)],
    "gluon": [("pi+", 0.3),  ("pi-", 0.3),  ("pi0", 0.2), ("K+", 0.1), ("K-", 0.1)],
}

def _hadron_from_parton(flavour: str, rng: random.Random) -> str:
    base = flavour.replace("anti_", "") if flavour.startswith("anti_") else flavour
    table = _HADRON_TABLE.get(base, _HADRON_TABLE["gluon"])
    r = rng.random()
    acc = 0.0
    for species, prob in table:
        acc += prob
        if r <= acc:
            return species
    return table[-1][0]


def hadronize(
    shower_partons: list[tuple[str, float, float, float]],
    vertex: Vec3,
    rng: random.Random,
    parent_id: int = None,
) -> list[ParticleState]:
    """
    Convert shower partons into observable hadrons.

    Args:
        shower_partons: list of (flavour, energy_gev, theta_rad, phi_rad)
        vertex: collision vertex position
        rng: random number generator
        parent_id: ID of the originating particle

    Returns:
        List of ParticleState objects (hadrons at the production vertex)
    """
    hadrons = []
    min_energy_gev = 0.15  # below pion mass — discard

    for flav, energy, theta, phi in shower_partons:
        if energy < min_energy_gev:
            continue

        species = _hadron_from_parton(flav, rng)
        props = PARTICLE_PROPERTIES.get(species, {"mass_gev": 0.14, "charge": 0})
        m = props["mass_gev"]

        # Compute 3-momentum from energy and angles
        p_mag = math.sqrt(max(0.0, energy**2 - m**2))
        sin_th = math.sin(theta)
        px = p_mag * sin_th * math.cos(phi)
        py = p_mag * sin_th * math.sin(phi)
        pz = p_mag * math.cos(theta)

        p = make_particle(species, vertex, (px, py, pz), parent_id=parent_id, generation=1)
        hadrons.append(p)

    return hadrons



# Decay channels: species → [(daughters tuple, branching ratio), ...]
_DECAY_TABLE = {
    "pi0":  [(("photon", "photon"), 0.99)],
    "K+":   [(("muon+", "neutrino"), 0.64), (("pi+", "pi0"), 0.21), (("pi+", "pi+", "pi-"), 0.06)],
    "K-":   [(("muon-", "neutrino"), 0.64), (("pi-", "pi0"), 0.21), (("pi-", "pi-", "pi+"), 0.06)],
    "muon-": [(("electron", "neutrino", "neutrino"), 1.0)],
    "muon+": [(("positron", "neutrino", "neutrino"), 1.0)],
    "W+":   [(("muon+",  "neutrino"), 0.11), (("electron", "neutrino"), 0.11), (("u", "d"), 0.68)],
    "W-":   [(("muon-",  "neutrino"), 0.11), (("electron", "neutrino"), 0.11), (("d", "u"), 0.68)],
    "Z0":   [(("muon-", "muon+"), 0.034), (("electron", "positron"), 0.034), (("u", "anti_u"), 0.30)],
}

STABLE_SPECIES = {"proton", "electron", "positron", "photon", "neutrino",
                  "pi+", "pi-", "antiproton"}


def _sample_decay_channel(species: str, rng: random.Random) -> tuple[str, ... | None]:
    """Sample a decay channel for the given species. Returns None if stable."""
    if species in STABLE_SPECIES:
        return None
    channels = _DECAY_TABLE.get(species)
    if not channels:
        return None  # Unknown unstable — treat as stable for now
    r = rng.random()
    acc = 0.0
    for daughters, br in channels:
        acc += br
        if r <= acc:
            return daughters
    return channels[-1][0]


def _isotropic_decay(
    parent: ParticleState,
    daughter_species: tuple[str, ...],
    rng: random.Random,
) -> list[ParticleState]:
    """
    Decay a parent into daughter particles with isotropic kinematics in the CM frame.
    Uses a simplified 2- or 3-body phase space.
    """
    n = len(daughter_species)
    if n == 0:
        return []

    parent_e = parent.energy_gev
    parent_m = parent.mass_gev
    daughters = []

    # Share energy equally with Gaussian smearing (simplified)
    energies = []
    remaining = parent_e
    for i in range(n):
        if i == n - 1:
            energies.append(remaining)
        else:
            frac = rng.uniform(0.2, 0.8) / (n - i)
            e = remaining * frac
            energies.append(e)
            remaining -= e

    for i, species in enumerate(daughter_species):
        props = PARTICLE_PROPERTIES.get(species, {"mass_gev": 0.0, "charge": 0})
        m = props["mass_gev"]
        e = max(m, energies[i])
        p_mag = math.sqrt(max(0.0, e**2 - m**2))

        # Isotropic direction in parent rest frame
        cos_theta = rng.uniform(-1.0, 1.0)
        sin_theta = math.sqrt(max(0.0, 1.0 - cos_theta**2))
        phi = rng.uniform(0.0, 2 * math.pi)
        px = p_mag * sin_theta * math.cos(phi)
        py = p_mag * sin_theta * math.sin(phi)
        pz = p_mag * cos_theta

        d = make_particle(species, parent.position, (px, py, pz),
                          parent_id=parent.id, generation=parent.generation + 1)
        daughters.append(d)

    return daughters


def decay_all(
    particles: list[ParticleState],
    rng: random.Random,
    max_depth: int = 8,
) -> list[ParticleState]:
    """
    Recursively decay all unstable particles until only stable ones remain.

    Returns:
        List of stable final-state ParticleState objects.
    """
    queue = list(particles)
    final = []
    depth = 0

    while queue and depth < max_depth:
        next_queue = []
        for p in queue:
            if not p.alive:
                final.append(p)
                continue
            channel = _sample_decay_channel(p.species, rng)
            if channel is None:
                final.append(p)  # Stable
            else:
                daughters = _isotropic_decay(p, channel, rng)
                if daughters:
                    next_queue.extend(daughters)
                    # Mark parent as dead
                else:
                    final.append(p)  # Couldn't decay, keep
        queue = next_queue
        depth += 1

    final.extend(queue)  # Anything remaining at max depth
    return final



class CollisionEngine:
    """
    Full Monte Carlo collision pipeline:
        find_collisions → parton_sample → scatter → shower → hadronize → decay

    Returns CollisionEvent objects for each hard scatter.
    """

    def __init__(
        self,
        interaction_radius_m: float = 0.05,
        seed: int = 42,
        cutoff_gev: float = 1.0,
    ):
        self.interaction_radius_m = interaction_radius_m
        self.cutoff_gev = cutoff_gev
        self._rng = random.Random(seed)

    def simulate_collision(self, particles: list[ParticleState]) -> list[CollisionEvent]:
        """
        Process all eligible collision pairs in a particle list.

        Returns:
            List of CollisionEvent objects (one per hard scatter).
        """
        pairs = find_collisions(particles, self.interaction_radius_m)
        events = []
        consumed = set()

        for p1, p2 in pairs:
            if p1.id in consumed or p2.id in consumed:
                continue

            event = self._process_single_collision(p1, p2)
            if event is not None:
                events.append(event)
                consumed.add(p1.id)
                consumed.add(p2.id)

        return events

    def _process_single_collision(
        self,
        p1: ParticleState,
        p2: ParticleState,
    ) -> CollisionEvent | None:
        """Run the full pipeline for a single pair."""
        # Interaction vertex = midpoint
        vertex = (
            (p1.position[0] + p2.position[0]) / 2,
            (p1.position[1] + p2.position[1]) / 2,
            (p1.position[2] + p2.position[2]) / 2,
        )

        s_gev = sqrt_s(p1, p2)
        if s_gev < 1.0:
            return None  # Below threshold

        # Sample partons
        flav1, x1 = sample_parton(self._rng)
        flav2, x2 = sample_parton(self._rng)
        sqrt_s_hat = s_gev * math.sqrt(x1 * x2)

        # Hard scatter
        scattered = qcd_scatter(flav1, flav2, sqrt_s_hat, self._rng)
        if not scattered:
            return None

        # Parton shower
        shower_partons = []
        for flav, energy, theta, phi in scattered:
            shower_partons.extend(
                generate_shower(flav, energy, theta, phi, self._rng, self.cutoff_gev)
            )

        # Hadronization
        hadrons = hadronize(shower_partons, vertex, self._rng, parent_id=p1.id)

        # Decay chain
        final_state = decay_all(hadrons, self._rng)

        return CollisionEvent(
            event_id=next(_event_id_counter),
            vertex=vertex,
            sqrt_s_gev=s_gev,
            incoming=(p1.killed(), p2.killed()),
            final_state=final_state,
            process=f"{flav1}+{flav2}→shower",
            parton_x1=x1,
            parton_x2=x2,
        )
