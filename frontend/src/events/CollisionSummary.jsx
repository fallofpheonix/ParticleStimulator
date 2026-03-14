import { memo } from "react";

const Gauge = memo(function Gauge({ label, value, max, unit, color }) {
  const pct = Math.min(100, (value / Math.max(max, 1)) * 100);

  return (
    <div className="gauge">
      <div className="gauge-header">
        <span className="gauge-label">{label}</span>
        <span className="gauge-value" style={{ color }}>
          {typeof value === "number" ? value.toFixed(value < 10 ? 2 : 0) : value}
          {unit ? <span className="gauge-unit"> {unit}</span> : null}
        </span>
      </div>
      <div className="gauge-track">
        <div className="gauge-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
});

const CollisionSummary = memo(function CollisionSummary({ event }) {
  const collision = event?.collision ?? {};
  const energy = event?.collision_energy ?? 0;
  const mass = collision.mass ?? 0;
  const jets = collision.jets ?? 0;
  const muons = collision.muons ?? 0;
  const particles = event?.particles ?? [];
  const muonCount = particles.filter((particle) => particle.type?.startsWith("muon") || particle.type === "muon").length;
  const photonCount = particles.filter((particle) => particle.type === "photon").length;

  return (
    <div className="collision-summary">
      <div className="cs-title">Collision Summary</div>
      <div className="cs-gauges">
        <Gauge label="Inv. Mass" value={mass} max={250} unit="GeV" color="#ff6b9d" />
        <Gauge label="Jets" value={jets} max={10} color="#ffe566" />
        <Gauge label="Muons" value={muons || muonCount} max={8} color="#5ce1e6" />
        <Gauge label="Energy" value={energy / 1000} max={14} unit="TeV" color="#73b4ff" />
      </div>
      <div className="cs-stats">
        <div className="cs-stat">
          <span className="cs-stat-label">particles</span>
          <span className="cs-stat-val">{particles.length}</span>
        </div>
        <div className="cs-stat">
          <span className="cs-stat-label">photons</span>
          <span className="cs-stat-val">{photonCount}</span>
        </div>
        <div className="cs-stat">
          <span className="cs-stat-label">event id</span>
          <span className="cs-stat-val">#{event?.event_id ?? "n/a"}</span>
        </div>
      </div>
    </div>
  );
});

export default CollisionSummary;
