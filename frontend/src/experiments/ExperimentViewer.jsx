import { memo } from "react";

import { exportEvents, exportExperiment, exportTracks } from "@services/exportService";

const ExperimentViewer = memo(function ExperimentViewer({ run, datasets, eventData, particleTracks }) {
  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Run Viewer</h3>
        <span>{run ? run.status : "no run selected"}</span>
      </div>
      {run ? (
        <>
          <div className="metric-grid">
            {[
              ["Beam", `${run.beamEnergyTeV.toFixed(2)} TeV`],
              ["Collisions", run.collisions],
              ["Particles", run.particles],
              ["Mass Peak", `${run.massPeak.toFixed(3)} GeV`],
            ].map(([label, value]) => (
              <article key={label} className="metric-card">
                <strong>{value}</strong>
                <span>{label}</span>
              </article>
            ))}
          </div>
          <div className="control-meta">
            <span>datasets: {datasets.map((dataset) => `${dataset.name}=${dataset.records}`).join(" | ")}</span>
          </div>
          <div className="actions">
            <button type="button" onClick={() => exportExperiment(run, "json")}>
              Export Run JSON
            </button>
            <button type="button" className="ghost" onClick={() => exportEvents(eventData, "csv")}>
              Export Events CSV
            </button>
            <button type="button" className="ghost" onClick={() => exportTracks(particleTracks, "json")}>
              Export Tracks JSON
            </button>
          </div>
        </>
      ) : (
        <div className="empty-state">Run metadata becomes available after the first simulation.</div>
      )}
    </section>
  );
});

export default ExperimentViewer;
