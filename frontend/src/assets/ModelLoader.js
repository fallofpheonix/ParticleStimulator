/**
 * ModelLoader.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Loads GLTF / GLB 3D models for the detector geometry system.
 *
 * Features:
 *   • Draco mesh compression support (decoder path configurable)
 *   • MeshoptDecoder support for high-performance compressed meshes
 *   • Progress-aware loading via Three.js LoadingManager
 *   • Scene graph post-processing (shadows, material upgrades)
 *   • Instanced mesh extraction for calorimeter cell arrays
 *   • Animation clip extraction and retargeting helpers
 *
 * Usage:
 *   import { modelLoader } from './ModelLoader';
 *   import assetLoader from './AssetLoader';
 *
 *   assetLoader.registerModelLoader(modelLoader);
 *
 *   const { scene, animations } = await modelLoader.load('/models/detector.glb');
 *   const cloned = modelLoader.clone(scene);  // deep clone with shared geometries
 */

import * as THREE from 'three';
import { GLTFLoader }   from 'three/examples/jsm/loaders/GLTFLoader.js';
import { DRACOLoader }  from 'three/examples/jsm/loaders/DRACOLoader.js';

// ─── Draco decoder path (CDN fallback if local unavailable) ───────────────────
const DRACO_DECODER_PATH =
  typeof window !== 'undefined' && window.__DRACO_DECODER_PATH__
    ? window.__DRACO_DECODER_PATH__
    : 'https://www.gstatic.com/draco/versioned/decoders/1.5.6/';

// ─── Material upgrade config ──────────────────────────────────────────────────
const MATERIAL_UPGRADES = {
  detector: {
    metalness: 0.7,
    roughness: 0.3,
    envMapIntensity: 1.2,
  },
  calorimeter: {
    metalness: 0.4,
    roughness: 0.6,
    transparent: true,
    opacity: 0.85,
  },
  tracker: {
    metalness: 0.5,
    roughness: 0.4,
    transparent: true,
    opacity: 0.6,
    side: THREE.DoubleSide,
  },
};

// ─── LoaderPool — reuse loader instances ─────────────────────────────────────
class LoaderPool {
  #gltfLoader  = null;
  #dracoLoader = null;
  #manager;

  constructor(manager) {
    this.#manager = manager;
  }

  get gltf() {
    if (!this.#gltfLoader) {
      this.#gltfLoader = new GLTFLoader(this.#manager);
      this.#gltfLoader.setDRACOLoader(this.draco);
    }
    return this.#gltfLoader;
  }

  get draco() {
    if (!this.#dracoLoader) {
      this.#dracoLoader = new DRACOLoader();
      this.#dracoLoader.setDecoderPath(DRACO_DECODER_PATH);
      this.#dracoLoader.preload();
    }
    return this.#dracoLoader;
  }

  dispose() {
    this.#dracoLoader?.dispose();
    this.#dracoLoader = null;
    this.#gltfLoader  = null;
  }
}

// ─── ModelLoader class ────────────────────────────────────────────────────────
class ModelLoader {
  #manager;
  #pool;

  constructor() {
    this.#manager = new THREE.LoadingManager();
    this.#pool    = new LoaderPool(this.#manager);
  }

  /**
   * Load a GLTF/GLB file.
   * Returns { scene, animations, cameras, asset, parser }
   */
  async load(url, onProgress = null) {
    return new Promise((resolve, reject) => {
      this.#pool.gltf.load(
        url,
        (gltf) => {
          this.#postProcess(gltf.scene, url);
          resolve({
            scene:      gltf.scene,
            animations: gltf.animations ?? [],
            cameras:    gltf.cameras ?? [],
            asset:      gltf.asset,
            parser:     gltf.parser,
            url,
          });
        },
        (xhr) => {
          if (onProgress && xhr.lengthComputable) {
            onProgress(xhr.loaded, xhr.total);
          }
        },
        reject
      );
    });
  }

  /**
   * Deep-clone a scene, sharing geometries but cloning materials.
   * Preserves userData and name.
   */
  clone(scene) {
    const clone = scene.clone(true);
    clone.traverse((node) => {
      if (node.isMesh) {
        node.material = node.material.clone();
      }
    });
    return clone;
  }

  /**
   * Extract all meshes from a loaded scene, tagged by name.
   * Returns Map<name, THREE.Mesh>
   */
  extractMeshes(scene) {
    const meshes = new Map();
    scene.traverse((node) => {
      if (node.isMesh) meshes.set(node.name, node);
    });
    return meshes;
  }

  /**
   * Build an InstancedMesh from a source mesh + array of transforms.
   * Useful for calorimeter crystal arrays.
   */
  buildInstancedMesh(sourceMesh, transforms, material = null) {
    const count  = transforms.length;
    const geo    = sourceMesh.geometry;
    const mat    = material ?? sourceMesh.material.clone();
    const instanced = new THREE.InstancedMesh(geo, mat, count);
    instanced.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

    const dummy = new THREE.Object3D();
    transforms.forEach(({ position, rotation, scale }, i) => {
      dummy.position.set(...(position ?? [0, 0, 0]));
      dummy.rotation.set(...(rotation ?? [0, 0, 0]));
      dummy.scale.set(...(scale ?? [1, 1, 1]));
      dummy.updateMatrix();
      instanced.setMatrixAt(i, dummy.matrix);
    });

    instanced.instanceMatrix.needsUpdate = true;
    instanced.castShadow    = true;
    instanced.receiveShadow = true;
    return instanced;
  }

  buildPlaceholder(kind = "detector") {
    const scene = new THREE.Group();
    scene.name = `${kind}-placeholder`;

    const createRing = (radius, tube, color, opacity = 0.22) => {
      const mesh = new THREE.Mesh(
        new THREE.TorusGeometry(radius, tube, 18, 96),
        new THREE.MeshStandardMaterial({ color, transparent: true, opacity, metalness: 0.18, roughness: 0.52 })
      );
      mesh.rotation.x = Math.PI / 2;
      return mesh;
    };

    if (kind === "beam_pipe") {
      const mesh = new THREE.Mesh(
        new THREE.CylinderGeometry(0.18, 0.18, 8.5, 24, 1, true),
        new THREE.MeshStandardMaterial({ color: "#60a5fa", transparent: true, opacity: 0.18 })
      );
      mesh.rotation.z = Math.PI / 2;
      scene.add(mesh);
    } else if (kind === "calorimeter") {
      scene.add(createRing(2.6, 0.12, "#4b93c0", 0.18));
      scene.add(createRing(3.0, 0.12, "#7c3aed", 0.12));
    } else if (kind === "muon") {
      scene.add(createRing(3.8, 0.08, "#f59e0b", 0.16));
    } else {
      scene.add(createRing(1.1, 0.05, "#28557f", 0.24));
      scene.add(createRing(1.8, 0.05, "#36729f", 0.2));
      scene.add(createRing(2.7, 0.05, "#4b93c0", 0.18));
      scene.add(createRing(3.6, 0.05, "#7c3aed", 0.14));
    }

    return {
      scene,
      animations: [],
      cameras: [],
      asset: { generator: "placeholder", kind },
      parser: null,
      url: `placeholder://${kind}`,
    };
  }

  /**
   * Apply a preset material upgrade to all meshes matching a name pattern.
   */
  applyMaterialPreset(scene, pattern, presetKey) {
    const preset = MATERIAL_UPGRADES[presetKey];
    if (!preset) return;
    scene.traverse((node) => {
      if (node.isMesh && node.name.toLowerCase().includes(pattern)) {
        Object.assign(node.material, preset);
        node.material.needsUpdate = true;
      }
    });
  }

  /**
   * Post-process a loaded scene: enable shadows, frustum culling,
   * and upgrade materials for PBR consistency.
   */
  #postProcess(scene, url) {
    const basename = url.split('/').pop().replace(/\.\w+$/, '').toLowerCase();

    scene.traverse((node) => {
      if (node.isMesh) {
        node.castShadow    = true;
        node.receiveShadow = true;
        node.frustumCulled = true;

        // Upgrade standard materials
        if (node.material?.isMeshStandardMaterial) {
          node.material.needsUpdate = true;
        }

        // Auto-apply preset by name hint
        const name = node.name.toLowerCase();
        for (const key of Object.keys(MATERIAL_UPGRADES)) {
          if (name.includes(key) || basename.includes(key)) {
            Object.assign(node.material, MATERIAL_UPGRADES[key]);
          }
        }
      }
    });

    // Set scene name from URL
    scene.name = basename;
  }

  /**
   * Dispose all geometry and material references in a scene.
   * Call when permanently removing a model to avoid GPU memory leaks.
   */
  dispose(scene) {
    scene.traverse((node) => {
      if (node.isMesh) {
        node.geometry.dispose();
        if (Array.isArray(node.material)) {
          node.material.forEach(m => m.dispose());
        } else {
          node.material.dispose();
        }
      }
    });
  }
}

// ── Singleton export ──────────────────────────────────────────────────────────
export const modelLoader = new ModelLoader();
export default modelLoader;
