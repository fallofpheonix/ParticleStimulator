import { memo, useEffect, useMemo, useRef, useState } from "react";
import { extent, line, scaleLinear, select, zoom, zoomIdentity } from "d3";

const WIDTH = 560;
const HEIGHT = 220;
const MARGIN = { top: 16, right: 16, bottom: 28, left: 42 };

const EnergyGraph = memo(function EnergyGraph({ events }) {
  const svgRef = useRef(null);
  const [transform, setTransform] = useState(zoomIdentity);

  const points = useMemo(
    () =>
      [...events]
        .sort((left, right) => (left.timestamp ?? left.time_s ?? 0) - (right.timestamp ?? right.time_s ?? 0))
        .map((event, index) => ({
          x: event.timestamp ?? (event.time_s ?? index) * 1000,
          y: event.collision_energy ?? 0
        })),
    [events]
  );

  const xBase = useMemo(() => {
    const [min, max] = extent(points, (point) => point.x);
    return scaleLinear().domain([min ?? 0, max ?? 1]).range([MARGIN.left, WIDTH - MARGIN.right]);
  }, [points]);

  const yScale = useMemo(() => {
    const [, max] = extent(points, (point) => point.y);
    return scaleLinear().domain([0, max ?? 1]).nice().range([HEIGHT - MARGIN.bottom, MARGIN.top]);
  }, [points]);

  const xScale = useMemo(() => transform.rescaleX(xBase), [transform, xBase]);

  useEffect(() => {
    if (!svgRef.current) {
      return undefined;
    }
    const behavior = zoom()
      .scaleExtent([1, 10])
      .translateExtent([
        [MARGIN.left, 0],
        [WIDTH - MARGIN.right, HEIGHT]
      ])
      .on("zoom", (event) => setTransform(event.transform));
    const selection = select(svgRef.current);
    selection.call(behavior);
    return () => {
      selection.on(".zoom", null);
    };
  }, []);

  const graphLine = useMemo(
    () =>
      line()
        .x((point) => xScale(point.x))
        .y((point) => yScale(point.y))(points),
    [points, xScale, yScale]
  );

  const latest = points[points.length - 1];

  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Collision Energy</h3>
        <span>{latest ? `${(latest.y / 1000).toFixed(2)} TeV` : "idle"}</span>
      </div>
      <svg ref={svgRef} className="histogram-svg analytics-svg" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="Collision energy over time">
        <defs>
          <linearGradient id="energy-gradient" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#7dd3fc" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#7dd3fc" stopOpacity="0.08" />
          </linearGradient>
        </defs>
        {Array.from({ length: 4 }).map((_, index) => {
          const y = MARGIN.top + ((HEIGHT - MARGIN.top - MARGIN.bottom) / 3) * index;
          return <line key={index} x1={MARGIN.left} x2={WIDTH - MARGIN.right} y1={y} y2={y} className="chart-grid-line" />;
        })}
        {graphLine ? (
          <>
            <path
              d={`${graphLine} L ${xScale(points[points.length - 1].x)} ${HEIGHT - MARGIN.bottom} L ${xScale(points[0].x)} ${HEIGHT - MARGIN.bottom} Z`}
              fill="url(#energy-gradient)"
              className="chart-area"
            />
            <path d={graphLine} fill="none" stroke="#7dd3fc" strokeWidth="3" className="chart-line" />
          </>
        ) : null}
        {points.map((point, index) => (
          <circle key={index} cx={xScale(point.x)} cy={yScale(point.y)} r="3.2" fill="#f97316" className="chart-point" />
        ))}
      </svg>
      <p className="chart-footnote">Wheel to zoom, drag to pan.</p>
    </section>
  );
});

export default EnergyGraph;
