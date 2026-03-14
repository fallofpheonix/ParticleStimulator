# Fundamental Laws for Particle Simulation

This document outlines the core scientific laws across Physics, Quantum Mechanics, Thermodynamics, Electromagnetism, Chemistry, and Biology that are essential for building particle accelerators, simulators, and high-energy physics systems.

## 1. Fundamental Physics Laws

* **Mass-Energy Equivalence**: $E = mc^2$. Shows energy can convert into matter. Essential for modeling high-energy collisions.
* **Newton's Second Law**: $F = ma$. Used to compute basic classical particle motion.
* **Momentum Conservation**: $p = mv$. Total momentum before and after a collision must remain constant.
* **Relativistic Momentum**: $p = \gamma mv$, where $\gamma = \frac{1}{\sqrt{1-v^2/c^2}}$. Used when particles move close to the speed of light.
* **Lorentz Force**: $F = q(E + v \times B)$. Controls particle motion in accelerators and guides beam steering.
* **Coulomb's Law**: $F = k \frac{q_1 q_2}{r^2}$. Describes the electric force between charged particles.
* **Magnetic Force on Moving Charge**: $F = qvB\sin(\theta)$. Crucial for beam bending magnets.

## 2. Quantum Physics Laws

* **Schrödinger Equation**: $i\hbar \frac{\partial \psi}{\partial t} = -\frac{\hbar^2}{2m}\nabla^2 \psi + V\psi$. Describes quantum wave behavior.
* **Heisenberg Uncertainty Principle**: $\Delta x \Delta p \geq \frac{\hbar}{2}$. Position and momentum cannot both be precisely known simultaneously.
* **Planck Relation**: $E = hf$. Determines the energy of photons.
* **De Broglie Wavelength**: $\lambda = \frac{h}{p}$. Illustrates that particles behave like waves.

## 3. Particle Physics Laws

* **Standard Model**: Describes quarks, leptons, and gauge bosons, including the Higgs boson discovered at the LHC.
* **Conservation Laws**: Preservation of Energy, Momentum, Charge, Baryon number, and Lepton number.

## 4. Thermodynamics Laws

* **First Law of Thermodynamics**: $\Delta U = Q - W$. Energy conservation in systems.
* **Second Law**: Entropy always increases. Critical for accelerator systems and detectors.

## 5. Electromagnetism Laws (Maxwell's Equations)

* **Gauss's Law**: $\nabla \cdot E = \frac{\rho}{\epsilon_0}$
* **Gauss's Law for Magnetism**: $\nabla \cdot B = 0$
* **Faraday's Law**: $\nabla \times E = -\frac{\partial B}{\partial t}$
* **Ampère-Maxwell Law**: $\nabla \times B = \mu_0 J + \mu_0 \epsilon_0 \frac{\partial E}{\partial t}$

## 6. Chemistry Laws (For Detectors)

* **Beer-Lambert Law**: $A = \epsilon c l$. Used to model radiation absorption in detector materials.
* **Radioactive Decay Law**: $N(t) = N_0 e^{-\lambda t}$. Fundamental to nuclear physics.

## 7. Mathematical Foundations Required

* **Linear Algebra**: Vectors and matrices describe particle states (e.g., $p = (p_x, p_y, p_z)$).
* **Calculus**: Crucial for tracking motion ($v = \frac{dx}{dt}, a = \frac{dv}{dt}$).
* **Differential Equations**: Most physics simulations solve differential equations ($\frac{d^2x}{dt^2} = \frac{F}{m}$).
* **Probability Theory**: Monte-Carlo simulations rely heavily on probability ($P(A \cap B) = P(A)P(B)$).

## 8. Biology Laws (Radiation Effects)

* **Radiation Dose**: $D = \frac{E}{m}$. Used to measure energy absorbed by biological tissue.
* **DNA Damage Models**: High-energy particles can cause ionization and molecular bond breaking.

## 9. Computational Physics Principles

Large simulations (like GEANT4 at CERN) rely on:
* Monte Carlo methods
* Numerical integration
* Parallel computing (GPUs, HPC clusters)

---

**Summary:** In practice, about 90% of accelerator physics is based on Relativity, Quantum Mechanics, Electromagnetism, and Statistical Physics.
<!-- pad -->
