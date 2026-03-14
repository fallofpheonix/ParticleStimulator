# Accelerator Design

## Implemented Beamline Model
- `DipoleMagnet`: constant `Bz` field for bending
- `QuadrupoleMagnet`: weak linear focusing term in the transverse plane
- `RFCavity`: localized `Ey` field for acceleration
- `VacuumChamber`: cylindrical aperture and longitudinal bound

## Invariants
- Particles are advanced in SI units.
- Velocity is capped below `c`.
- A particle leaving the vacuum chamber is marked inactive.
- Collision eligibility requires short separation and negative radial closing rate.

## Current Limits
- No synchrotron-ring geometry solver
- No lattice sequencing
- No beam optics matching
- No synchrotron radiation losses
<!-- pad -->
