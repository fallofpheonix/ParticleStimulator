import { memo, useMemo } from "react";

import { particleColor } from "./colors.js";

const magnitude = (particle) =>
  Math.sqrt((particle.px ?? 0) ** 2 + (particle.py ?? 0) ** 2 + (particle.pz ?? 0) ** 2);

const MomentumBar = memo(function MomentumBar({ value, max }) {
  const pct = Math.min(100, (value / Math.max(max, 1)) * 100);
  return (
    <div className="mom-track">
      <div className="mom-fill" style={{ width: `${pct}%` }} />
    </div>
  );
});

const ParticleList = memo(function ParticleList({ particles }) {
  const momenta = useMemo(() => (particles ?? []).map((particle) => magnitude(particle)), [particles]);
  const maxMomentum = Math.max(...momenta, 1);

  if (!particles?.length) {
    return null;
  }

  return (
    <div className="particle-list">
      <div className="pl-header">
        <span>Type</span>
        <span>px</span>
        <span>py</span>
        <span>pz</span>
        <span>|p|</span>
      </div>
      {particles.map((particle, index) => {
        const color = particleColor(particle.type);
        const momentum = momenta[index];
        return (
          <div key={`${particle.type}-${index}`} className="pl-row">
            <span className="pl-type" style={{ color }}>
              <span className="pl-bullet" style={{ background: color }} />
              {particle.type}
            </span>
            <span className="pl-val">{(particle.px ?? 0).toFixed(2)}</span>
            <span className="pl-val">{(particle.py ?? 0).toFixed(2)}</span>
            <span className="pl-val">{(particle.pz ?? 0).toFixed(2)}</span>
            <span className="pl-mom">
              <MomentumBar value={momentum} max={maxMomentum} />
              <span>{momentum.toFixed(2)}</span>
            </span>
          </div>
        );
      })}
    </div>
  );
});

export default ParticleList;
