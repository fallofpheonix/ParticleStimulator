from __future__ import annotations

from dataclasses import dataclass
import math

from src.simulation_core import BeamParameters, SimulationConfig, SimulationController
from src.simulation_core.core_models import AnalysisResult, CollisionEvent, DetectorHit, ParticleState, ReconstructedEvent
from src.web.event_stream import event_broker


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _round(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


@dataclass(slots=True)
class SimulationRequest:
    beam_energy_gev: float = 6500.0
    beam_intensity: float = 0.82
    magnetic_field_t: float = 3.5
    rf_field_v_m: float = 1.5e5
    quadrupole_gradient_t_per_m: float = 0.08
    beam_particles_per_side: int = 6
    beam_spread_m: float = 0.018
    longitudinal_spacing_m: float = 0.008
    interaction_radius_m: float = 0.06
    event_probability: float = 0.78
    aperture_radius_m: float = 1.5
    chamber_half_length_m: float = 2.0
    steps: int = 160
    seed: int = 7

    @classmethod
    def from_dict(cls, payload: dict[str, object] | None) -> "SimulationRequest":
        source = payload or {}
        defaults = cls()
        beam_energy = source.get("beam_energy_gev", source.get("beamEnergy", defaults.beam_energy_gev))
        beam_intensity = source.get("beam_intensity", source.get("beamIntensity", defaults.beam_intensity))
        magnetic_field = source.get("magnetic_field_t", source.get("magneticField", defaults.magnetic_field_t))
        particle_count = source.get("beam_particles_per_side", source.get("particleCount", defaults.beam_particles_per_side))
        beam_particles_per_side = float(particle_count)
        if "particleCount" in source and "beam_particles_per_side" not in source:
            beam_particles_per_side = max(2.0, beam_particles_per_side / 2.0)
        event_probability = source.get("event_probability", source.get("eventProbability", defaults.event_probability))
        aperture_radius = source.get("aperture_radius_m", source.get("apertureRadius", defaults.aperture_radius_m))
        simulation_steps = source.get("steps", source.get("simulationSteps", defaults.steps))
        return cls(
            beam_energy_gev=_clamp(float(beam_energy), 1.0, 7000.0),
            beam_intensity=_clamp(float(beam_intensity), 0.1, 1.0),
            magnetic_field_t=_clamp(float(magnetic_field), 0.0, 8.0),
            rf_field_v_m=_clamp(float(source.get("rf_field_v_m", defaults.rf_field_v_m)), 0.0, 8.0e6),
            quadrupole_gradient_t_per_m=_clamp(
                float(source.get("quadrupole_gradient_t_per_m", defaults.quadrupole_gradient_t_per_m)),
                0.0,
                1.0,
            ),
            beam_particles_per_side=int(_clamp(beam_particles_per_side, 2, 32)),
            beam_spread_m=_clamp(float(source.get("beam_spread_m", defaults.beam_spread_m)), 0.002, 0.08),
            longitudinal_spacing_m=_clamp(
                float(source.get("longitudinal_spacing_m", defaults.longitudinal_spacing_m)),
                0.002,
                0.05,
            ),
            interaction_radius_m=_clamp(float(source.get("interaction_radius_m", defaults.interaction_radius_m)), 0.01, 0.12),
            event_probability=_clamp(float(event_probability), 0.05, 1.0),
            aperture_radius_m=_clamp(float(aperture_radius), 0.1, 4.0),
            chamber_half_length_m=_clamp(
                float(source.get("chamber_half_length_m", defaults.chamber_half_length_m)),
                0.5,
                6.0,
            ),
            steps=int(_clamp(float(simulation_steps), 10, 400)),
            seed=int(float(source.get("seed", defaults.seed))),
        )


def _serialize_vec3(vector: tuple[float, float, float]) -> dict[str, float]:
    return {"x": _round(vector[0]), "y": _round(vector[1]), "z": _round(vector[2])}


def _velocity_components(particle: ParticleState) -> tuple[float, float, float]:
    return tuple(float(component) for component in particle.velocity_ms)


def _serialize_particle(particle: ParticleState) -> dict[str, object]:
    velocity = _velocity_components(particle)
    return {
        "particle_id": particle.id,
        "species": particle.species,
        "alive": particle.alive,
        "charge_c": _round(particle.charge, 12),
        "position": _serialize_vec3(particle.position),
        "velocity": _serialize_vec3(velocity),
        "speed_m_s": _round(math.sqrt(sum(component * component for component in velocity)), 3),
        "gamma": _round(particle.gamma, 6),
        "kinetic_energy_gev": _round(particle.kinetic_energy_gev, 6),
    }


def _config_to_pipeline(request: SimulationRequest) -> SimulationConfig:
    n_events = max(1, min(6, int(round(request.event_probability * 4.0))))
    transport_steps = max(8, min(request.steps, 12))
    return SimulationConfig(
        run_id=f"run_{request.seed}",
        n_events=n_events,
        beam=BeamParameters(
            species="proton",
            energy_gev=request.beam_energy_gev,
            n_particles=request.beam_particles_per_side,
            bunch_spread_m=request.beam_spread_m,
            longitudinal_spread_m=request.longitudinal_spacing_m * max(1, request.beam_particles_per_side),
            seed=request.seed,
        ),
        dt_s=1.0e-11,
        max_steps=transport_steps,
        magnetic_field_t=request.magnetic_field_t,
        rf_voltage_v=request.rf_field_v_m,
        interaction_radius_m=request.interaction_radius_m * (0.5 + (0.5 * request.event_probability)),
        jet_radius=0.4,
        min_jet_pt_gev=5.0,
        random_seed=request.seed,
    )


def _collect_final_particles(collisions: list[CollisionEvent]) -> list[ParticleState]:
    final_particles: dict[int, ParticleState] = {}
    for collision in collisions:
        for particle in collision.final_state:
            final_particles[particle.id] = particle
    return list(final_particles.values())


def _event_time_s(index: int) -> float:
    return index * 1.0e-9


def _serialize_collision(index: int, collision: CollisionEvent) -> dict[str, object]:
    return {
        "event_id": collision.event_id,
        "time_s": _round(_event_time_s(index), 12),
        "position": _serialize_vec3(collision.vertex),
        "incoming_ids": [particle.id for particle in collision.incoming],
        "product_ids": [particle.id for particle in collision.final_state],
        "product_species": [particle.species for particle in collision.final_state],
        "invariant_mass_gev": _round(collision.sqrt_s_gev, 6),
        "process": collision.process,
        "weight": _round(collision.weight, 6),
    }


def _tracker_layer_index(layer_name: str) -> int:
    if "_" not in layer_name:
        return 0
    suffix = layer_name.rsplit("_", 1)[-1]
    return int(suffix) if suffix.isdigit() else 0


def _phi_bin(position: tuple[float, float, float], bins: int = 24) -> int:
    phi = math.atan2(position[1], position[0])
    normalized = (phi + math.pi) / (2.0 * math.pi)
    return min(bins - 1, max(0, int(normalized * bins)))


def _serialize_tracker_hits(detector_hits: list[DetectorHit]) -> list[dict[str, object]]:
    tracker_hits: list[dict[str, object]] = []
    for hit in detector_hits:
        if not hit.detector_layer.startswith("tracker"):
            continue
        tracker_hits.append(
            {
                "particle_id": hit.particle_id,
                "layer_index": _tracker_layer_index(hit.detector_layer),
                "position": _serialize_vec3(hit.position),
                "time_s": _round(hit.time_ns * 1.0e-9, 12),
            }
        )
    return tracker_hits


def _serialize_calorimeter_hits(detector_hits: list[DetectorHit]) -> list[dict[str, object]]:
    calorimeter_hits: list[dict[str, object]] = []
    for hit in detector_hits:
        if hit.detector_layer not in {"em_cal", "had_cal"}:
            continue
        calorimeter_hits.append(
            {
                "particle_id": hit.particle_id,
                "phi_bin": _phi_bin(hit.position),
                "deposited_energy_gev": _round(hit.energy_gev, 6),
                "time_s": _round(hit.time_ns * 1.0e-9, 12),
            }
        )
    return calorimeter_hits


def _serialize_detector_hits(
    tracker_hits: list[dict[str, object]],
    calorimeter_hits: list[dict[str, object]],
) -> list[dict[str, object]]:
    return [
        *[
            {
                "layer": "tracker",
                "particle_id": hit["particle_id"],
                "time_s": hit["time_s"],
                "position": hit["position"],
            }
            for hit in tracker_hits
        ],
        *[
            {
                "layer": "calorimeter",
                "particle_id": hit["particle_id"],
                "time_s": hit["time_s"],
                "energy_gev": hit["deposited_energy_gev"],
                "phi_bin": hit["phi_bin"],
            }
            for hit in calorimeter_hits
        ],
    ]


def _serialize_particle_tracks(final_particles: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "particle_id": particle["particle_id"],
            "type": particle["species"],
            "position": particle["position"],
            "momentum": particle["velocity"],
            "kinetic_energy_gev": particle["kinetic_energy_gev"],
        }
        for particle in final_particles
    ]


def _build_mass_histogram(results: list[AnalysisResult]) -> list[dict[str, float]]:
    for result in results:
        if not result.histogram_bins or not result.histogram_counts:
            continue
        return [
            {"label": _round(bin_center, 2), "count": int(count)}
            for bin_center, count in zip(result.histogram_bins, result.histogram_counts)
        ]
    return []


def _summary(
    output,
    collisions: list[dict[str, object]],
    final_particles: list[ParticleState],
    analysis_results: list[AnalysisResult],
) -> dict[str, object]:
    species_counts: dict[str, int] = {}
    for particle in final_particles:
        species_counts[particle.species] = species_counts.get(particle.species, 0) + 1

    invariant_masses = [float(collision["invariant_mass_gev"]) for collision in collisions]
    return {
        "metrics": {
            "runtime_s": _round(output.total_duration_s, 6),
            "stage_metrics": output.summary().get("stage_metrics", []),
            "n_beam_particles": len(output.beam_particles),
            "n_collisions": len(output.collision_events),
            "n_detector_hits": len(output.detector_hits),
            "n_reco_events": len(output.reco_events),
        },
        "active_particles": sum(1 for particle in final_particles if particle.alive),
        "mean_invariant_mass_gev": _round(sum(invariant_masses) / len(invariant_masses), 6) if invariant_masses else 0.0,
        "max_invariant_mass_gev": _round(max(invariant_masses), 6) if invariant_masses else 0.0,
        "species_counts": species_counts,
        "mass_histogram": _build_mass_histogram(analysis_results),
        "analysis_highlights": [result.as_dict() for result in analysis_results[:5]],
    }


def _aggregate_calorimeter(calorimeter_hits: list[dict[str, object]]) -> list[dict[str, float]]:
    totals: dict[int, float] = {}
    for hit in calorimeter_hits:
        phi_bin = int(hit["phi_bin"])
        totals[phi_bin] = totals.get(phi_bin, 0.0) + float(hit["deposited_energy_gev"])
    return [{"phi_bin": phi_bin, "energy_gev": _round(energy, 6)} for phi_bin, energy in sorted(totals.items())]


def _timeline(
    output,
    collisions: list[dict[str, object]],
    reco_events: list[ReconstructedEvent],
    analysis_results: list[AnalysisResult],
) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for stage in output.summary().get("stage_metrics", []):
        entries.append({"type": "stage", **stage})
    for collision in collisions:
        entries.append(
            {
                "type": "collision",
                "event_id": collision["event_id"],
                "time_s": collision["time_s"],
                "process": collision["process"],
                "products": len(collision["product_ids"]),
            }
        )
    for event in reco_events:
        entries.append(
            {
                "type": "reconstruction",
                "event_id": event.event_id,
                "tracks": event.n_tracks,
                "jets": event.n_jets,
                "met_gev": _round(event.met_gev, 6),
            }
        )
    for result in analysis_results:
        entries.append(
            {
                "type": "analysis",
                "analysis_type": result.analysis_type,
                "value": _round(result.value, 6),
                "significance_sigma": _round(result.significance_sigma, 6),
            }
        )
    return entries


def _serialize_collision_stream_event(
    collision: dict[str, object],
    collision_energy_gev: float,
    final_particle_map: dict[int, dict[str, object]],
) -> dict[str, object]:
    particles = [
        {
            "type": particle["species"],
            "px": particle["velocity"]["x"],
            "py": particle["velocity"]["y"],
            "pz": particle["velocity"]["z"],
        }
        for particle_id in collision["product_ids"]
        if (particle := final_particle_map.get(int(particle_id)))
    ]
    return {
        "type": "collision_event",
        "event_id": collision["event_id"],
        "timestamp": int(float(collision["time_s"]) * 1000.0),
        "collision_energy": collision_energy_gev,
        "product_ids": collision["product_ids"],
        "product_species": collision["product_species"],
        "particles": particles,
        "collision": {
            "mass": collision["invariant_mass_gev"],
            "jets": sum(1 for species in collision["product_species"] if str(species).startswith("pi")),
            "muons": sum(1 for species in collision["product_species"] if str(species).startswith("muon")),
        },
        "time_s": collision["time_s"],
    }


def _run_simulation(request: SimulationRequest):
    base_config = _config_to_pipeline(request)
    output = SimulationController(base_config).run_pipeline()
    if output.success and output.collision_events:
        return output

    fallback_config = SimulationConfig(
        run_id=f"{base_config.run_id}_fallback",
        n_events=max(2, base_config.n_events),
        beam=BeamParameters(
            species=base_config.beam.species,
            energy_gev=base_config.beam.energy_gev,
            n_particles=max(base_config.beam.n_particles, 3),
            bunch_spread_m=base_config.beam.bunch_spread_m,
            longitudinal_spread_m=max(base_config.beam.longitudinal_spread_m, 0.02),
            seed=base_config.beam.seed,
        ),
        dt_s=base_config.dt_s,
        max_steps=max(base_config.max_steps, 64),
        magnetic_field_t=base_config.magnetic_field_t,
        rf_voltage_v=base_config.rf_voltage_v,
        interaction_radius_m=min(0.18, base_config.interaction_radius_m * 2.5),
        jet_radius=base_config.jet_radius,
        min_jet_pt_gev=base_config.min_jet_pt_gev,
        random_seed=base_config.random_seed,
    )
    fallback_output = SimulationController(fallback_config).run_pipeline()
    return fallback_output if fallback_output.success else output


def simulate_payload(config_dict: dict[str, object] | None = None) -> dict[str, object]:
    request = SimulationRequest.from_dict(config_dict)
    output = _run_simulation(request)
    if not output.success:
        raise RuntimeError(output.error_message or "simulation pipeline failed")

    collisions = [_serialize_collision(index, collision) for index, collision in enumerate(output.collision_events)]
    initial_particles = [_serialize_particle(particle) for particle in output.beam_particles]
    final_particle_states = _collect_final_particles(output.collision_events)
    final_particles = [_serialize_particle(particle) for particle in final_particle_states]
    tracker_hits = _serialize_tracker_hits(output.detector_hits)
    calorimeter_hits = _serialize_calorimeter_hits(output.detector_hits)
    detector_hits = _serialize_detector_hits(tracker_hits, calorimeter_hits)
    tracks = _serialize_particle_tracks(final_particles)
    timeline = _timeline(output, collisions, output.reco_events, output.analysis_results)

    response = {
        "config": {
            "beam_energy_gev": request.beam_energy_gev,
            "beam_intensity": request.beam_intensity,
            "magnetic_field_t": request.magnetic_field_t,
            "rf_field_v_m": request.rf_field_v_m,
            "quadrupole_gradient_t_per_m": request.quadrupole_gradient_t_per_m,
            "beam_particles_per_side": request.beam_particles_per_side,
            "beam_spread_m": request.beam_spread_m,
            "longitudinal_spacing_m": request.longitudinal_spacing_m,
            "interaction_radius_m": request.interaction_radius_m,
            "event_probability": request.event_probability,
            "aperture_radius_m": request.aperture_radius_m,
            "steps": request.steps,
            "seed": request.seed,
        },
        "summary": _summary(output, collisions, final_particle_states, output.analysis_results),
        "initial_particles": initial_particles,
        "final_particles": final_particles,
        "collisions": collisions,
        "particles": final_particles,
        "tracks": tracks,
        "tracker_hits": tracker_hits,
        "calorimeter_hits": calorimeter_hits,
        "detector_hits": detector_hits,
        "calorimeter_phi_totals": _aggregate_calorimeter(calorimeter_hits),
        "timeline": timeline,
        "analysis_results": [result.as_dict() for result in output.analysis_results],
        "reconstructed_events": [event.as_dict() for event in output.reco_events],
    }

    collision_energy_gev = request.beam_energy_gev * 2.0
    final_particle_map = {int(particle["particle_id"]): particle for particle in final_particles}
    for collision in collisions:
        event_broker.publish_event(_serialize_collision_stream_event(collision, collision_energy_gev, final_particle_map))
    event_broker.publish_snapshot(response)
    return response
