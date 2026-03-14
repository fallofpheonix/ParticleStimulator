from __future__ import annotations

from dataclasses import dataclass
import itertools

from src.core.constants import GEV_TO_J, SPEED_OF_LIGHT_M_S
from src.core.particle import Particle
from src.core.vector import Vector3


_event_ids = itertools.count(1)


@dataclass(slots=True)
class CollisionEvent:
    event_id: int
    time_s: float
    position: Vector3
    incoming_ids: tuple[int, int]
    products: list[Particle]
    invariant_mass_gev: float


def should_collide(left: Particle, right: Particle, interaction_radius_m: float) -> bool:
    if not left.alive or not right.alive:
        return False
    separation = (left.position - right.position).magnitude()
    if separation > interaction_radius_m:
        return False
    relative_position = right.position - left.position
    relative_velocity = right.velocity - left.velocity
    return relative_position.dot(relative_velocity) < 0.0


def synthesize_collision(left: Particle, right: Particle, time_s: float) -> CollisionEvent:
    collision_position = (left.position + right.position) * 0.5
    total_energy_j = left.kinetic_energy_j() + right.kinetic_energy_j()
    invariant_mass_gev = total_energy_j / GEV_TO_J

    direction = (left.velocity - right.velocity).normalized()
    if direction.magnitude() == 0.0:
        direction = Vector3(1.0, 0.0, 0.0)
    transverse = Vector3(-direction.y, direction.x, 0.0).normalized()
    if transverse.magnitude() == 0.0:
        transverse = Vector3(0.0, 1.0, 0.0)

    product_speed = 0.72 * SPEED_OF_LIGHT_M_S
    products = [
        Particle("pi+", collision_position, transverse * product_speed),
        Particle("pi-", collision_position, transverse * -product_speed),
        Particle("photon", collision_position, direction * (0.98 * SPEED_OF_LIGHT_M_S)),
        Particle("photon", collision_position, direction * (-0.98 * SPEED_OF_LIGHT_M_S)),
    ]

    left.alive = False
    right.alive = False
    return CollisionEvent(
        event_id=next(_event_ids),
        time_s=time_s,
        position=collision_position,
        incoming_ids=(left.particle_id, right.particle_id),
        products=products,
        invariant_mass_gev=invariant_mass_gev,
    )
