import { memo, useMemo } from "react";
import * as THREE from "three";

import { useShaderMaterial, useTexture } from "@assets";

const CollisionPoint = memo(function CollisionPoint({ position = [0, 0, 0] }) {
  const emissive = useMemo(() => new THREE.Color("#ff5d73"), []);
  const { asset: glowTexture } = useTexture("particle_glow");
  const glowUniforms = useMemo(
    () => ({
      uGlowTex: { value: glowTexture },
      uColor: { value: new THREE.Color("#ff5d73") },
      uIntensity: { value: 1.85 },
      uOpacity: { value: 0.72 },
    }),
    [glowTexture]
  );
  const glowMaterial = useShaderMaterial("glowShader", glowUniforms, {
    depthWrite: false,
    transparent: true,
  });

  return (
    <group position={position}>
      <pointLight color="#ff8da1" intensity={28} distance={8} />
      <mesh>
        <sphereGeometry args={[0.16, 24, 24]} />
        <meshStandardMaterial color="#ffd0d8" emissive={emissive} emissiveIntensity={2.2} />
      </mesh>
      <mesh>
        <torusGeometry args={[0.34, 0.016, 12, 64]} />
        <meshBasicMaterial color="#ff8da1" transparent opacity={0.5} />
      </mesh>
      {glowMaterial ? (
        <mesh>
          <planeGeometry args={[1.4, 1.4]} />
          <primitive attach="material" object={glowMaterial} />
        </mesh>
      ) : null}
    </group>
  );
});

export default CollisionPoint;
