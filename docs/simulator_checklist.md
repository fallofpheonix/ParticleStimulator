# Simulator Development Checklist: MVP vs. Full Scope

This document provides a breakdown of what is absolutely required to build a working Minimum Viable Simulator (MVP), what is recommended but optional, and what is definitively not needed.

## 1. Absolutely Needed (Core MVP Requirements)

### Physics & Math
*   **Classical Mechanics**: Newtonian motion ($F=ma$).
*   **Electromagnetism**: Magnetic steering ($F = q(E + v \times B)$).
*   **Relativity**: Mass-energy equivalence ($E=mc^2$).
*   **Math**: Calculus, linear algebra, differential equations, basic numerical simulations.

### Software Stack
*   **Backend**: Python or C++
*   **Frontend**: React, Three.js, WebGL

### Core Modules (MVP = 10k–15k lines)
1.  **Physics Engine**: Motion integration.
2.  **Accelerator Model**: Magnetic beam steering.
3.  **Collision Engine**: Simple interaction generator.
4.  **Detector Model**: Basic hit tracking.
5.  **Visualization System**: 3D event viewer with points and trails.

## 2. Recommended but Optional (For 40k–60k Line Scope)

*   **Advanced Physics**: QFT, Feynman diagrams, Quantum Chromodynamics.
*   **Professional Libraries**: GEANT4, PYTHIA for high-accuracy simulations.
*   **Machine Learning**: Event classification, jet tagging, anomaly detection.
*   **Performance**: GPU Acceleration (CUDA, OpenCL).

## 3. Not Needed for a Practical Simulator

*   A real particle accelerator hardware setup.
*   Full quantum field theory solvers (simplified models are standard).
*   Supercomputer clusters (unless scaling to CERN data volumes).
*   The complete Standard Model Lagrangian implementation.

## Final Summary
To build a Minimum Viable Simulator quickly, stick to basic mechanics, simple collisions, a static detector model, and a WebGL viewer. Only expand into advanced Machine Learning, PYTHIA integrations, and GPU acceleration if building the full research-grade 50k-line platform.
<!-- pad -->
