import { memo } from "react";

const LAYERS = [
  [1.1, "#28557f", 0.24],
  [1.8, "#36729f", 0.2],
  [2.7, "#4b93c0", 0.18],
  [3.6, "#7c3aed", 0.14]
];

const DetectorGeometry = memo(function DetectorGeometry() {
  return (
    <group rotation={[Math.PI / 2, 0, 0]}>
      {LAYERS.map(([radius, color, opacity]) => (
        <mesh key={radius} rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[radius, 0.05, 18, 96]} />
          <meshStandardMaterial color={color} transparent opacity={opacity} roughness={0.4} metalness={0.1} />
        </mesh>
      ))}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.18, 0.18, 8.5, 24, 1, true]} />
        <meshStandardMaterial color="#60a5fa" transparent opacity={0.18} />
      </mesh>
    </group>
  );
});

export default DetectorGeometry;
