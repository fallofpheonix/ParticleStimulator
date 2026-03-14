import { memo, useMemo } from "react";
import * as THREE from "three";

const JetCone = memo(function JetCone({ direction, energy = 1, color = "#f97316" }) {
  const vector = useMemo(() => {
    const next = new THREE.Vector3(...direction);
    return next.lengthSq() ? next.normalize() : new THREE.Vector3(0, 0, 1);
  }, [direction]);
  const quaternion = useMemo(
    () => new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), vector),
    [vector]
  );
  const scale = Math.min(2.8, 0.6 + energy * 0.15);
  const midpoint = useMemo(() => vector.clone().multiplyScalar(scale * 0.45), [scale, vector]);

  return (
    <group position={midpoint} quaternion={quaternion}>
      <mesh rotation={[Math.PI, 0, 0]}>
        <coneGeometry args={[0.28 + energy * 0.05, scale, 18, 1, true]} />
        <meshStandardMaterial color={color} transparent opacity={0.12} />
      </mesh>
      <line>
        <bufferGeometry attach="geometry">
          <bufferAttribute
            attach="attributes-position"
            array={new Float32Array([0, -scale * 0.5, 0, 0, scale * 0.5, 0])}
            count={2}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial color={color} transparent opacity={0.5} />
      </line>
    </group>
  );
});

export default JetCone;
