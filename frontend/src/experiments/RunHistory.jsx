import { memo } from "react";

const RunHistory = memo(function RunHistory({ runs }) {
  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Run History</h3>
        <span>{runs.length ? runs[0].status : "idle"}</span>
      </div>
      <div className="timeline-list">
        {runs.slice(0, 6).map((run) => (
          <div key={run.id} className="log-row">
            <strong>{run.startedAt}</strong>
            <small>
              collisions={run.collisions} particles={run.particles} transport={run.transport}
            </small>
          </div>
        ))}
      </div>
    </section>
  );
});

export default RunHistory;
