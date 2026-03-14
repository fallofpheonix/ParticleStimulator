import { memo } from "react";

import { selectSelectedEvent } from "@app/selectors";
import { eventBus } from "@services/eventBus";
import { useSimulationStore } from "@store/simulationStore";

const PredictionViewer = memo(function PredictionViewer() {
  const selectedEvent = useSimulationStore(selectSelectedEvent);
  const prediction = useSimulationStore((state) => state.ml.lastPrediction);
  const status = useSimulationStore((state) => state.ml.status);

  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Prediction Viewer</h3>
        <span>{prediction?.label ?? "no prediction"}</span>
      </div>
      <div className="actions">
        <button
          type="button"
          onClick={() => selectedEvent && eventBus.predictEvent({ event: selectedEvent })}
          disabled={!selectedEvent || status !== "completed"}
        >
          Classify Selected Event
        </button>
      </div>
      {prediction ? (
        <div className="metric-grid">
          <article className="metric-card">
            <strong>{prediction.label}</strong>
            <span>prediction</span>
          </article>
          <article className="metric-card">
            <strong>{prediction.probability_signal?.toFixed(3)}</strong>
            <span>signal</span>
          </article>
          <article className="metric-card">
            <strong>{prediction.probability_background?.toFixed(3)}</strong>
            <span>background</span>
          </article>
        </div>
      ) : (
        <div className="empty-state">Select an event, train a model, then run inference.</div>
      )}
    </section>
  );
});

export default PredictionViewer;
