import { memo } from "react";

import { useSimulationStore } from "@store/simulationStore";

const CollaborationPanel = memo(function CollaborationPanel() {
  const session = useSimulationStore((state) => state.userSession);

  return (
    <section className="subpanel">
      <h3>Collaboration</h3>
      <div className="kv-row">
        <span>session</span>
        <strong>{session.sessionId.slice(0, 8)}</strong>
      </div>
      <div className="kv-row">
        <span>connected</span>
        <strong>{session.connectedAt ? "yes" : "no"}</strong>
      </div>
    </section>
  );
});

export default CollaborationPanel;
