"""
simulation_controller — Full physics simulation pipeline orchestrator.

This is the single entry point that chains all subsystems:
    BeamSource → BeamDynamics → CollisionEngine → DetectorSimulator
    → EventReconstructor → PhysicsAnalyser

External systems (API, WebSocket, database) call run_pipeline() and receive
a structured SimulationOutput — they never import from individual subsystems.

Usage:
    from simulation_core.simulation_controller import SimulationController, SimulationOutput
    from simulation_core.core_models.models import SimulationConfig, BeamParameters

    config = SimulationConfig(
        run_id="lhc_run3",
        n_events=100,
        beam=BeamParameters(energy_gev=6500.0, n_particles=8),
        magnetic_field_t=3.8,
    )
    ctrl = SimulationController(config)
    output = ctrl.run_pipeline()

    # Output is a clean dataclass — safe to serialise to JSON
    print(output.summary())
"""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Any

from simulation_core.core_models.models import (
    ParticleState,
    CollisionEvent,
    DetectorHit,
    ReconstructedEvent,
    AnalysisResult,
    SimulationConfig,
    BeamParameters,
)
from simulation_core.accelerator import (
    BeamSource,
    BeamDynamics,
    AcceleratorLattice,
    DipoleMagnet,
    QuadrupoleMagnet,
    RFCavity,
    VacuumChamber,
)
from simulation_core.collision_engine import CollisionEngine
from simulation_core.detector import DetectorSimulator
from simulation_core.event_reconstruction import EventReconstructor
from simulation_core.analysis import PhysicsAnalyser

log = logging.getLogger("simulation_controller")



@dataclass
class StageMetrics:
    """Timing and count metrics for one pipeline stage."""
    stage: str
    duration_s: float
    n_objects: int
    notes: str = ""


@dataclass
class SimulationOutput:
    """
    Complete output of one simulation run.

    All fields are plain Python objects (lists of dataclasses).
    No numpy arrays or internal engine types leak through this boundary.
    """
    run_id: str
    config: SimulationConfig
    beam_particles:   list[ParticleState]
    collision_events: list[CollisionEvent]
    detector_hits:    list[DetectorHit]
    reco_events:      list[ReconstructedEvent]
    analysis_results: list[AnalysisResult]
    stage_metrics:    list[StageMetrics] = field(default_factory=list)
    total_duration_s: float = 0.0
    success: bool = True
    error_message: str = ""

    def summary(self) -> dict[str, Any]:
        """Compact summary dict — suitable for API serialisation."""
        return {
            "run_id": self.run_id,
            "success": self.success,
            "n_beam_particles": len(self.beam_particles),
            "n_collisions": len(self.collision_events),
            "n_detector_hits": len(self.detector_hits),
            "n_reco_events": len(self.reco_events),
            "n_analysis_results": len(self.analysis_results),
            "total_duration_s": round(self.total_duration_s, 4),
            "stage_metrics": [
                {"stage": m.stage, "duration_s": round(m.duration_s, 4),
                 "n_objects": m.n_objects, "notes": m.notes}
                for m in self.stage_metrics
            ],
            "analysis_highlights": [r.as_dict() for r in self.analysis_results[:5]],
        }

    def collision_event_dicts(self) -> list[dict]:
        return [e.as_dict() for e in self.collision_events]

    def reco_event_dicts(self) -> list[dict]:
        return [e.as_dict() for e in self.reco_events]

    def analysis_result_dicts(self) -> list[dict]:
        return [r.as_dict() for r in self.analysis_results]


class SimulationController:
    """
    Executes the full simulation pipeline from beam generation to physics analysis.

    Architecture:
        Each stage is a self-contained method that calls a single subsystem.
        Data flows exclusively through core_models types.
        No stage has knowledge of other stages' internals.

    Thread safety:
        This class is NOT thread-safe. Run one instance per concurrent simulation.
        For parallel runs, instantiate separate controllers with different seeds.
    """

    def __init__(self, config: SimulationConfig = None):
        self.config = config or SimulationConfig()
        self._metrics: list[StageMetrics] = []

    # Stage 1: Beam Generation

    def _stage_beam_generation(self) -> list[ParticleState]:
        """Generate the initial beam bunch using BeamSource."""
        t0 = time.perf_counter()
        log.info(f"[Stage 1] Beam generation — species={self.config.beam.species}, "
                 f"E={self.config.beam.energy_gev} GeV, N={self.config.beam.n_particles}×2")

        source = BeamSource(self.config.beam)
        particles = source.emit_beam()

        duration = time.perf_counter() - t0
        self._metrics.append(StageMetrics("beam_generation", duration, len(particles),
                                           f"{len(particles)} beam particles generated"))
        log.info(f"[Stage 1] ✓ {len(particles)} particles in {duration:.4f}s")
        return particles

    # Stage 2: Accelerator Transport

    def _stage_accelerator(self, particles: list[ParticleState]) -> list[ParticleState]:
        """Transport beam particles through the accelerator lattice to the IP."""
        t0 = time.perf_counter()
        log.info("[Stage 2] Accelerator transport")

        lattice = AcceleratorLattice(
            dipole=DipoleMagnet(field_t=self.config.magnetic_field_t),
            quadrupole=QuadrupoleMagnet(gradient_t_per_m=0.08),
            rf_cavity=RFCavity(peak_voltage_v=self.config.rf_voltage_v),
            vacuum=VacuumChamber(aperture_r_m=1.5, half_length_m=10.0),
        )
        dynamics = BeamDynamics(
            lattice=lattice,
            dt_s=self.config.dt_s,
            max_steps=self.config.max_steps,
        )
        transported = dynamics.transport_to_ip(particles)
        alive = [p for p in transported if p.alive]

        duration = time.perf_counter() - t0
        lost = len(particles) - len(alive)
        self._metrics.append(StageMetrics("accelerator", duration, len(alive),
                                           f"{lost} particles lost on aperture"))
        log.info(f"[Stage 2] ✓ {len(alive)} alive at IP ({lost} lost) in {duration:.4f}s")
        return transported

    # Stage 3: Collision Engine

    def _stage_collisions(self, particles: list[ParticleState]) -> list[CollisionEvent]:
        """Find collision pairs and run the full QCD+shower+hadron pipeline."""
        t0 = time.perf_counter()
        log.info("[Stage 3] Collision engine")

        engine = CollisionEngine(
            interaction_radius_m=self.config.interaction_radius_m,
            seed=self.config.random_seed,
        )
        events = engine.simulate_collision(particles)

        duration = time.perf_counter() - t0
        n_final = sum(len(e.final_state) for e in events)
        self._metrics.append(StageMetrics("collisions", duration, len(events),
                                           f"{n_final} final-state particles"))
        log.info(f"[Stage 3] ✓ {len(events)} collision events, {n_final} final-state particles "
                 f"in {duration:.4f}s")
        return events

    # Stage 4: Detector Simulation

    def _stage_detector(
        self, events: list[CollisionEvent]
    ) -> list[DetectorHit]:
        """Simulate detector response for all final-state particles."""
        t0 = time.perf_counter()
        log.info("[Stage 4] Detector simulation")

        sim = DetectorSimulator(seed=self.config.random_seed)
        all_hits: list[DetectorHit] = []

        for event in events:
            hits = sim.simulate_detector(event.final_state)
            all_hits.extend(hits)

        by_layer: dict[str, int] = {}
        for h in all_hits:
            by_layer[h.detector_layer] = by_layer.get(h.detector_layer, 0) + 1

        duration = time.perf_counter() - t0
        self._metrics.append(StageMetrics("detector", duration, len(all_hits),
                                           str(by_layer)))
        log.info(f"[Stage 4] ✓ {len(all_hits)} detector hits in {duration:.4f}s  {by_layer}")
        return all_hits

    # Stage 5: Event Reconstruction

    def _stage_reconstruction(
        self,
        hits: list[DetectorHit],
        events: list[CollisionEvent],
    ) -> list[ReconstructedEvent]:
        """Reconstruct tracks, jets, vertices, and MET from raw hits."""
        t0 = time.perf_counter()
        log.info("[Stage 5] Event reconstruction")

        reco = EventReconstructor(
            jet_radius=self.config.jet_radius,
            min_jet_pt_gev=self.config.min_jet_pt_gev,
        )

        reco_events: list[ReconstructedEvent] = []

        if not events:
            return reco_events

        # Associate hits to collision events by particle ID.
        # In a real pipeline hits would be associated by bunch crossing timestamp.
        hit_by_pid: dict[int, list[DetectorHit]] = {}
        for h in hits:
            hit_by_pid.setdefault(h.particle_id, []).append(h)

        for collision in events:
            pids = {p.id for p in collision.final_state}
            event_hits = [h for pid in pids for h in hit_by_pid.get(pid, [])]
            re = reco.reconstruct_event(event_hits, event_id=collision.event_id)
            reco_events.append(re)

        duration = time.perf_counter() - t0
        n_tracks = sum(e.n_tracks for e in reco_events)
        n_jets   = sum(e.n_jets   for e in reco_events)
        self._metrics.append(StageMetrics("reconstruction", duration, len(reco_events),
                                           f"{n_tracks} tracks, {n_jets} jets"))
        log.info(f"[Stage 5] ✓ {len(reco_events)} reco events, "
                 f"{n_tracks} tracks, {n_jets} jets in {duration:.4f}s")
        return reco_events

    # Stage 6: Physics Analysis

    def _stage_analysis(
        self, reco_events: list[ReconstructedEvent]
    ) -> list[AnalysisResult]:
        """Run physics analysis modules on the reconstructed event collection."""
        t0 = time.perf_counter()
        log.info("[Stage 6] Physics analysis")

        analyser = PhysicsAnalyser(
            mass_range_gev=(0.0, max(500.0, 3 * self.config.beam.energy_gev / 1000)),
            n_mass_bins=50,
        )
        results = analyser.analyse_events(reco_events)

        duration = time.perf_counter() - t0
        discoveries = [r for r in results if r.is_discovery]
        evidence    = [r for r in results if r.is_evidence and not r.is_discovery]
        self._metrics.append(StageMetrics("analysis", duration, len(results),
                                           f"{len(discoveries)} discoveries, {len(evidence)} evidence"))
        log.info(f"[Stage 6] ✓ {len(results)} analysis results in {duration:.4f}s  "
                 f"({len(discoveries)} discovery-level, {len(evidence)} evidence-level)")
        return results

    # Master pipeline

    def run_pipeline(self) -> SimulationOutput:
        """
        Execute the complete simulation pipeline.

        Returns:
            SimulationOutput with all physics objects from all stages.
        """
        wall_t0 = time.perf_counter()
        self._metrics = []
        log.info(f"═══ Starting simulation run: {self.config.run_id} ═══")

        try:
            # Stage 1: Beam
            beam_particles = self._stage_beam_generation()

            # Stage 2: Accelerator transport
            transported = self._stage_accelerator(beam_particles)

            # Stage 3: Collisions (run n_events times or until pairs exhausted)
            all_events: list[CollisionEvent] = []
            all_particles = list(transported)

            # For multiple collision events, regenerate beam bunches
            for event_idx in range(self.config.n_events):
                if event_idx > 0:
                    # Re-emit fresh beam for each simulated collision
                    new_source = BeamSource(
                        BeamParameters(
                            species=self.config.beam.species,
                            energy_gev=self.config.beam.energy_gev,
                            n_particles=self.config.beam.n_particles,
                            seed=self.config.beam.seed + event_idx,
                        )
                    )
                    fresh = new_source.emit_beam()
                    all_particles = fresh

                events = self._stage_collisions(all_particles)
                all_events.extend(events)

                if not events and event_idx == 0:
                    log.warning("No collision pairs found. Check interaction_radius_m.")
                    break

            # Stage 4: Detector
            all_hits = self._stage_detector(all_events)

            # Stage 5: Reconstruction
            reco_events = self._stage_reconstruction(all_hits, all_events)

            # Stage 6: Analysis
            analysis_results = self._stage_analysis(reco_events)

            total = time.perf_counter() - wall_t0
            log.info(f"═══ Run {self.config.run_id} complete in {total:.3f}s ═══")

            return SimulationOutput(
                run_id=self.config.run_id,
                config=self.config,
                beam_particles=beam_particles,
                collision_events=all_events,
                detector_hits=all_hits,
                reco_events=reco_events,
                analysis_results=analysis_results,
                stage_metrics=list(self._metrics),
                total_duration_s=total,
                success=True,
            )

        except Exception as exc:
            total = time.perf_counter() - wall_t0
            log.exception(f"Pipeline failed after {total:.3f}s: {exc}")
            return SimulationOutput(
                run_id=self.config.run_id,
                config=self.config,
                beam_particles=[],
                collision_events=[],
                detector_hits=[],
                reco_events=[],
                analysis_results=[],
                stage_metrics=list(self._metrics),
                total_duration_s=total,
                success=False,
                error_message=str(exc),
            )

    # Convenience single-event API

    def run_single_event(self, particles: list[ParticleState]) -> SimulationOutput | None:
        """
        Run a single-event pipeline given pre-built beam particles.
        Useful for testing individual collision scenarios.
        """
        self._metrics = []
        t0 = time.perf_counter()

        events  = self._stage_collisions(particles)
        if not events:
            return None

        hits        = self._stage_detector(events)
        reco_events = self._stage_reconstruction(hits, events)
        results     = self._stage_analysis(reco_events)

        return SimulationOutput(
            run_id=self.config.run_id + "_single",
            config=self.config,
            beam_particles=particles,
            collision_events=events,
            detector_hits=hits,
            reco_events=reco_events,
            analysis_results=results,
            stage_metrics=list(self._metrics),
            total_duration_s=time.perf_counter() - t0,
            success=True,
        )
