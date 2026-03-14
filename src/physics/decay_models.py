from __future__ import annotations

from src.core.constants import SPEED_OF_LIGHT_M_S
from src.core.particle import Particle
from src.core.vector import Vector3


def decay_products(particle: Particle) -> list[Particle]:
    if particle.species != "pi0":
        return []

    direction = particle.velocity.normalized()
    if direction.magnitude() == 0.0:
        direction = Vector3(1.0, 0.0, 0.0)
    transverse = Vector3(-direction.y, direction.x, 0.0).normalized()
    if transverse.magnitude() == 0.0:
        transverse = Vector3(0.0, 1.0, 0.0)

    speed = 0.95 * SPEED_OF_LIGHT_M_S
    return [
        Particle("photon", particle.position, (direction + transverse).normalized() * speed),
        Particle("photon", particle.position, (direction - transverse).normalized() * speed),
    ]
