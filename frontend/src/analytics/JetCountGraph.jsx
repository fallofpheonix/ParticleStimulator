import { memo, useMemo } from "react";
import { max, scaleLinear } from "d3";

const WIDTH = 280;
const HEIGHT = 220;

const JetCountGraph = memo(function JetCountGraph({ events }) {
  const yScale = useMemo(
    () => scaleLinear().domain([0, max(events, (event) => event.collision?.jets ?? event.jets ?? 0) ?? 1]).range([0, 150]),
    [events]
  );

  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Jet Count</h3>
        <span>per event</span>
      </div>
      {events.length ? (
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="analytics-svg analytics-svg--small" role="img" aria-label="Jet count per event">
          {events.slice(-12).map((event, index) => {
            const barWidth = 18;
            const height = yScale(event.collision?.jets ?? event.jets ?? 0);
            const x = 18 + index * 20;
            const y = 170 - height;
            return (
              <g key={event.event_id ?? index}>
                <rect x={x} y={y} width={barWidth} height={height} rx="8" className="chart-bar chart-bar--jets" />
                <text x={x + 4} y="190" className="chart-label">
                  {event.collision?.jets ?? event.jets ?? 0}
                </text>
              </g>
            );
          })}
        </svg>
      ) : (
        <div className="empty-state">No jet statistics yet.</div>
      )}
    </section>
  );
});

export default JetCountGraph;
