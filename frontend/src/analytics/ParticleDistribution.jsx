import { memo, useMemo, useState } from "react";
import { arc, pie } from "d3";

import { particleColor } from "@events/colors";

const WIDTH = 280;
const HEIGHT = 220;
const RADIUS = 78;

const ParticleDistribution = memo(function ParticleDistribution({ events }) {
  const [active, setActive] = useState(null);
  const species = useMemo(() => {
    const counts = new Map();
    for (const event of events) {
      for (const particle of event.particles ?? []) {
        counts.set(particle.type, (counts.get(particle.type) ?? 0) + 1);
      }
    }
    return [...counts.entries()].map(([label, value]) => ({ label, value }));
  }, [events]);

  const arcs = useMemo(() => pie().value((entry) => entry.value)(species), [species]);
  const shape = useMemo(() => arc().innerRadius(40).outerRadius(RADIUS), []);
  const total = species.reduce((sum, entry) => sum + entry.value, 0);
  const activeEntry = active ?? species[0];

  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Particle Types</h3>
        <span>{total} detections</span>
      </div>
      {species.length ? (
        <div className="particle-distribution">
          <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="analytics-svg analytics-svg--small" role="img" aria-label="Particle type distribution">
            <g transform={`translate(${WIDTH / 2} ${HEIGHT / 2})`}>
              {arcs.map((entry) => (
                <path
                  key={entry.data.label}
                  d={shape(entry) ?? undefined}
                  fill={particleColor(entry.data.label)}
                  className="distribution-slice"
                  onMouseEnter={() => setActive(entry.data)}
                />
              ))}
              <text textAnchor="middle" className="distribution-center distribution-center--label" y="-4">
                {activeEntry?.label ?? "none"}
              </text>
              <text textAnchor="middle" className="distribution-center" y="18">
                {activeEntry ? `${((activeEntry.value / total) * 100).toFixed(1)}%` : "0%"}
              </text>
            </g>
          </svg>
          <div className="distribution-legend">
            {species.map((entry) => (
              <div key={entry.label} className="legend-row">
                <span><i className="swatch" style={{ background: particleColor(entry.label) }} /> {entry.label}</span>
                <strong>{entry.value}</strong>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="empty-state">No particle distribution available.</div>
      )}
    </section>
  );
});

export default ParticleDistribution;
