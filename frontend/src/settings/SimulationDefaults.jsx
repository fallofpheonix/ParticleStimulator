import { memo } from "react";

import { useSimulationStore } from "@store/simulationStore";

const FIELDS = [
  ["beam_energy_gev", "Beam Energy (GeV)"],
  ["magnetic_field_t", "Magnetic Field (T)"],
  ["beam_particles_per_side", "Particles / Side"],
  ["event_probability", "Event Probability"],
];

const SimulationDefaults = memo(function SimulationDefaults({ defaults, onCommit }) {
  const parameters = useSimulationStore((state) => state.simulationParameters);

  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Simulation Defaults</h3>
        <span>persisted</span>
      </div>
      <div className="control-grid">
        {FIELDS.map(([key, label]) => (
          <div key={key} className="kv-row">
            <span>{label}</span>
            <strong>{defaults[key]}</strong>
          </div>
        ))}
      </div>
      <div className="actions">
        <button
          type="button"
          onClick={() => onCommit({ defaultPhysicsParameters: parameters })}
        >
          Save Current Physics As Default
        </button>
      </div>
    </section>
  );
});

export default SimulationDefaults;
