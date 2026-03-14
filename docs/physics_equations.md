# Core Physics Equation Library

This library catalogs the fundamental formulas governing classical mechanics, electromagnetism, relativity, quantum mechanics, and statistical physics for the simulator.

## Classical Mechanics
*   **Newton's Second Law**: $F = ma$ (Beam motion, acceleration)
*   **Momentum**: $p = mv$ (Momentum conservation in collisions)
*   **Kinetic Energy**: $E_k = \frac{1}{2}mv^2$ (Computing classical particle energies)

## Electromagnetism
*   **Lorentz Force**: $F = q(E + v \times B)$ (Particle trajectories inside magnetic fields)
*   **Coulomb's Law**: $F = k_e \frac{q_1 q_2}{r^2}$ (Electrostatic interactions)

## Relativity
*   **Energy-Mass Relation**: $E = mc^2$ (Mass-energy conversion in collisions)
*   **Relativistic Momentum**: $p = \gamma mv$, where $\gamma = \frac{1}{\sqrt{1-v^2/c^2}}$ (High-energy accelerators)

## Quantum Mechanics & Field Theory
*   **Schrödinger Equation**: $i\hbar \frac{\partial \psi}{\partial t} = -\frac{\hbar^2}{2m}\nabla^2\psi + V\psi$
*   **Uncertainty Principle**: $\Delta x \Delta p \ge \frac{\hbar}{2}$ (Measurement precision limit)
*   **QFT Interactions**: Modeled using Feynman diagrams across fermion fields, gauge boson fields, and the Higgs field.

## Statistical and Collision Physics
*   **Gaussian Distribution**: $P(x) = \frac{1}{\sqrt{2\pi\sigma^2}} e^{-\frac{(x-\mu)^2}{2\sigma^2}}$ (Models detector noise and measurement uncertainty)
*   **Mandelstam Variables**: $s = (p_1 + p_2)^2$ (Used to compute collision energy computationally)

## Detector Physics
*   **Calorimeter Energy Deposition**: $E_{measured} = E_{true} + \text{noise}$ (Energy approximations; tracks reconstructed using Kalman filtering)
<!-- pad -->
