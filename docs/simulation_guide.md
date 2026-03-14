# Simulation Guide

## MVP Scope
The current implementation is a deterministic Python MVP intended to define execution flow and subsystem interfaces. It is not a GEANT4/PYTHIA-class simulation.

## Execution Path
1. Create `Particle` objects with SI-space position and velocity vectors.
2. Pass them into `SimulationEngine.run(...)`.
3. For each step:
   - Select a stable time step from current particle speed.
   - Compute RF electric field and magnetic beamline fields.
   - Advance particles with Lorentz-force integration.
   - Kill particles leaving the vacuum aperture.
   - Detect short-range, closing collisions.
   - Synthesize deterministic collision products.
   - Record tracker hits and calorimeter deposits.
4. Return `SimulationResult` with particles, collisions, detector data, and JSON logs.

## Outputs
- `SimulationResult.collisions`
- `SimulationResult.tracker_hits`
- `SimulationResult.calorimeter_hits`
- `SimulationResult.event_log_json`

## Assumptions
- Units are SI internally.
- Collision synthesis is a toy model.
- Detector geometry is cylindrical and coarse.
- Visualization is text/metric output only.
<!-- pad -->
