import { memo } from "react";

import { fieldSchema } from "@app/defaults";
import { useSimulationStore } from "@store/simulationStore";

const ConfigPanel = memo(function ConfigPanel() {
  const parameters = useSimulationStore((state) => state.physicsParameters);
  const setPhysicsParameter = useSimulationStore((state) => state.setPhysicsParameter);

  return (
    <div className="control-grid">
      {fieldSchema.map((field) => {
        const value = parameters[field.name];
        return (
          <label key={field.name}>
            <span>{field.label}</span>
            <input
              name={field.name}
              type={field.type}
              min={field.min}
              max={field.max}
              step={field.step}
              value={value}
              onChange={(event) =>
                setPhysicsParameter(
                  field.name,
                  field.type === "number" ? Number(event.target.value) : Number(event.target.value)
                )
              }
            />
            {field.type === "range" ? <output>{value}</output> : null}
          </label>
        );
      })}
    </div>
  );
});

export default ConfigPanel;
