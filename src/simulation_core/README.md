# Particle Stimulator — Physics Simulation Pipeline

## Architecture Overview

A modular, research-grade particle physics simulation stack written in pure Python (NumPy + SciPy). Every subsystem is fully independent and communicates exclusively through **frozen immutable dataclasses** defined in `core_models`.

```
beam generation
    ↓  BeamSource (accelerator)
accelerator transport
    ↓  BeamDynamics → Boris push integrator
collision detection & generation
    ↓  CollisionEngine → parton PDF → QCD scatter → DGLAP shower → hadronize → decay
detector simulation
    ↓  SiliconTracker + EMCalorimeter + HadronicCalorimeter + MuonChamber
event reconstruction
    ↓  KalmanFilter track fit → VertexFinder → anti-kT JetClusterer → MET
physics analysis
    ↓  HistogramEngine → InvariantMass → LikelihoodFitter → Significance
    ↓
SimulationOutput  ──→  external API / database / WebSocket layer
```

## Directory Structure

```
backend/
├── __init__.py
├── core_models/
│   ├── __init__.py
│   └── models.py                 ← All shared frozen dataclasses
│
├── physics_engine/
│   └── __init__.py               ← Relativistic kinematics, Lorentz force,
│                                   Boris push, EM field, simulation kernel
│
├── accelerator/
│   └── __init__.py               ← BeamSource, DipoleMagnet, QuadrupoleMagnet,
│                                   RFCavity, VacuumChamber, BeamDynamics
│
├── collision_engine/
│   └── __init__.py               ← find_collisions, PDF sampling, QCD scatter,
│                                   DGLAP shower, string fragmentation,
│                                   decay chains, CollisionEngine orchestrator
│
├── detector/
│   └── __init__.py               ← DetectorGeometry, SiliconTracker,
│                                   EMCalorimeter, HadronicCalorimeter,
│                                   MuonChamber, DetectorSimulator
│
├── event_reconstruction/
│   └── __init__.py               ← KalmanFilter1D, TrackReconstructor,
│                                   VertexFinder, anti-kT JetClusterer,
│                                   compute_missing_energy, EventReconstructor
│
├── analysis/
│   └── __init__.py               ← Histogram1D/2D, HistogramEngine,
│                                   invariant_mass, LikelihoodFitter,
│                                   significance_test, PhysicsAnalyser
│
└── simulation_controller/
    └── __init__.py               ← SimulationController (full pipeline),
                                    SimulationOutput (external interface)
```

## Core Data Models

All subsystems communicate through these frozen dataclasses (`core_models/models.py`):

| Model | Purpose |
|-------|---------|
| `ParticleState` | Complete kinematic state of one particle |
| `CollisionEvent` | One hard-scatter collision with all final-state particles |
| `DetectorHit` | A single raw detector signal |
| `ReconstructedTrack` | Kalman-filtered charged particle track |
| `ReconstructedJet` | Anti-kT jet cluster |
| `ReconstructedVertex` | Fitted interaction vertex |
| `ReconstructedEvent` | Complete reconstructed physics event |
| `AnalysisResult` | Physics measurement or discovery significance |
| `BeamParameters` | Beam source configuration |
| `SimulationConfig` | Full run configuration |

## Quick Start

```python
from backend.simulation_controller import SimulationController
from backend.core_models import SimulationConfig, BeamParameters

config = SimulationConfig(
    run_id="lhc_run3_test",
    n_events=50,
    beam=BeamParameters(
        species="proton",
        energy_gev=6500.0,
        n_particles=8,
        seed=42,
    ),
    magnetic_field_t=3.8,
    rf_voltage_v=2.0e6,
    interaction_radius_m=0.05,
    jet_radius=0.4,
    min_jet_pt_gev=5.0,
)

ctrl = SimulationController(config)
output = ctrl.run_pipeline()

print(output.summary())
# → {run_id, n_collisions, n_detector_hits, n_reco_events, analysis_highlights, ...}

# Access individual stages
for event in output.reco_events:
    print(f"Event {event.event_id}: {event.n_jets} jets, MET={event.met_gev:.1f} GeV")
```

## Subsystem APIs

### Physics Engine
```python
from backend.physics_engine import boris_push, ElectromagneticField, make_particle

field = ElectromagneticField().uniform_magnetic((0, 0, 3.8))
p = make_particle("proton", (0, 0, 0), (0, 100, 0))   # 100 GeV/c in y
p_new = boris_push(p, E_field, B_field, dt_s=1e-11)
```

### Accelerator
```python
from backend.accelerator import BeamSource, BeamDynamics
from backend.core_models import BeamParameters

source = BeamSource(BeamParameters(energy_gev=6500, n_particles=10))
beam = source.emit_beam()                 # List[ParticleState]
dynamics = BeamDynamics()
at_ip = dynamics.transport_to_ip(beam)   # Boris-pushed to IP
```

### Collision Engine
```python
from backend.collision_engine import CollisionEngine

engine = CollisionEngine(interaction_radius_m=0.05, seed=42)
events = engine.simulate_collision(at_ip)   # List[CollisionEvent]
```

### Detector
```python
from backend.detector import DetectorSimulator

sim = DetectorSimulator(seed=42)
hits = sim.simulate_detector(events[0].final_state)  # List[DetectorHit]
```

### Reconstruction
```python
from backend.event_reconstruction import EventReconstructor

reco = EventReconstructor(jet_radius=0.4, min_jet_pt_gev=5.0)
event = reco.reconstruct_event(hits, event_id=1)   # ReconstructedEvent
```

### Analysis
```python
from backend.analysis import PhysicsAnalyser

analyser = PhysicsAnalyser(mass_range_gev=(0, 500), n_mass_bins=50)
results = analyser.analyse_events([event])           # List[AnalysisResult]
```

## Physics Models

### Integrator
- **Boris push** — symplectic, 2nd-order, correct magnetic moment conservation
- Momentum stored in GeV/c; position in metres; time in seconds

### Collision Engine
- **PDF**: power-law parton distribution functions (CTEQ/MRST-inspired)
- **QCD scatter**: simplified 2→2 processes (gg→gg, qg→qg, qq→qq, qq̄→gg)
- **Shower**: DGLAP parton cascade with α_s-weighted splitting
- **Hadronization**: simplified string fragmentation
- **Decay**: recursive Breit-Wigner-weighted decay chains (π⁰, K, μ, W, Z)

### Detector
- **Tracker**: straight-line hit extrapolation, 10 μm position resolution
- **EM cal**: σ_E/E = 10%/√E ⊕ 0.7% (ATLAS-like)
- **Had cal**: σ_E/E = 50%/√E ⊕ 3%
- **Muon**: 100 μm resolution, three stations at r = 4.8, 7.25, 9.75 m

### Reconstruction
- **Track fit**: 1D Kalman filter per coordinate; p estimated from track curvature
- **Vertex**: iterative weighted-mean adaptive fitting
- **Jets**: anti-kT algorithm (exact O(N³) — appropriate for N < 200)
- **MET**: calorimeter vector sum imbalance

### Analysis
- **Mass spectrum**: binned extended maximum-likelihood fit
- **Significance**: Asimov profile likelihood ratio Z = √[2((s+b)ln(1+s/b)−s)]
- **Histograms**: Poisson-weighted 1D with overflow/underflow tracking

## Dependencies

```
numpy >= 1.24
scipy >= 1.10
```

No other runtime dependencies. The simulation core intentionally avoids
ROOT, GEANT4, or any particle physics framework.

## Integration Notes

The `SimulationOutput` object is the only type that should cross the
boundary into the API/database/WebSocket layer. All fields are plain
Python (lists of dataclasses with `.as_dict()` methods).

```python
# In your API handler:
output = ctrl.run_pipeline()
return output.summary()               # dict — safe for JSON
return output.reco_event_dicts()      # list of dicts
return output.analysis_result_dicts() # list of dicts
```
