import { memo } from "react";

import { useSimulationStore } from "@store/simulationStore";

const ExperimentsPanel = memo(function ExperimentsPanel() {
  const payload = useSimulationStore((state) => state.simulationState.payload);

  return (
    <section className="subpanel">
      <h3>Experiments</h3>
      <div className="kv-row">
        <span>payload</span>
        <strong>{payload ? "loaded" : "empty"}</strong>
      </div>
      <div className="kv-row">
        <span>collisions</span>
        <strong>{payload?.collisions?.length ?? 0}</strong>
      </div>
    </section>
  );
});

export default ExperimentsPanel;
