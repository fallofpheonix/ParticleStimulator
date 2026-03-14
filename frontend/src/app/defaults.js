export const defaultPhysicsParameters = {
  beam_energy_gev: 6500,
  beam_intensity: 0.82,
  magnetic_field_t: 3.5,
  rf_field_v_m: 150000,
  quadrupole_gradient_t_per_m: 0.08,
  beam_particles_per_side: 6,
  beam_spread_m: 0.018,
  longitudinal_spacing_m: 0.008,
  interaction_radius_m: 0.06,
  event_probability: 0.78,
  aperture_radius_m: 1.5,
  chamber_half_length_m: 2.0,
  detector_resolution_pct: 8,
  detector_noise_pct: 1.8,
  tracker_resolution_um: 45,
  noise_model: "poisson",
  steps: 160,
  seed: 7
};

export const fieldSchema = [
  { name: "beam_energy_gev", label: "Beam Energy (GeV)", type: "range", min: 100, max: 7000, step: 50 },
  { name: "beam_intensity", label: "Beam Intensity", type: "range", min: 0.1, max: 1, step: 0.01 },
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
  { name: "event_probability", label: "Event Probability", type: "range", min: 0.05, max: 1, step: 0.01 },
  { name: "aperture_radius_m", label: "Aperture Radius (m)", type: "range", min: 0.1, max: 4, step: 0.05 },
  { name: "chamber_half_length_m", label: "Chamber Half Length (m)", type: "range", min: 0.5, max: 6, step: 0.1 },
  { name: "detector_resolution_pct", label: "Detector Resolution (%)", type: "range", min: 1, max: 20, step: 0.5 },
  { name: "detector_noise_pct", label: "Detector Noise (%)", type: "range", min: 0, max: 15, step: 0.5 },
  { name: "tracker_resolution_um", label: "Tracker Resolution (um)", type: "range", min: 5, max: 150, step: 1 },
  { name: "steps", label: "Steps", type: "range", min: 10, max: 400, step: 10 },
  { name: "noise_model", label: "Noise Model", type: "select", options: ["poisson", "gaussian", "none"] },
  { name: "seed", label: "Seed", type: "number", min: 0, max: 999999, step: 1 }
];
