import { memo, useEffect, useState } from "react";

import { eventBus } from "@services/eventBus";
import { useSimulationStore } from "@store/simulationStore";

const TrainingPanel = memo(function TrainingPanel() {
  const ml = useSimulationStore((state) => state.ml);
  const setMlStatus = useSimulationStore((state) => state.setMlStatus);
  const [dataset, setDataset] = useState("auto");
  const [sampleSize, setSampleSize] = useState(25000);

  useEffect(() => {
    if (ml.status !== "running" && ml.status !== "queued") {
      return undefined;
    }
    const handle = window.setInterval(() => {
      eventBus.getModelStatus().catch((error) => setMlStatus({ status: "error", error: String(error) }));
    }, 1200);
    return () => window.clearInterval(handle);
  }, [ml.status, setMlStatus]);

  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Training Panel</h3>
        <span>{ml.status}</span>
      </div>
      <div className="control-grid">
        <label>
          <span>Dataset</span>
          <input value={dataset} onChange={(event) => setDataset(event.target.value)} placeholder="auto or data/HIGGS.csv.gz" />
        </label>
        <label>
          <span>Sample Size</span>
          <input
            type="number"
            min="1000"
            max="250000"
            step="1000"
            value={sampleSize}
            onChange={(event) => setSampleSize(Number(event.target.value))}
          />
        </label>
      </div>
      <div className="timeline-progress">
        <div className="bar-track">
          <div className="bar-fill" style={{ width: `${Math.round((ml.progress ?? 0) * 100)}%` }} />
        </div>
      </div>
      <div className="actions">
        <button
          type="button"
          onClick={() => eventBus.trainModel({ dataset, sample_size: sampleSize })}
          disabled={ml.status === "running"}
        >
          {ml.status === "running" ? "Training…" : "Train Classifier"}
        </button>
        <button type="button" className="ghost" onClick={() => eventBus.getModelStatus()}>
          Refresh Status
        </button>
      </div>
      {ml.error ? <div className="error-banner">{ml.error}</div> : null}
    </section>
  );
});

export default TrainingPanel;
