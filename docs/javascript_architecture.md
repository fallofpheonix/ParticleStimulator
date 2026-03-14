# JavaScript Simulator Architecture

This document outlines the correct, decoupled architecture for a JavaScript-based particle physics simulator, separating the physics engine from rendering and UI state.

## 1. System Architecture Layers
1. **Physics Engine Layer**: Relativistic kinematics and Lorentz forces.
2. **Event Generation Layer**: Monte-Carlo parton sampling and hadronization.
3. **Detector Simulation Layer**: Energy deposits in tracker/calorimeter materials.
4. **Event Reconstruction Layer**: Track rebuilding, vertex finding, clustering.
5. **Visualization Layer**: React/Three.js frontend.

## 2. Project Structure
```text
particle-simulator/
├── backend/
│   ├── physics_engine/    (relativistic_motion.js, lorentz_force.js, integrator.js)
│   ├── accelerator/       (beam_source.js, rf_cavity.js, magnet_field.js, beam_dynamics.js)
│   ├── collision/         (parton_distribution.js, scattering_model.js, event_generator.js, particle_shower.js)
│   ├── detector/          (tracker_simulation.js, calorimeter.js, muon_system.js, detector_geometry.js)
│   ├── reconstruction/    (track_reconstruction.js, vertex_finder.js, jet_clustering.js, missing_energy.js)
│   ├── analysis/          (histogram.js, likelihood_fit.js, significance_test.js)
│   └── server/            (websocket_server.js, event_stream.js)
└── frontend/
    ├── renderer/          (particle_scene.jsx, detector_view.jsx, collision_effects.jsx)
    ├── ui/                (control_panel.jsx, energy_dashboard.jsx, event_log.jsx)
    └── app.jsx
```

## 3. Physics Core Example
```javascript
// relativistic_motion.js
export function gamma(v, c=299792458) {
  return 1 / Math.sqrt(1 - (v*v)/(c*c));
}

export function momentum(m, v) {
  const g = gamma(v);
  return g * m * v;
}
```

## 4. Beamline Simulation Example
```javascript
// magnet_field.js
export function dipoleField(Bz) {
  return { Bx: 0, By: 0, Bz };
}
```

## 5. Data Streaming Architecture
Particles flow from the `physics engine` → `event generator` → `JSON event stream` → `WebSocket server` → `frontend renderer`.

**Example Payload:**
```json
{
  "event_id": 1042,
  "collision_energy": 13000,
  "particles": [
    {"type":"electron","px":1.2,"py":-0.5,"pz":0.1},
    {"type":"positron","px":-1.2,"py":0.5,"pz":-0.1}
  ]
}
```

## 6. Realistic Code Volumes
* Physics Engine: ~10k lines
* Detector Simulation: ~15k lines
* Event Generation: ~8k lines
* Reconstruction: ~10k lines
* Visualization: ~7k lines
