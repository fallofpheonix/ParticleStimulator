import { lazy, memo, Suspense } from "react";

import { useSimulationStore } from "@store/simulationStore";

const CollaborationPanel = lazy(() => import("@collaboration/CollaborationPanel.jsx"));
const ExperimentsPanel = lazy(() => import("@experiments/ExperimentsPanel.jsx"));

const DebugPanel = memo(function DebugPanel() {
  const simulationState = useSimulationStore((state) => state.simulationState);
  const wsStatus = useSimulationStore((state) => state.eventStream.wsStatus);
  const debugVisible = useSimulationStore((state) => state.uiLayout.debugVisible);
  const toggleLayoutPanel = useSimulationStore((state) => state.toggleLayoutPanel);

  return (
    <div className="debug-shell">
      <button type="button" className="ghost" onClick={() => toggleLayoutPanel("debugVisible")}>
        {debugVisible ? "Hide Debug" : "Show Debug"}
      </button>
      {debugVisible ? (
        <div className="debug-panel">
          <div className="kv-row">
            <span>health</span>
            <strong>{simulationState.health}</strong>
          </div>
          <div className="kv-row">
            <span>sim status</span>
            <strong>{simulationState.status}</strong>
          </div>
          <div className="kv-row">
            <span>ws</span>
            <strong>{wsStatus}</strong>
          </div>
          <Suspense fallback={<div className="empty-state">Loading debug adapters…</div>}>
            <CollaborationPanel />
            <ExperimentsPanel />
          </Suspense>
        </div>
      ) : null}
    </div>
  );
});

export default DebugPanel;
