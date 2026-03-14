from __future__ import annotations

from dataclasses import dataclass
import json
import math
import random

from accelerator.beamline import Beamline
from accelerator.magnets import DipoleMagnet, QuadrupoleMagnet
from accelerator.rf_cavity import RFCavity
from accelerator.vacuum_chamber import VacuumChamber
from core.constants import GEV_TO_J, PARTICLE_DB, SPEED_OF_LIGHT_M_S
from core.particle import Particle
from core.vector import Vector3
from simulation.engine import SimulationEngine, SimulationResult
from visualization.ui_dashboard import dashboard_metrics


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _round(value: float, digits: int = 6) -> float:
    return round(value, digits)


@dataclass(slots=True)
class SimulationRequest:
    beam_energy_gev: float = 6500.0
    magnetic_field_t: float = 3.5
    rf_field_v_m: float = 1.5e5
    quadrupole_gradient_t_per_m: float = 0.08
    beam_particles_per_side: int = 6
    beam_spread_m: float = 0.018
    longitudinal_spacing_m: float = 0.008
    interaction_radius_m: float = 0.06
    aperture_radius_m: float = 1.5
    chamber_half_length_m: float = 2.0
    steps: int = 160
    seed: int = 7

    @classmethod
    def from_dict(cls, payload: dict[str, object] | None) -> "SimulationRequest":
        source = payload or {}
        defaults = cls()
        return cls(
            beam_energy_gev=_clamp(float(source.get("beam_energy_gev", defaults.beam_energy_gev)), 1.0, 7_000.0),
            magnetic_field_t=_clamp(float(source.get("magnetic_field_t", defaults.magnetic_field_t)), 0.0, 8.0),
            rf_field_v_m=_clamp(float(source.get("rf_field_v_m", defaults.rf_field_v_m)), 0.0, 8.0e5),
            quadrupole_gradient_t_per_m=_clamp(
                float(source.get("quadrupole_gradient_t_per_m", defaults.quadrupole_gradient_t_per_m)),
                0.0,
                1.0,
            ),
            beam_particles_per_side=int(
                _clamp(float(source.get("beam_particles_per_side", defaults.beam_particles_per_side)), 2, 16)
            ),
            beam_spread_m=_clamp(float(source.get("beam_spread_m", defaults.beam_spread_m)), 0.002, 0.08),
            longitudinal_spacing_m=_clamp(
                float(source.get("longitudinal_spacing_m", defaults.longitudinal_spacing_m)),
                0.002,
                0.05,
            ),
            interaction_radius_m=_clamp(float(source.get("interaction_radius_m", defaults.interaction_radius_m)), 0.01, 0.12),
            aperture_radius_m=_clamp(float(source.get("aperture_radius_m", defaults.aperture_radius_m)), 0.1, 4.0),
            chamber_half_length_m=_clamp(
                float(source.get("chamber_half_length_m", defaults.chamber_half_length_m)),
                0.5,
                6.0,
            ),
            steps=int(_clamp(float(source.get("steps", defaults.steps)), 10, 400)),
            seed=int(float(source.get("seed", defaults.seed))),
        )


def _speed_from_kinetic_energy(species: str, kinetic_energy_gev: float) -> float:
    mass_kg = PARTICLE_DB[species].mass_kg
    gamma = 1.0 + ((kinetic_energy_gev * GEV_TO_J) / (mass_kg * (SPEED_OF_LIGHT_M_S ** 2)))
    if gamma <= 1.0:
        return 0.0
    beta_squared = 1.0 - (1.0 / (gamma * gamma))
    return SPEED_OF_LIGHT_M_S * math.sqrt(max(0.0, beta_squared))


def _build_beamline(config: SimulationRequest) -> Beamline:
    return Beamline(
        dipole=DipoleMagnet(config.magnetic_field_t),
        quadrupole=QuadrupoleMagnet(config.quadrupole_gradient_t_per_m),
        rf_cavity=RFCavity(
            center=Vector3(0.0, 0.0, 0.0),
            half_width_m=0.15,
            electric_field_v_m=config.rf_field_v_m,
        ),
        vacuum_chamber=VacuumChamber(
            aperture_radius_m=config.aperture_radius_m,
            half_length_m=config.chamber_half_length_m,
        ),
        interaction_radius_m=config.interaction_radius_m,
    )


def build_initial_particles(config: SimulationRequest) -> list[Particle]:
    rng = random.Random(config.seed)
    speed = _speed_from_kinetic_energy("proton", config.beam_energy_gev)
    base_x = min(0.5 * config.interaction_radius_m, 0.045)
    particles: list[Particle] = []

    for beam_sign in (-1.0, 1.0):
        x = base_x * beam_sign
        velocity = Vector3(-speed, 0.0, 0.0) if beam_sign > 0.0 else Vector3(speed, 0.0, 0.0)
        for index in range(config.beam_particles_per_side):
            offset_center = (index - ((config.beam_particles_per_side - 1) * 0.5)) * config.longitudinal_spacing_m
            y = offset_center + rng.uniform(-config.beam_spread_m, config.beam_spread_m)
            z = rng.uniform(-0.35, 0.35) * config.beam_spread_m
            particles.append(
                Particle(
                    species="proton",
                    position=Vector3(x, y, z),
                    velocity=velocity,
                )
            )
    return particles


def _serialize_vector(vector: Vector3) -> dict[str, float]:
    return {"x": _round(vector.x), "y": _round(vector.y), "z": _round(vector.z)}


def _serialize_particle(particle: Particle) -> dict[str, object]:
    return {
        "particle_id": particle.particle_id,
        "species": particle.species,
        "alive": particle.alive,
        "charge_c": _round(particle.charge_c or 0.0, 12),
        "position": _serialize_vector(particle.position),
        "velocity": _serialize_vector(particle.velocity),
        "speed_m_s": _round(particle.speed(), 3),
        "gamma": _round(particle.gamma(), 6),
        "kinetic_energy_gev": _round(particle.kinetic_energy_j() / GEV_TO_J, 6),
    }


def _histogram(values: list[float], bin_count: int, lower: float, upper: float) -> list[dict[str, float]]:
    width = (upper - lower) / bin_count
    counts = [0 for _ in range(bin_count)]
    for value in values:
        if value < lower or value > upper:
            continue
        index = min(bin_count - 1, int((value - lower) / width))
        counts[index] += 1
    return [
        {
            "label": _round(lower + (index * width), 2),
            "count": counts[index],
        }
        for index in range(bin_count)
    ]


def _timeline_records(result: SimulationResult) -> list[dict[str, object]]:
    records = json.loads(result.event_log_json)
    records.sort(key=lambda item: (float(item.get("time_s", 0.0)), str(item.get("type", ""))))
    return records


def _aggregate_calorimeter(result: SimulationResult) -> list[dict[str, float]]:
    bins = [0.0 for _ in range(result.calorimeter_hits[0].phi_bin + 1)] if result.calorimeter_hits else []
    for hit in result.calorimeter_hits:
        if hit.phi_bin >= len(bins):
            bins.extend([0.0] * ((hit.phi_bin + 1) - len(bins)))
        bins[hit.phi_bin] += hit.deposited_energy_gev
    return [{"phi_bin": index, "energy_gev": _round(value, 6)} for index, value in enumerate(bins)]


def _summaries(result: SimulationResult) -> dict[str, object]:
    invariant_masses = [event.invariant_mass_gev for event in result.collisions]
    active_particles = [particle for particle in result.final_particles if particle.alive]
    species_counts: dict[str, int] = {}
    for particle in result.final_particles:
        species_counts[particle.species] = species_counts.get(particle.species, 0) + 1

    return {
        "metrics": dashboard_metrics(result),
        "active_particles": len(active_particles),
        "mean_invariant_mass_gev": _round(sum(invariant_masses) / len(invariant_masses), 6) if invariant_masses else 0.0,
        "max_invariant_mass_gev": _round(max(invariant_masses), 6) if invariant_masses else 0.0,
        "species_counts": species_counts,
        "mass_histogram": _histogram(invariant_masses, bin_count=10, lower=0.0, upper=max(1.0, max(invariant_masses, default=1.0))),
    }


def simulate_payload(config_dict: dict[str, object] | None = None) -> dict[str, object]:
    config = SimulationRequest.from_dict(config_dict)
    engine = SimulationEngine(beamline=_build_beamline(config))
    initial_particles = build_initial_particles(config)
    result = engine.run(initial_particles, steps=config.steps)

    collisions = [
        {
            "event_id": event.event_id,
            "time_s": _round(event.time_s, 12),
            "position": _serialize_vector(event.position),
            "incoming_ids": list(event.incoming_ids),
            "product_ids": [particle.particle_id for particle in event.products],
            "product_species": [particle.species for particle in event.products],
            "invariant_mass_gev": _round(event.invariant_mass_gev, 6),
        }
        for event in result.collisions
    ]

    tracker_hits = [
        {
            "particle_id": hit.particle_id,
            "layer_index": hit.layer_index,
            "position": _serialize_vector(hit.position),
            "time_s": _round(hit.time_s, 12),
        }
        for hit in result.tracker_hits
    ]

    calorimeter_hits = [
        {
            "particle_id": hit.particle_id,
            "phi_bin": hit.phi_bin,
            "deposited_energy_gev": _round(hit.deposited_energy_gev, 6),
            "time_s": _round(hit.time_s, 12),
        }
        for hit in result.calorimeter_hits
    ]

    return {
        "config": {
            "beam_energy_gev": config.beam_energy_gev,
            "magnetic_field_t": config.magnetic_field_t,
            "rf_field_v_m": config.rf_field_v_m,
            "quadrupole_gradient_t_per_m": config.quadrupole_gradient_t_per_m,
            "beam_particles_per_side": config.beam_particles_per_side,
            "beam_spread_m": config.beam_spread_m,
            "longitudinal_spacing_m": config.longitudinal_spacing_m,
            "interaction_radius_m": config.interaction_radius_m,
            "steps": config.steps,
            "seed": config.seed,
        },
        "summary": _summaries(result),
        "initial_particles": [_serialize_particle(particle) for particle in initial_particles],
        "final_particles": [_serialize_particle(particle) for particle in result.final_particles],
        "collisions": collisions,
        "tracker_hits": tracker_hits,
        "calorimeter_hits": calorimeter_hits,
        "calorimeter_phi_totals": _aggregate_calorimeter(result),
        "timeline": _timeline_records(result),
    }
