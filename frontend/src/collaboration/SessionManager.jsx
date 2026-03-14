import { memo } from "react";

import { useSimulationStore } from "@store/simulationStore";

const SessionManager = memo(function SessionManager({ onShare }) {
  const session = useSimulationStore((state) => state.userSession);
  const parameters = useSimulationStore((state) => state.physicsParameters);

  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Session Manager</h3>
        <span>{session.sessionId.slice(0, 8)}</span>
      </div>
      <div className="session-grid">
        <div className="kv-row">
          <span>invite</span>
          <strong>{`PS-${session.sessionId.slice(0, 6).toUpperCase()}`}</strong>
        </div>
        <div className="kv-row">
          <span>transport</span>
          <strong>{session.connectedAt ? "synced" : "local-only"}</strong>
        </div>
        <button type="button" className="ghost" onClick={() => navigator.clipboard?.writeText(JSON.stringify(parameters, null, 2))}>
          Copy Config JSON
        </button>
        <button type="button" onClick={onShare}>
          Share Experiment
        </button>
      </div>
    </section>
  );
});

export default SessionManager;
