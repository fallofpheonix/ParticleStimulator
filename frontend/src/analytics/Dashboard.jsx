import { memo, useMemo } from "react";
import { scaleLinear } from "d3-scale";

import { useSimulationStore } from "@store/simulationStore";

function Histogram({ bins }) {
  const maxCount = useMemo(() => Math.max(1, ...bins.map((bin) => bin.count ?? 0)), [bins]);
  const yScale = useMemo(() => scaleLinear().domain([0, maxCount]).range([0, 160]), [maxCount]);

  if (!bins.length) {
    return <div className="empty-state">Run a simulation to populate invariant-mass bins.</div>;
  }

  return (
    <svg className="histogram-svg" viewBox="0 0 520 220" role="img" aria-label="Invariant mass histogram">
      {bins.map((bin, index) => {
        const barWidth = 520 / bins.length;
        const height = yScale(bin.count ?? 0);
        const x = index * barWidth + 4;
        const y = 180 - height;
        return (
          <g key={`${bin.label}-${index}`}>
            <rect x={x} y={y} width={Math.max(10, barWidth - 8)} height={height} rx="8" />
            <text x={x + 4} y="205">
              {bin.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function CalorimeterBars({ totals }) {
  const maxEnergy = useMemo(() => Math.max(1, ...totals.map((row) => row.energy_gev ?? 0)), [totals]);

  if (!totals.length) {
    return <div className="empty-state">No calorimeter occupancy yet.</div>;
  }

  return (
    <div className="bar-list">
      {totals.map((row) => (
        <div className="bar-row" key={row.phi_bin}>
          <span>phi {row.phi_bin}</span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${((row.energy_gev ?? 0) / maxEnergy) * 100}%` }} />
          </div>
          <strong>{(row.energy_gev ?? 0).toFixed(4)}</strong>
        </div>
      ))}
    </div>
  );
}

const Dashboard = memo(function Dashboard() {
  const payload = useSimulationStore((state) => state.simulationState.payload);
  const summary = payload?.summary;

  return (
    <>
      <div className="panel-header">
        <h2>Analytics Dashboard</h2>
        <p>Collision summaries, invariant mass distribution, and calorimeter occupancy</p>
      </div>
      <div className="metric-grid">
        {[
          ["Collisions", summary?.metrics?.collision_count ?? 0],
          ["Tracker Hits", summary?.metrics?.tracker_hit_count ?? 0],
          ["Calorimeter Hits", summary?.metrics?.calorimeter_hit_count ?? 0],
          ["Active Particles", summary?.active_particles ?? 0],
          ["Mean Mass (GeV)", summary?.mean_invariant_mass_gev ?? 0],
          ["Max Mass (GeV)", summary?.max_invariant_mass_gev ?? 0]
        ].map(([label, value]) => (
          <article className="metric-card" key={label}>
            <strong>{Number(value).toFixed(Number(value) >= 100 ? 0 : 3).replace(/\.000$/, "")}</strong>
            <span>{label}</span>
          </article>
        ))}
      </div>
      <div className="dashboard-grid">
        <section className="subpanel">
          <h3>Invariant Mass Histogram</h3>
          <Histogram bins={summary?.mass_histogram ?? []} />
        </section>
        <section className="subpanel">
          <h3>Calorimeter Occupancy</h3>
          <CalorimeterBars totals={payload?.calorimeter_phi_totals ?? []} />
        </section>
      </div>
    </>
  );
});

export default Dashboard;
