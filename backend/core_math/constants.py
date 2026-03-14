"""Physical constants and particle property databases.

This module contains fundamental physical constants used throughout the
simulation, as well as mass and charge databases for all supported particle
species.  Values are given in SI units unless otherwise noted.

Particle masses are in kilograms.
Particle charges are in Coulombs.
Energy conversions are provided for eV, MeV, GeV, and TeV.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Fundamental constants (SI)
# ---------------------------------------------------------------------------

SPEED_OF_LIGHT: float = 299_792_458.0  # m/s
ELEMENTARY_CHARGE: float = 1.602_176_634e-19  # C
PLANCK_CONSTANT: float = 6.626_070_15e-34  # J·s
HBAR: float = PLANCK_CONSTANT / (2.0 * 3.141_592_653_589_793)
VACUUM_PERMITTIVITY: float = 8.854_187_812_8e-12  # F/m
VACUUM_PERMEABILITY: float = 1.256_637_062_12e-6  # N/A²
BOLTZMANN_CONSTANT: float = 1.380_649e-23  # J/K
AVOGADRO_NUMBER: float = 6.022_140_76e23  # 1/mol

# ---------------------------------------------------------------------------
# Energy unit conversions
# ---------------------------------------------------------------------------

EV_TO_JOULE: float = ELEMENTARY_CHARGE
MEV_TO_JOULE: float = 1.0e6 * EV_TO_JOULE
GEV_TO_JOULE: float = 1.0e9 * EV_TO_JOULE
TEV_TO_JOULE: float = 1.0e12 * EV_TO_JOULE

JOULE_TO_EV: float = 1.0 / EV_TO_JOULE
JOULE_TO_GEV: float = 1.0 / GEV_TO_JOULE

# ---------------------------------------------------------------------------
# Mass conversions  (natural units ↔ SI)
# ---------------------------------------------------------------------------

GEV_OVER_C2_TO_KG: float = GEV_TO_JOULE / (SPEED_OF_LIGHT ** 2)

# ---------------------------------------------------------------------------
# Particle masses (kg)
# ---------------------------------------------------------------------------

PARTICLE_MASSES: dict[str, float] = {
    # Leptons
    "electron": 9.109_383_701_5e-31,
    "positron": 9.109_383_701_5e-31,
    "muon-": 1.883_531_627e-28,
    "muon+": 1.883_531_627e-28,
    "tau-": 3.167_54e-27,
    "tau+": 3.167_54e-27,
    "nu_e": 0.0,
    "nu_mu": 0.0,
    "nu_tau": 0.0,
    "anti_nu_e": 0.0,
    "anti_nu_mu": 0.0,
    "anti_nu_tau": 0.0,
    # Quarks (constituent masses, approximate)
    "u": 3.56e-30,
    "d": 8.01e-30,
    "s": 1.78e-28,
    "c": 2.28e-27,
    "b": 7.46e-27,
    "t": 3.08e-25,
    "anti_u": 3.56e-30,
    "anti_d": 8.01e-30,
    "anti_s": 1.78e-28,
    "anti_c": 2.28e-27,
    "anti_b": 7.46e-27,
    "anti_t": 3.08e-25,
    # Hadrons
    "proton": 1.672_621_923_69e-27,
    "antiproton": 1.672_621_923_69e-27,
    "neutron": 1.674_927_498_04e-27,
    "pi+": 2.488_061e-28,
    "pi-": 2.488_061e-28,
    "pi0": 2.406_176e-28,
    "K+": 8.800_59e-28,
    "K-": 8.800_59e-28,
    "K0": 8.871_13e-28,
    # Gauge bosons
    "photon": 0.0,
    "gluon": 0.0,
    "W+": 1.432_4e-25,
    "W-": 1.432_4e-25,
    "Z0": 1.625_4e-25,
    # Higgs boson
    "H0": 2.229_1e-25,
}

# ---------------------------------------------------------------------------
# Particle charges (Coulombs)
# ---------------------------------------------------------------------------

PARTICLE_CHARGES: dict[str, float] = {
    "electron": -ELEMENTARY_CHARGE,
    "positron": ELEMENTARY_CHARGE,
    "muon-": -ELEMENTARY_CHARGE,
    "muon+": ELEMENTARY_CHARGE,
    "tau-": -ELEMENTARY_CHARGE,
    "tau+": ELEMENTARY_CHARGE,
    "nu_e": 0.0,
    "nu_mu": 0.0,
    "nu_tau": 0.0,
    "anti_nu_e": 0.0,
    "anti_nu_mu": 0.0,
    "anti_nu_tau": 0.0,
    "u": (2.0 / 3.0) * ELEMENTARY_CHARGE,
    "d": (-1.0 / 3.0) * ELEMENTARY_CHARGE,
    "s": (-1.0 / 3.0) * ELEMENTARY_CHARGE,
    "c": (2.0 / 3.0) * ELEMENTARY_CHARGE,
    "b": (-1.0 / 3.0) * ELEMENTARY_CHARGE,
    "t": (2.0 / 3.0) * ELEMENTARY_CHARGE,
    "anti_u": (-2.0 / 3.0) * ELEMENTARY_CHARGE,
    "anti_d": (1.0 / 3.0) * ELEMENTARY_CHARGE,
    "anti_s": (1.0 / 3.0) * ELEMENTARY_CHARGE,
    "anti_c": (-2.0 / 3.0) * ELEMENTARY_CHARGE,
    "anti_b": (1.0 / 3.0) * ELEMENTARY_CHARGE,
    "anti_t": (-2.0 / 3.0) * ELEMENTARY_CHARGE,
    "proton": ELEMENTARY_CHARGE,
    "antiproton": -ELEMENTARY_CHARGE,
    "neutron": 0.0,
    "pi+": ELEMENTARY_CHARGE,
    "pi-": -ELEMENTARY_CHARGE,
    "pi0": 0.0,
    "K+": ELEMENTARY_CHARGE,
    "K-": -ELEMENTARY_CHARGE,
    "K0": 0.0,
    "photon": 0.0,
    "gluon": 0.0,
    "W+": ELEMENTARY_CHARGE,
    "W-": -ELEMENTARY_CHARGE,
    "Z0": 0.0,
    "H0": 0.0,
}

# ---------------------------------------------------------------------------
# Particle lifetimes (seconds) — 0.0 means stable
# ---------------------------------------------------------------------------

PARTICLE_LIFETIMES: dict[str, float] = {
    "electron": 0.0,
    "positron": 0.0,
    "muon-": 2.196_981_1e-6,
    "muon+": 2.196_981_1e-6,
    "tau-": 2.903e-13,
    "tau+": 2.903e-13,
    "proton": 0.0,
    "neutron": 878.4,
    "pi+": 2.603_3e-8,
    "pi-": 2.603_3e-8,
    "pi0": 8.43e-17,
    "K+": 1.238e-8,
    "K-": 1.238e-8,
    "photon": 0.0,
    "W+": 3.17e-25,
    "W-": 3.17e-25,
    "Z0": 2.64e-25,
    "H0": 1.56e-22,
}

# ---------------------------------------------------------------------------
# Particle spin (units of ℏ)
# ---------------------------------------------------------------------------

PARTICLE_SPINS: dict[str, float] = {
    "electron": 0.5,
    "positron": 0.5,
    "muon-": 0.5,
    "muon+": 0.5,
    "proton": 0.5,
    "neutron": 0.5,
    "pi+": 0.0,
    "pi-": 0.0,
    "pi0": 0.0,
    "photon": 1.0,
    "gluon": 1.0,
    "W+": 1.0,
    "W-": 1.0,
    "Z0": 1.0,
    "H0": 0.0,
}
