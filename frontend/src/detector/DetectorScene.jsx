import { memo } from "react";

const DetectorScene = memo(function DetectorScene() {
  return (
    <group rotation={[Math.PI / 2, 0, 0]}>
      {[
        [1.2, "#28557f"],
        [2.1, "#36729f"],
        [3.1, "#4b93c0"]
      ].map(([radius, color]) => (
        <mesh key={radius} rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[radius, 0.035, 16, 64]} />
          <meshStandardMaterial color={color} transparent opacity={0.32} />
        </mesh>
      ))}
    </group>
  );
});

export default DetectorScene;
