import { memo, useMemo } from "react";
import { interpolatePlasma, scaleLinear } from "d3";

const WIDTH = 560;
const HEIGHT = 240;
const ETA_BINS = 12;
const PHI_BINS = 14;

const magnitude = (particle) =>
  Math.sqrt((particle.px ?? 0) ** 2 + (particle.py ?? 0) ** 2 + (particle.pz ?? 0) ** 2);

const toEta = (particle) => {
  const p = magnitude(particle);
  const numerator = p + (particle.pz ?? 0);
  const denominator = Math.max(1e-6, p - (particle.pz ?? 0));
  return 0.5 * Math.log(Math.max(1e-6, numerator / denominator));
};

const DetectorHeatmap = memo(function DetectorHeatmap({ events }) {
  const cells = useMemo(() => {
    const grid = Array.from({ length: ETA_BINS * PHI_BINS }, (_, index) => ({
      eta: Math.floor(index / PHI_BINS),
      phi: index % PHI_BINS,
      energy: 0
    }));

    for (const event of events) {
      for (const particle of event.particles ?? []) {
        const eta = Math.max(-3, Math.min(3, toEta(particle)));
        const phi = Math.atan2(particle.py ?? 0, particle.px ?? 0);
        const etaIndex = Math.min(ETA_BINS - 1, Math.max(0, Math.floor(((eta + 3) / 6) * ETA_BINS)));
        const phiIndex = Math.min(PHI_BINS - 1, Math.max(0, Math.floor(((phi + Math.PI) / (Math.PI * 2)) * PHI_BINS)));
        grid[etaIndex * PHI_BINS + phiIndex].energy += magnitude(particle);
      }
    }
    return grid;
  }, [events]);

  const maxEnergy = Math.max(1, ...cells.map((cell) => cell.energy));
  const colorScale = scaleLinear().domain([0, maxEnergy]).range([0.08, 1]);
  const cellWidth = WIDTH / PHI_BINS;
  const cellHeight = (HEIGHT - 32) / ETA_BINS;

  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Detector Heatmap</h3>
        <span>calorimeter eta x phi</span>
      </div>
      <svg className="histogram-svg analytics-svg" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="Detector heatmap">
        {cells.map((cell) => (
          <rect
            key={`${cell.eta}-${cell.phi}`}
            x={cell.phi * cellWidth + 2}
            y={cell.eta * cellHeight + 2}
            width={cellWidth - 4}
            height={cellHeight - 4}
            rx="6"
            fill={interpolatePlasma(colorScale(cell.energy))}
            className="heatmap-cell"
          />
        ))}
        <g transform={`translate(18 ${HEIGHT - 18})`}>
          {Array.from({ length: 6 }).map((_, index) => (
            <rect key={index} x={index * 48} y="0" width="48" height="10" fill={interpolatePlasma(index / 5)} />
          ))}
        </g>
      </svg>
    </section>
  );
});

export default DetectorHeatmap;
