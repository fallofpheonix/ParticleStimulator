import { memo, useState } from "react";

import { useSimulationStore } from "@store/simulationStore";

const CONTROL_KEYS = [
  ["beam_energy_gev", "Beam Energy"],
  ["magnetic_field_t", "Dipole Field"],
  ["interaction_radius_m", "Interaction Radius"]
];

const SharedControls = memo(function SharedControls({ users }) {
  const parameters = useSimulationStore((state) => state.physicsParameters);
  const setPhysicsParameter = useSimulationStore((state) => state.setPhysicsParameter);
  const [locks, setLocks] = useState({});

  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Shared Controls</h3>
        <span>synchronized parameters</span>
      </div>
      <div className="shared-controls">
        {CONTROL_KEYS.map(([key, label], index) => {
          const holder = locks[key] ? users[index % users.length] : null;
          return (
            <div key={key} className="shared-control-row">
              <div className="shared-control-head">
                <span>{label}</span>
                <button
                  type="button"
                  className="ghost"
                  onClick={() => setLocks((current) => ({ ...current, [key]: !current[key] }))}
                >
                  {holder ? `Locked by ${holder.name}` : "Claim"}
                </button>
              </div>
              <input
                type="range"
                min={key === "beam_energy_gev" ? 100 : 0}
                max={key === "beam_energy_gev" ? 7000 : key === "magnetic_field_t" ? 8 : 0.12}
                step={key === "beam_energy_gev" ? 50 : 0.01}
                value={parameters[key]}
                onChange={(event) => setPhysicsParameter(key, Number(event.target.value))}
                disabled={Boolean(holder)}
              />
            </div>
          );
        })}
      </div>
    </section>
  );
});

export default SharedControls;
