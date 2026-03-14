from __future__ import annotations

from dataclasses import dataclass


SPEED_OF_LIGHT_M_S = 299_792_458.0
ELEMENTARY_CHARGE_C = 1.602_176_634e-19
EV_TO_J = ELEMENTARY_CHARGE_C
MEV_TO_J = 1.0e6 * EV_TO_J
GEV_TO_J = 1.0e9 * EV_TO_J
VACUUM_PERMITTIVITY = 8.854_187_812_8e-12


@dataclass(frozen=True, slots=True)
class ParticleSpec:
    name: str
    mass_kg: float
    charge_c: float


PARTICLE_DB: dict[str, ParticleSpec] = {
    "proton": ParticleSpec("proton", 1.672_621_923_69e-27, ELEMENTARY_CHARGE_C),
    "electron": ParticleSpec("electron", 9.109_383_701_5e-31, -ELEMENTARY_CHARGE_C),
    "positron": ParticleSpec("positron", 9.109_383_701_5e-31, ELEMENTARY_CHARGE_C),
    "muon-": ParticleSpec("muon-", 1.883_531_627e-28, -ELEMENTARY_CHARGE_C),
    "muon+": ParticleSpec("muon+", 1.883_531_627e-28, ELEMENTARY_CHARGE_C),
    "pi+": ParticleSpec("pi+", 2.488_061e-28, ELEMENTARY_CHARGE_C),
    "pi-": ParticleSpec("pi-", 2.488_061e-28, -ELEMENTARY_CHARGE_C),
    "pi0": ParticleSpec("pi0", 2.406_176e-28, 0.0),
    "photon": ParticleSpec("photon", 1.0e-36, 0.0),
}
