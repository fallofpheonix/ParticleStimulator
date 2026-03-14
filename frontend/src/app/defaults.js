export const defaultPhysicsParameters = {
  beam_energy_gev: 6500,
  magnetic_field_t: 3.5,
  rf_field_v_m: 150000,
  quadrupole_gradient_t_per_m: 0.08,
  beam_particles_per_side: 6,
  beam_spread_m: 0.018,
  longitudinal_spacing_m: 0.008,
  interaction_radius_m: 0.06,
  steps: 160,
  seed: 7
};

export const fieldSchema = [
  { name: "beam_energy_gev", label: "Beam Energy (GeV)", type: "range", min: 100, max: 7000, step: 50 },
  { name: "magnetic_field_t", label: "Magnetic Field (T)", type: "range", min: 0, max: 8, step: 0.1 },
  { name: "rf_field_v_m", label: "RF Field (V/m)", type: "range", min: 0, max: 800000, step: 10000 },
  {
    name: "quadrupole_gradient_t_per_m",
    label: "Quadrupole Gradient (T/m)",
    type: "range",
    min: 0,
    max: 1,
    step: 0.01
  },
  { name: "beam_particles_per_side", label: "Particles / Side", type: "range", min: 2, max: 16, step: 1 },
  { name: "beam_spread_m", label: "Beam Spread (m)", type: "range", min: 0.002, max: 0.08, step: 0.002 },
  {
    name: "longitudinal_spacing_m",
    label: "Longitudinal Spacing (m)",
    type: "range",
    min: 0.002,
    max: 0.05,
    step: 0.002
  },
  {
    name: "interaction_radius_m",
    label: "Interaction Radius (m)",
    type: "range",
    min: 0.01,
    max: 0.12,
    step: 0.005
  },
  { name: "steps", label: "Steps", type: "range", min: 10, max: 400, step: 10 },
  { name: "seed", label: "Seed", type: "number", min: 0, max: 999999, step: 1 }
];
