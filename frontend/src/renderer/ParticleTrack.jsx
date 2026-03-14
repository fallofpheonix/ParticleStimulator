import { memo, useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";

const TRACK_COLORS = {
  electron: "#00d4ff",
  positron: "#ff6b35",
  muon: "#b44fff",
  antimuon: "#ff44bb",
  photon: "#fffb00",
  proton: "#44ff88",
  neutron: "#94a3b8",
  pion: "#ff8844",
  kaon: "#44ffcc",
  default: "#ffffff"
};

const buildPoints = (particle, steps = 36, maxRadius = 5) => {
  const px = particle?.px ?? particle?.momentum?.x ?? 0;
  const py = particle?.py ?? particle?.momentum?.y ?? 0;
  const pz = particle?.pz ?? particle?.momentum?.z ?? 0;
  const magnitude = Math.sqrt(px ** 2 + py ** 2 + pz ** 2) || 1;
  const nx = px / magnitude;
  const ny = py / magnitude;
  const nz = pz / magnitude;
  const points = [];

  for (let index = 0; index <= steps; index += 1) {
    const t = (index / steps) * maxRadius;
    const wobble = Math.sin(index * 0.18 + magnitude) * 0.09;
    points.push(new THREE.Vector3(nx * t + wobble, ny * t + wobble * 0.4, nz * t));
  }

  return points;
};

const ParticleTrack = memo(function ParticleTrack({ particle }) {
  const lineRef = useRef(null);
  const [drawRange, setDrawRange] = useState(0);
  const points = useMemo(() => buildPoints(particle), [particle]);
  const color = TRACK_COLORS[particle?.type] || TRACK_COLORS.default;
  const geometry = useMemo(() => new THREE.BufferGeometry().setFromPoints(points), [points]);

  useEffect(() => {
    setDrawRange(0);
    const handle = window.setInterval(() => {
      setDrawRange((current) => {
        if (current >= points.length) {
          window.clearInterval(handle);
          return current;
        }
        return current + 2;
      });
    }, 16);
    return () => window.clearInterval(handle);
  }, [points.length]);

  useEffect(() => {
    geometry.setDrawRange(0, drawRange);
  }, [drawRange, geometry]);

  return (
    <line ref={lineRef} geometry={geometry}>
      <lineBasicMaterial color={color} transparent opacity={0.9} />
    </line>
  );
});

export default ParticleTrack;
