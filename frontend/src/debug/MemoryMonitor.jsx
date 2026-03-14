import { memo, useMemo } from "react";
import { line, max, scaleLinear } from "d3";

const WIDTH = 320;
const HEIGHT = 150;

const MemoryMonitor = memo(function MemoryMonitor({ history }) {
  const heap = history.map((entry) => entry.heapMb);
  const gpu = history.map((entry) => entry.gpuMb);
  const peak = Math.max(max(heap) ?? 1, max(gpu) ?? 1);
  const xScale = useMemo(() => scaleLinear().domain([0, Math.max(1, history.length - 1)]).range([12, WIDTH - 12]), [history.length]);
  const yScale = useMemo(() => scaleLinear().domain([0, peak]).range([HEIGHT - 18, 12]), [peak]);
  const heapPath = useMemo(() => line().x((_, i) => xScale(i)).y((value) => yScale(value))(heap), [heap, xScale, yScale]);
  const gpuPath = useMemo(() => line().x((_, i) => xScale(i)).y((value) => yScale(value))(gpu), [gpu, xScale, yScale]);

  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Memory Usage</h3>
        <span>{(heap.at(-1) ?? 0).toFixed(1)} MB heap</span>
      </div>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="analytics-svg analytics-svg--small" role="img" aria-label="Memory usage">
        {heapPath ? <path d={heapPath} fill="none" stroke="#60a5fa" strokeWidth="2.4" /> : null}
        {gpuPath ? <path d={gpuPath} fill="none" stroke="#c084fc" strokeWidth="2.4" /> : null}
      </svg>
      <div className="legend">
        <span><i className="swatch" style={{ background: "#60a5fa" }} /> JS Heap</span>
        <span><i className="swatch" style={{ background: "#c084fc" }} /> GPU VRAM</span>
      </div>
    </section>
  );
});

export default MemoryMonitor;
