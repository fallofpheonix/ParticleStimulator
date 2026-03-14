import { memo } from "react";

import { useSimulationStore } from "@store/simulationStore";

const ModelMetrics = memo(function ModelMetrics() {
  const metrics = useSimulationStore((state) => state.ml.metrics);

  if (!metrics) {
    return (
      <section className="subpanel">
        <div className="chart-header">
          <h3>Model Metrics</h3>
          <span>idle</span>
        </div>
        <div className="empty-state">No trained model metrics available.</div>
      </section>
    );
  }

  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Model Metrics</h3>
        <span>{metrics.model_backend}</span>
      </div>
      <div className="metric-grid">
        {[
          ["Accuracy", metrics.accuracy?.toFixed(3)],
          ["Precision", metrics.precision?.toFixed(3)],
          ["Recall", metrics.recall?.toFixed(3)],
          ["ROC AUC", metrics.roc_auc?.toFixed(3)],
        ].map(([label, value]) => (
          <article key={label} className="metric-card">
            <strong>{value}</strong>
            <span>{label}</span>
          </article>
        ))}
      </div>
      <div className="subpanel">
        <h3>Confusion Matrix</h3>
        <div className="metric-grid">
          {(metrics.confusion_matrix ?? []).flatMap((row, rowIndex) =>
            row.map((value, colIndex) => (
              <article key={`${rowIndex}-${colIndex}`} className="metric-card">
                <strong>{value}</strong>
                <span>{`y${rowIndex} → p${colIndex}`}</span>
              </article>
            ))
          )}
        </div>
      </div>
    </section>
  );
});

export default ModelMetrics;
