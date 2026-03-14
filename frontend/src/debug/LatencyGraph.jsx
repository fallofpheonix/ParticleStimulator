import { memo, useMemo } from "react";
import { area, line, max, scaleLinear } from "d3";

const WIDTH = 320;
const HEIGHT = 150;

const LatencyGraph = memo(function LatencyGraph({ history, wsStatus }) {
  const values = history.map((entry) => entry.latencyMs);
  const xScale = useMemo(() => scaleLinear().domain([0, Math.max(1, values.length - 1)]).range([12, WIDTH - 12]), [values.length]);
  const yScale = useMemo(() => scaleLinear().domain([0, max(values) ?? 100]).range([HEIGHT - 18, 12]), [values]);
  const curve = useMemo(() => line().x((_, index) => xScale(index)).y((value) => yScale(value))(values), [values, xScale, yScale]);
  const fill = useMemo(() => area().x((_, index) => xScale(index)).y0(HEIGHT - 18).y1((value) => yScale(value))(values), [values, xScale, yScale]);
  const latest = values.at(-1) ?? 0;

  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Simulation Latency</h3>
        <span>{latest.toFixed(1)} ms / {wsStatus}</span>
      </div>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="analytics-svg analytics-svg--small" role="img" aria-label="Simulation latency">
        {fill ? <path d={fill} fill="rgba(244,114,182,0.12)" /> : null}
        {curve ? <path d={curve} fill="none" stroke="#f472b6" strokeWidth="2.4" /> : null}
        {[16, 33, 100].map((threshold) => (
          <line key={threshold} x1="12" x2={WIDTH - 12} y1={yScale(threshold)} y2={yScale(threshold)} className="chart-grid-line" />
        ))}
      </svg>
    </section>
  );
});

export default LatencyGraph;
