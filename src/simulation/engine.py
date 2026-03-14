from __future__ import annotations

from dataclasses import dataclass, field

from src.accelerator.beamline import Beamline
from src.core.particle import Particle
from src.detectors.calorimeter import Calorimeter, EnergyDeposit
from src.detectors.event_logger import EventLogger
from src.detectors.tracker import SiliconTracker, TrackerHit
from src.physics.collisions import CollisionEvent, should_collide, synthesize_collision
from src.physics.decay_models import decay_products
from src.simulation.integrator import advance_particle
from src.simulation.timestep import choose_time_step


@dataclass(slots=True)
class SimulationResult:
    final_particles: list[Particle]
    collisions: list[CollisionEvent]
    tracker_hits: list[TrackerHit]
    calorimeter_hits: list[EnergyDeposit]
    event_log_json: str


@dataclass(slots=True)
class SimulationEngine:
    beamline: Beamline = field(default_factory=Beamline)
    tracker: SiliconTracker = field(default_factory=SiliconTracker)
    calorimeter: Calorimeter = field(default_factory=Calorimeter)
    logger: EventLogger = field(default_factory=EventLogger)
    base_dt_s: float = 1.0e-10
    max_particles: int = 64  # cap to prevent O(n²) cascade blowup

    def run(self, particles: list[Particle], steps: int) -> SimulationResult:
        self.logger = EventLogger()
        tracker_hits: list[TrackerHit] = []
        calorimeter_hits: list[EnergyDeposit] = []
        collisions: list[CollisionEvent] = []
        seen_tracker_layers: set[tuple[int, int]] = set()
        deposited_ids: set[int] = set()
        time_s = 0.0

        active_particles = [particle.copy() for particle in particles]

        for _ in range(steps):
            max_speed = max((particle.speed() for particle in active_particles if particle.alive), default=0.0)
            dt_s = choose_time_step(max_speed, self.base_dt_s)
            time_s += dt_s

            for particle in active_particles:
                if not particle.alive:
                    continue
                advance_particle(particle, self.beamline, dt_s)
                if not self.beamline.contains(particle.position):
                    particle.alive = False

            newborn_particles: list[Particle] = []
            if len(active_particles) < self.max_particles:
                for index, left in enumerate(active_particles):
                    if not left.alive:
                        continue
                    for right in active_particles[index + 1 :]:
                        if should_collide(left, right, self.beamline.interaction_radius_m):
                            event = synthesize_collision(left, right, time_s)
                            collisions.append(event)
                            self.logger.log_collision(event)
                            newborn_particles.extend(event.products)
                            if len(active_particles) + len(newborn_particles) >= self.max_particles:
                                break
                    if len(active_particles) + len(newborn_particles) >= self.max_particles:
                        break

            active_particles.extend(newborn_particles)

            decayed_particles: list[Particle] = []
            for particle in active_particles:
                if particle.alive and particle.species == "pi0":
                    particle.alive = False
                    decayed_particles.extend(decay_products(particle))
            active_particles.extend(decayed_particles)

            step_tracker_hits: list[TrackerHit] = []
            step_calorimeter_hits: list[EnergyDeposit] = []
            for particle in active_particles:
                step_tracker_hits.extend(self.tracker.record_hits(particle, time_s, seen_tracker_layers))
                step_calorimeter_hits.extend(self.calorimeter.deposit(particle, time_s, deposited_ids))

            if step_tracker_hits:
                tracker_hits.extend(step_tracker_hits)
                self.logger.log_tracker_hits(step_tracker_hits)
            if step_calorimeter_hits:
                calorimeter_hits.extend(step_calorimeter_hits)
                self.logger.log_calorimeter_hits(step_calorimeter_hits)

        return SimulationResult(
            final_particles=active_particles,
            collisions=collisions,
            tracker_hits=tracker_hits,
            calorimeter_hits=calorimeter_hits,
            event_log_json=self.logger.to_json(),
        )
