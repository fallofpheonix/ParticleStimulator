# Particle Simulator Frontend Architecture

This document describes the recommended 3D visualization frontend for the Particle Accelerator Simulator.

## Tech Stack
* **React**: For UI and state management.
* **Three.js** (via `@react-three/fiber` and `@react-three/drei`): For rendering the 3D particle scene and accelerator ring.
* **WebGL**: Underlying graphics API used by Three.js.
* **D3.js / Chart.js**: For real-time physics and data visualization.
* **TailwindCSS**: For modern UI design (glassmorphism, dark mode).

## Recommended Frontend Architecture

```text
Frontend

UI Layer
│
├── Simulation Controls (ControlPanel)
├── Parameter Dashboard (StatsDashboard)
└── Event Logger

3D Visualization
│
├── Particle Renderer (ParticleScene)
├── Beam Path Renderer (AcceleratorRing)
└── Collision Effects (CollisionView)

Data Visualization
│
├── Energy Graphs
├── Particle Count
└── Detector Signals
```

## Example File Structure

```text
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── ParticleScene.jsx
│   │   ├── AcceleratorRing.jsx
│   │   └── CollisionView.jsx
│   │
│   ├── physics/
│   │   └── particleEngine.js
│   │
│   ├── ui/
│   │   ├── ControlPanel.jsx
│   │   └── StatsDashboard.jsx
│   │
│   └── App.jsx
```

## UI Controls

* **Control Panel**: Sliders to control Beam Intensity, Particle Energy, and Magnetic Field Strength.
* **Stats Dashboard**: Real-time graphs for Collision Energy and Particle Momentum.

## Development Workflow

1. Initialize Vite React project
2. Install dependencies: `three`, `@react-three/fiber`, `@react-three/drei`, `tailwindcss`, `d3`.
3. Build the 3D `ParticleScene` rendering particles inside a toroidal `AcceleratorRing`.
4. Connect the Python physics backend or internal JS physics engine properties to the UI via state management.
<!-- pad -->
