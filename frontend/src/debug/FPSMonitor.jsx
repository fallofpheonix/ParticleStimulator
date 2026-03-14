import { memo, useMemo } from "react";
import { area, line, max, scaleLinear } from "d3";

const WIDTH = 320;
const HEIGHT = 150;

const FPSMonitor = memo(function FPSMonitor({ history, statsNode }) {
  const values = history.map((entry) => entry.fps);
  const xScale = useMemo(() => scaleLinear().domain([0, Math.max(1, values.length - 1)]).range([12, WIDTH - 12]), [values.length]);
  const yScale = useMemo(() => scaleLinear().domain([0, max(values) ?? 60]).range([HEIGHT - 18, 12]), [values]);
  const curve = useMemo(
    () => line().x((_, index) => xScale(index)).y((value) => yScale(value))(values),
    [values, xScale, yScale]
  );
  const fill = useMemo(
    () => area().x((_, index) => xScale(index)).y0(HEIGHT - 18).y1((value) => yScale(value))(values),
    [values, xScale, yScale]
  );
  const latest = values.at(-1) ?? 0;

  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>FPS Monitor</h3>
        <span>{latest.toFixed(1)} fps</span>
      </div>
      <div className="debug-inline-meter" ref={statsNode} />
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="analytics-svg analytics-svg--small" role="img" aria-label="Frames per second">
        {fill ? <path d={fill} fill="rgba(34,197,94,0.14)" /> : null}
        {curve ? <path d={curve} fill="none" stroke={latest < 30 ? "#fb7185" : latest < 55 ? "#f59e0b" : "#4ade80"} strokeWidth="2.5" /> : null}
        <line x1="12" x2={WIDTH - 12} y1={yScale(60)} y2={yScale(60)} className="chart-grid-line" />
      </svg>
    </section>
  );
});

export default FPSMonitor;
