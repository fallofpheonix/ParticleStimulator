import { memo, useLayoutEffect, useMemo, useRef } from "react";
import { Canvas } from "@react-three/fiber";
import { Grid, OrbitControls, Stars } from "@react-three/drei";
import * as THREE from "three";

import { selectSelectedEvent } from "@app/selectors";
import { useSimulationStore } from "@store/simulationStore";

import CollisionPoint from "./CollisionPoint.jsx";
import DetectorGeometry from "./DetectorGeometry.jsx";
import JetCone from "./JetCone.jsx";
import ParticleTrack from "./ParticleTrack.jsx";

const SCALE = 18;

function ParticleInstances({ particles, highlightIds }) {
  const meshRef = useRef(null);
  const color = useMemo(() => new THREE.Color(), []);
  const particlesMemo = useMemo(() => particles, [particles]);

  useLayoutEffect(() => {
    const mesh = meshRef.current;
    if (!mesh) {
      return;
    }

    const matrix = new THREE.Matrix4();
    for (let index = 0; index < particlesMemo.length; index += 1) {
      const particle = particlesMemo[index];
      const position = particle.position ?? { x: 0, y: 0, z: 0 };
      const radius = highlightIds.has(particle.particle_id) ? 0.16 : particle.alive ? 0.11 : 0.08;
      matrix.compose(
        new THREE.Vector3(position.x * SCALE, position.y * SCALE, position.z * SCALE),
        new THREE.Quaternion(),
        new THREE.Vector3(radius, radius, radius)
      );
      mesh.setMatrixAt(index, matrix);
      color.set(highlightIds.has(particle.particle_id) ? "#ff5d73" : particle.alive ? "#73b4ff" : "#5ce1e6");
      mesh.setColorAt(index, color);
    }
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) {
      mesh.instanceColor.needsUpdate = true;
    }
  }, [particlesMemo, highlightIds, color]);

  if (!particlesMemo.length) {
    return null;
  }

  return (
    <instancedMesh ref={meshRef} args={[null, null, particlesMemo.length]}>
      <sphereGeometry args={[1, 16, 16]} />
      <meshStandardMaterial vertexColors roughness={0.3} metalness={0.1} />
    </instancedMesh>
  );
}

const SceneContents = memo(function SceneContents({ particles, highlightIds }) {
  const highlightedParticles = particles.filter((particle) => highlightIds.has(particle.particle_id));

  return (
    <>
      <ambientLight intensity={0.45} />
      <pointLight position={[6, 8, 12]} intensity={28} color="#9acaff" />
      <pointLight position={[-8, -6, 4]} intensity={16} color="#ffb787" />
      <Stars radius={48} depth={36} count={1800} factor={2.8} saturation={0} fade speed={0.4} />
      <group rotation={[-0.38, 0.28, 0]}>
        <DetectorGeometry />
        <CollisionPoint />
        <ParticleInstances particles={particles} highlightIds={highlightIds} />
        {highlightedParticles.map((particle) => (
          <ParticleTrack
            key={`track-${particle.particle_id}`}
            particle={{
              type: particle.species,
              momentum: particle.velocity,
              position: particle.position
            }}
          />
        ))}
        {highlightedParticles.map((particle) => (
          <JetCone
            key={`jet-${particle.particle_id}`}
            direction={[particle.velocity.x, particle.velocity.y, particle.velocity.z]}
            energy={particle.kinetic_energy_gev ?? 1}
            color="#ff8a5b"
          />
        ))}
      </group>
      <Grid
        args={[20, 20]}
        cellSize={1}
        cellThickness={0.3}
        cellColor="#1b3956"
        sectionSize={5}
        sectionThickness={0.8}
        sectionColor="#2b6aa1"
        fadeDistance={28}
        fadeStrength={1.2}
        position={[0, -3.5, 0]}
      />
    </>
  );
});

const ParticleScene = memo(function ParticleScene() {
  const payload = useSimulationStore((state) => state.simulationState.payload);
  const selectedEvent = useSimulationStore(selectSelectedEvent);
  const renderPaused = useSimulationStore((state) => state.uiLayout.renderPaused);
  const particles = payload?.final_particles ?? [];
  const highlightIds = useMemo(() => new Set(selectedEvent?.product_ids ?? []), [selectedEvent]);

  return (
    <>
      <div className="panel-header">
        <h2>Particle Scene</h2>
        <p>Instanced 3D particle rendering fed from simulation payloads</p>
      </div>
      <div className="scene-shell">
        <Canvas camera={{ position: [0, 1.6, 8.2], fov: 42 }} frameloop={renderPaused ? "never" : "always"}>
          <SceneContents particles={particles} highlightIds={highlightIds} />
          <OrbitControls enablePan enableZoom enableRotate autoRotate autoRotateSpeed={0.2} />
        </Canvas>
        <div className="legend">
          <span><i className="swatch beam-a" /> Active Particles</span>
          <span><i className="swatch beam-b" /> Detector Layers</span>
          <span><i className="swatch collision" /> Selected Event</span>
          <span>{renderPaused ? "Renderer paused" : "Renderer live"}</span>
        </div>
      </div>
    </>
  );
});

export default ParticleScene;
