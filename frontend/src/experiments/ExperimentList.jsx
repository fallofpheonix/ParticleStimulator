import { memo } from "react";

const ExperimentList = memo(function ExperimentList({ runs, selectedRunId, onSelect }) {
  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Experiment Runs</h3>
        <span>{runs.length} recorded</span>
      </div>
      <div className="timeline-list">
        {runs.length ? (
          runs.map((run) => (
            <button
              key={run.id}
              type="button"
              className={`event-card ${selectedRunId === run.id ? "event-card--selected" : ""}`}
              onClick={() => onSelect(run.id)}
            >
              <div className="card-row">
                <span className="eid">{run.id}</span>
                <span className="energy-badge">{run.beamEnergyTeV.toFixed(2)} TeV</span>
              </div>
              <div className="card-row">
                <span>{run.collisions} collisions</span>
                <span>{run.detectorHits} hits</span>
              </div>
            </button>
          ))
        ) : (
          <div className="empty-state">No completed runs yet.</div>
        )}
      </div>
    </section>
  );
});

export default ExperimentList;
