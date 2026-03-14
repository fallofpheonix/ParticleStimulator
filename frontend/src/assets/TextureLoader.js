/**
 * TextureLoader.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Texture and environment map loader for the Particle Stimulator.
 *
 * Handles:
 *   • PNG / JPG / WebP sprite and PBR textures
 *   • HDR / EXR environment maps (RGBELoader / EXRLoader)
 *   • 1D color-ramp LUT textures for energy heatmaps
 *   • Procedurally generated fallback textures (no network needed)
 *   • sRGB vs linear colour-space configuration
 *   • Repeat / wrap mode configuration
 *   • Anisotropic filtering (uses renderer max)
 *
 * Usage:
 *   import { textureLoader } from './TextureLoader';
 *   import assetLoader from './AssetLoader';
 *
 *   assetLoader.registerTextureLoader(textureLoader);
 *
 *   const tex = await textureLoader.load('/textures/particle_glow.png', { sRGB: true });
 *   const hdr = await textureLoader.loadHDR('/envmaps/space.hdr');
 *   const lut = textureLoader.buildEnergyRamp();   // no network, instant
 */

import * as THREE from 'three';
import { RGBELoader } from 'three/examples/jsm/loaders/RGBELoader.js';
import { EXRLoader }  from 'three/examples/jsm/loaders/EXRLoader.js';

// ─── Anisotropy helper ────────────────────────────────────────────────────────
let _maxAnisotropy = 8;
export function setMaxAnisotropy(renderer) {
  _maxAnisotropy = renderer.capabilities.getMaxAnisotropy();
}

// ─── Wrap mode shortcuts ──────────────────────────────────────────────────────
export const WrapMode = Object.freeze({
  CLAMP:  THREE.ClampToEdgeWrapping,
  REPEAT: THREE.RepeatWrapping,
  MIRROR: THREE.MirroredRepeatWrapping,
});

// ─── Default texture options ──────────────────────────────────────────────────
const DEFAULT_OPTIONS = {
  sRGB:        false,
  mipmap:      true,
  anisotropy:  true,
  repeat:      true,
  wrapS:       WrapMode.REPEAT,
  wrapT:       WrapMode.REPEAT,
  minFilter:   THREE.LinearMipmapLinearFilter,
  magFilter:   THREE.LinearFilter,
  flipY:       true,
};

// ─── TextureLoader class ──────────────────────────────────────────────────────
class ParticleTextureLoader {
  #loader;
  #rgbeLoader;
  #exrLoader;

  constructor() {
    this.#loader     = new THREE.TextureLoader();
    this.#rgbeLoader = new RGBELoader();
    this.#exrLoader  = new EXRLoader();
  }

  /**
   * Load a 2D texture (PNG / JPG / WebP).
   */
  async load(url, options = {}, onProgress = null) {
    const opts = { ...DEFAULT_OPTIONS, ...options };

    return new Promise((resolve, reject) => {
      this.#loader.load(
        url,
        (texture) => {
          this.#configure(texture, opts);
          resolve(texture);
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
   * Load an HDR environment map (.hdr via RGBELoader).
   * Returns a DataTexture ready for scene.environment / scene.background.
   */
  async loadHDR(url, onProgress = null) {
    return new Promise((resolve, reject) => {
      this.#rgbeLoader.load(
        url,
        (texture) => {
          texture.mapping = THREE.EquirectangularReflectionMapping;
          resolve(texture);
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
   * Load an EXR environment map (.exr via EXRLoader).
   */
  async loadEXR(url, onProgress = null) {
    return new Promise((resolve, reject) => {
      this.#exrLoader.load(
        url,
        (texture) => {
          texture.mapping = THREE.EquirectangularReflectionMapping;
          resolve(texture);
        },
        (xhr) => {
          if (onProgress && xhr.lengthComputable) onProgress(xhr.loaded, xhr.total);
        },
        reject
      );
    });
  }

  // ─── Procedural texture generators ─────────────────────────────────────────
  // These produce fallback textures with no network dependency,
  // useful for offline/dev mode and unit tests.

  /**
   * Radial soft-glow sprite — white centre fading to transparent.
   * Used as particle billboard sprite.
   */
  buildGlowSprite(size = 128, color = { r: 1, g: 1, b: 1 }) {
    const data   = new Uint8Array(size * size * 4);
    const center = size / 2;

    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        const dx   = (x - center) / center;
        const dy   = (y - center) / center;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const glow = Math.max(0, 1 - dist);
        const a    = Math.pow(glow, 2.2) * 255;
        const idx  = (y * size + x) * 4;
        data[idx]     = color.r * 255;
        data[idx + 1] = color.g * 255;
        data[idx + 2] = color.b * 255;
        data[idx + 3] = a;
      }
    }

    const texture       = new THREE.DataTexture(data, size, size, THREE.RGBAFormat);
    texture.needsUpdate = true;
    texture.premultiplyAlpha = true;
    return texture;
  }

  /**
   * 1D energy colour-ramp LUT.
   * Maps [0, 1] → (blue → cyan → green → yellow → red) for heatmap shaders.
   */
  buildEnergyRamp(width = 256) {
    const data = new Uint8Array(width * 4);

    const stops = [
      [0.00, [0,   0,   160]],
      [0.20, [0,   80,  255]],
      [0.40, [0,   220, 220]],
      [0.60, [0,   255, 60 ]],
      [0.75, [255, 220, 0  ]],
      [0.90, [255, 80,  0  ]],
      [1.00, [255, 0,   0  ]],
    ];

    for (let i = 0; i < width; i++) {
      const t = i / (width - 1);
      let lo = stops[0], hi = stops[stops.length - 1];
      for (let s = 0; s < stops.length - 1; s++) {
        if (t >= stops[s][0] && t <= stops[s + 1][0]) {
          lo = stops[s];
          hi = stops[s + 1];
          break;
        }
      }
      const f   = lo[0] === hi[0] ? 0 : (t - lo[0]) / (hi[0] - lo[0]);
      const idx = i * 4;
      data[idx]     = Math.round(lo[1][0] + (hi[1][0] - lo[1][0]) * f);
      data[idx + 1] = Math.round(lo[1][1] + (hi[1][1] - lo[1][1]) * f);
      data[idx + 2] = Math.round(lo[1][2] + (hi[1][2] - lo[1][2]) * f);
      data[idx + 3] = 255;
    }

    const texture         = new THREE.DataTexture(data, width, 1, THREE.RGBAFormat);
    texture.wrapS         = THREE.ClampToEdgeWrapping;
    texture.wrapT         = THREE.ClampToEdgeWrapping;
    texture.minFilter     = THREE.LinearFilter;
    texture.magFilter     = THREE.LinearFilter;
    texture.needsUpdate   = true;
    return texture;
  }

  /**
   * White noise texture — useful for dithering and volumetric FX.
   */
  buildNoiseTexture(size = 256) {
    const data = new Uint8Array(size * size * 4);
    for (let i = 0; i < data.length; i++) data[i] = Math.random() * 255;
    const texture       = new THREE.DataTexture(data, size, size, THREE.RGBAFormat);
    texture.wrapS       = THREE.RepeatWrapping;
    texture.wrapT       = THREE.RepeatWrapping;
    texture.needsUpdate = true;
    return texture;
  }

  /**
   * Grid / checker pattern — useful for detector geometry debug views.
   */
  buildCheckerTexture(size = 256, divisions = 16) {
    const data      = new Uint8Array(size * size * 4);
    const cellSize  = size / divisions;

    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        const cx  = Math.floor(x / cellSize);
        const cy  = Math.floor(y / cellSize);
        const val = (cx + cy) % 2 === 0 ? 40 : 80;
        const idx = (y * size + x) * 4;
        data[idx]     = val;
        data[idx + 1] = val + 20;
        data[idx + 2] = val + 30;
        data[idx + 3] = 255;
      }
    }

    const texture       = new THREE.DataTexture(data, size, size, THREE.RGBAFormat);
    texture.needsUpdate = true;
    return texture;
  }

  buildEnvironmentMap(kind = "space", width = 64, height = 32) {
    const data = new Uint8Array(width * height * 4);
    const palette =
      kind === "lab"
        ? [[18, 42, 71], [46, 105, 168], [139, 176, 214]]
        : [[2, 8, 18], [11, 30, 61], [108, 178, 255]];
    for (let y = 0; y < height; y++) {
      const t = y / Math.max(1, height - 1);
      for (let x = 0; x < width; x++) {
        const noise = ((Math.sin((x + 1) * 0.27) + 1) * 0.5) * 0.08;
        const idx = (y * width + x) * 4;
        data[idx] = Math.round(palette[0][0] * (1 - t) + palette[2][0] * t);
        data[idx + 1] = Math.round((palette[0][1] * (1 - t) + palette[2][1] * t) * (1 + noise));
        data[idx + 2] = Math.round((palette[1][2] * (1 - t) + palette[2][2] * t) * (1 + noise));
        data[idx + 3] = 255;
      }
    }
    const texture = new THREE.DataTexture(data, width, height, THREE.RGBAFormat);
    texture.mapping = THREE.EquirectangularReflectionMapping;
    texture.needsUpdate = true;
    return texture;
  }

  buildProcedural(kind, options = {}) {
    switch (kind) {
      case "glow":
        return this.buildGlowSprite(options.size ?? 128, options.color);
      case "energyRamp":
        return this.buildEnergyRamp(options.width ?? 256);
      case "noise":
        return this.buildNoiseTexture(options.size ?? 256);
      case "checker":
        return this.buildCheckerTexture(options.size ?? 256, options.divisions ?? 16);
      default:
        return this.buildCheckerTexture(64, 8);
    }
  }

  /**
   * Apply all configuration options to a loaded THREE.Texture.
   */
  #configure(texture, opts) {
    if (opts.sRGB) {
      texture.colorSpace = THREE.SRGBColorSpace;
    } else {
      texture.colorSpace = THREE.LinearSRGBColorSpace;
    }

    texture.generateMipmaps = opts.mipmap ?? true;
    texture.minFilter       = opts.minFilter ?? (opts.mipmap
      ? THREE.LinearMipmapLinearFilter
      : THREE.LinearFilter);
    texture.magFilter       = opts.magFilter ?? THREE.LinearFilter;

    if (opts.anisotropy) {
      texture.anisotropy = _maxAnisotropy;
    }

    texture.wrapS = opts.wrapS ?? WrapMode.REPEAT;
    texture.wrapT = opts.wrapT ?? WrapMode.REPEAT;
    texture.flipY = opts.flipY ?? true;

    texture.needsUpdate = true;
    return texture;
  }

  dispose(texture) {
    texture?.dispose();
  }
}

// ── Singleton export ──────────────────────────────────────────────────────────
export const textureLoader = new ParticleTextureLoader();
export default textureLoader;
