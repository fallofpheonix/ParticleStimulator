import { memo, useMemo } from "react";
import { bin, max, scaleLinear } from "d3";

const WIDTH = 560;
const HEIGHT = 220;
const MARGIN = { top: 16, right: 16, bottom: 30, left: 32 };

const magnitude = (particle) =>
  Math.sqrt((particle.px ?? 0) ** 2 + (particle.py ?? 0) ** 2 + (particle.pz ?? 0) ** 2);

const MomentumHistogram = memo(function MomentumHistogram({ events }) {
  const values = useMemo(() => events.flatMap((event) => (event.particles ?? []).map((particle) => magnitude(particle))), [events]);
  const bins = useMemo(() => bin().thresholds(18)(values), [values]);
  const yScale = useMemo(
    () => scaleLinear().domain([0, max(bins, (entry) => entry.length) ?? 1]).range([0, HEIGHT - MARGIN.top - MARGIN.bottom]),
    [bins]
  );

  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Momentum Histogram</h3>
        <span>{values.length} particles</span>
      </div>
      {values.length ? (
        <svg className="histogram-svg analytics-svg" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="Particle momentum distribution">
          {bins.map((entry, index) => {
            const band = (WIDTH - MARGIN.left - MARGIN.right) / bins.length;
            const height = yScale(entry.length);
            const x = MARGIN.left + index * band + 3;
            const y = HEIGHT - MARGIN.bottom - height;
            return (
              <g key={index}>
                <rect x={x} y={y} width={Math.max(8, band - 6)} height={height} rx="10" className="chart-bar chart-bar--momentum" />
                <text x={x + 2} y={HEIGHT - 10} className="chart-label">
                  {entry.x0?.toFixed(0)}
                </text>
              </g>
            );
          })}
        </svg>
      ) : (
        <div className="empty-state">No particle tracks available.</div>
      )}
    </section>
  );
});

export default MomentumHistogram;
