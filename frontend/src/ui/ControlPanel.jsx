import { memo, useCallback } from "react";

import { ConfigPanel } from "@config";
import { eventBus } from "@services/eventBus";
import { useSimulationStore } from "@store/simulationStore";

const ControlPanel = memo(function ControlPanel() {
  const parameters = useSimulationStore((state) => state.simulationParameters);
  const status = useSimulationStore((state) => state.simulationState.status);
  const error = useSimulationStore((state) => state.simulationState.error);
  const transport = useSimulationStore((state) => state.simulationState.transport);
  const hydrateDefaults = useSimulationStore((state) => state.hydrateDefaults);
  const defaultParameters = useSimulationStore((state) => state.settings.defaultPhysicsParameters);

  const runSimulation = useCallback(async () => {
    await eventBus.runSimulation(parameters);
  }, [parameters]);

  const resetDefaults = useCallback(() => {
    hydrateDefaults(defaultParameters);
  }, [defaultParameters, hydrateDefaults]);

  return (
    <>
      <div className="panel-header">
        <h2>Control Panel</h2>
        <p>Unified physics parameter editor backed by the application store</p>
      </div>
      <ConfigPanel />
      <div className="actions">
        <button type="button" onClick={runSimulation} disabled={status === "running"}>
          {status === "running" ? "Running…" : "Run Simulation"}
        </button>
        <button type="button" className="ghost" onClick={resetDefaults}>
          Reset Defaults
        </button>
      </div>
      <div className="control-meta">
        <span>transport: {transport}</span>
        <span>status: {status}</span>
      </div>
      {error ? <div className="error-banner">{error}</div> : null}
    </>
  );
});

export default ControlPanel;
