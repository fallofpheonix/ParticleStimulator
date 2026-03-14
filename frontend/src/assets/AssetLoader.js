/**
 * AssetLoader.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Central asset pipeline for the Particle Stimulator visualization system.
 *
 * Responsibilities:
 *   • Unified registry of all asset manifests (models, textures, shaders, envmaps)
 *   • LRU cache with configurable size cap and TTL eviction
 *   • Preload queue with prioritisation (CRITICAL → HIGH → NORMAL → LAZY)
 *   • Progress tracking with per-asset and aggregate callbacks
 *   • Retry logic with exponential back-off
 *   • Lazy-load API returning Promises that resolve on first access
 *
 * Usage:
 *   import { assetLoader } from './AssetLoader';
 *
 *   // Preload a named bundle
 *   await assetLoader.preloadBundle('core');
 *
 *   // Lazy-load a single asset
 *   const texture = await assetLoader.load('particle_glow');
 *
 *   // Direct API (mirrors loader sub-modules)
 *   const model   = await assetLoader.loadModel('detector.glb');
 *   const tex     = await assetLoader.loadTexture('particle.png');
 *   const shader  = await assetLoader.loadShader('collisionShader');
 */

// ─── Priority levels ──────────────────────────────────────────────────────────
export const Priority = Object.freeze({
  CRITICAL: 0,   // Blocks render — load first
  HIGH:     1,   // Load before interaction
  NORMAL:   2,   // Load during idle
  LAZY:     3,   // Load on demand
});

// ─── Asset type constants ─────────────────────────────────────────────────────
export const AssetType = Object.freeze({
  MODEL:   'model',
  TEXTURE: 'texture',
  SHADER:  'shader',
  ENVMAP:  'envmap',
  FONT:    'font',
  JSON:    'json',
});

// ─── Asset manifest ───────────────────────────────────────────────────────────
// All named assets the simulator may request. Loaders resolve these keys.
export const ASSET_MANIFEST = {
  // ── Detector models ──
  detector_atlas: {
    type: AssetType.MODEL,
    source: 'placeholder',
    priority: Priority.LAZY,
    bundle: 'scene',
    placeholder: 'atlas',
    tags: ['detector', '3d'],
  },
  detector_cms: {
    type: AssetType.MODEL,
    source: 'placeholder',
    priority: Priority.LAZY,
    bundle: 'scene',
    placeholder: 'cms',
    tags: ['detector', '3d'],
  },
  beam_pipe: {
    type: AssetType.MODEL,
    source: 'placeholder',
    priority: Priority.LAZY,
    bundle: 'scene',
    placeholder: 'beam_pipe',
    tags: ['detector', 'core'],
  },
  calorimeter_cell: {
    type: AssetType.MODEL,
    source: 'placeholder',
    priority: Priority.LAZY,
    bundle: 'scene',
    placeholder: 'calorimeter',
    tags: ['detector', 'calorimeter'],
  },
  muon_chamber: {
    type: AssetType.MODEL,
    source: 'placeholder',
    priority: Priority.LAZY,
    bundle: 'scene',
    placeholder: 'muon',
    tags: ['detector', 'muon'],
  },

  // ── Particle textures ──
  particle_glow: {
    type: AssetType.TEXTURE,
    source: 'procedural',
    generator: 'glow',
    priority: Priority.CRITICAL,
    bundle: 'core',
    options: { size: 128, color: { r: 0.45, g: 0.8, b: 1.0 } },
    tags: ['particle', 'sprite'],
  },
  particle_spark: {
    type: AssetType.TEXTURE,
    source: 'procedural',
    generator: 'glow',
    priority: Priority.HIGH,
    bundle: 'core',
    options: { size: 96, color: { r: 1.0, g: 0.74, b: 0.35 } },
    tags: ['particle', 'sprite'],
  },
  particle_trail: {
    type: AssetType.TEXTURE,
    source: 'procedural',
    generator: 'glow',
    priority: Priority.HIGH,
    bundle: 'core',
    options: { size: 64, color: { r: 0.58, g: 1.0, b: 0.76 } },
    tags: ['particle', 'trail'],
  },
  energy_ramp: {
    type: AssetType.TEXTURE,
    source: 'procedural',
    generator: 'energyRamp',
    priority: Priority.HIGH,
    bundle: 'core',
    options: { width: 256 },
    tags: ['heatmap', 'lut'],
  },
  detector_surface: {
    type: AssetType.TEXTURE,
    source: 'procedural',
    generator: 'checker',
    priority: Priority.NORMAL,
    bundle: 'detail',
    options: { size: 256, divisions: 24 },
    tags: ['material', 'pbr'],
  },
  noise_vol: {
    type: AssetType.TEXTURE,
    source: 'procedural',
    generator: 'noise',
    priority: Priority.LAZY,
    bundle: 'fx',
    options: { size: 128 },
    tags: ['noise', 'volume'],
  },

  // ── Shaders ──
  collisionShader: {
    type: AssetType.SHADER,
    source: 'builtin',
    priority: Priority.CRITICAL,
    bundle: 'core',
    tags: ['shader', 'collision'],
  },
  heatmapShader: {
    type: AssetType.SHADER,
    source: 'builtin',
    priority: Priority.HIGH,
    bundle: 'core',
    tags: ['shader', 'heatmap'],
  },
  trackShader: {
    type: AssetType.SHADER,
    source: 'builtin',
    priority: Priority.HIGH,
    bundle: 'core',
    tags: ['shader', 'track'],
  },
  glowShader: {
    type: AssetType.SHADER,
    source: 'builtin',
    priority: Priority.NORMAL,
    bundle: 'fx',
    tags: ['shader', 'glow'],
  },
  volumetricShader: {
    type: AssetType.SHADER,
    source: 'builtin',
    priority: Priority.LAZY,
    bundle: 'fx',
    tags: ['shader', 'volumetric'],
  },

  // ── Environment maps ──
  envmap_space: {
    type: AssetType.ENVMAP,
    source: 'procedural',
    generator: 'space',
    priority: Priority.LAZY,
    bundle: 'scene',
    tags: ['envmap', 'hdr'],
  },
  envmap_lab: {
    type: AssetType.ENVMAP,
    source: 'procedural',
    generator: 'lab',
    priority: Priority.LAZY,
    bundle: 'detail',
    tags: ['envmap', 'hdr'],
  },
};

// ─── Bundle definitions ───────────────────────────────────────────────────────
export const BUNDLES = {
  core:   { label: 'Core Assets',   priority: Priority.CRITICAL },
  scene:  { label: 'Scene Assets',  priority: Priority.LAZY     },
  cms:    { label: 'CMS Geometry',  priority: Priority.NORMAL   },
  detail: { label: 'Detail Assets', priority: Priority.NORMAL   },
  fx:     { label: 'VFX Assets',    priority: Priority.LAZY     },
};

// ─── LRU Cache ────────────────────────────────────────────────────────────────
class LRUCache {
  #map    = new Map();
  #maxSize;
  #ttl;   // ms, 0 = no eviction

  constructor(maxSize = 256, ttlMs = 0) {
    this.#maxSize = maxSize;
    this.#ttl     = ttlMs;
  }

  get(key) {
    if (!this.#map.has(key)) return undefined;
    const entry = this.#map.get(key);
    if (this.#ttl > 0 && Date.now() - entry.ts > this.#ttl) {
      this.#map.delete(key);
      return undefined;
    }
    // Move to end (most-recently-used)
    this.#map.delete(key);
    this.#map.set(key, entry);
    return entry.value;
  }

  set(key, value) {
    if (this.#map.has(key)) this.#map.delete(key);
    else if (this.#map.size >= this.#maxSize) {
      // Evict LRU (first entry)
      const firstKey = this.#map.keys().next().value;
      this.#map.delete(firstKey);
    }
    this.#map.set(key, { value, ts: Date.now() });
  }

  has(key) {
    return this.get(key) !== undefined;
  }

  delete(key) { this.#map.delete(key); }
  clear()     { this.#map.clear(); }
  get size()  { return this.#map.size; }

  keys() { return [...this.#map.keys()]; }
}

// ─── Progress tracker ─────────────────────────────────────────────────────────
class ProgressTracker {
  #items     = new Map(); // key → { total, loaded, status }
  #listeners = new Set();

  register(key, total = 100) {
    this.#items.set(key, { total, loaded: 0, status: 'pending' });
  }

  update(key, loaded, total) {
    const item = this.#items.get(key) ?? { total, loaded: 0, status: 'loading' };
    item.loaded = loaded;
    item.total  = total;
    item.status = 'loading';
    this.#items.set(key, item);
    this.#notify();
  }

  complete(key, success = true) {
    const item = this.#items.get(key);
    if (item) {
      item.status = success ? 'done' : 'error';
      item.loaded = item.total;
      this.#items.set(key, item);
    }
    this.#notify();
  }

  get aggregate() {
    let total = 0, loaded = 0, done = 0, errors = 0;
    for (const item of this.#items.values()) {
      total  += item.total;
      loaded += item.loaded;
      if (item.status === 'done')  done++;
      if (item.status === 'error') errors++;
    }
    const count    = this.#items.size;
    const percent  = total > 0 ? Math.round((loaded / total) * 100) : 0;
    const complete = count > 0 && done + errors === count;
    return { total, loaded, count, done, errors, percent, complete };
  }

  get items() {
    return Object.fromEntries(this.#items);
  }

  subscribe(fn) {
    this.#listeners.add(fn);
    return () => this.#listeners.delete(fn);
  }

  #notify() {
    const state = { aggregate: this.aggregate, items: this.items };
    for (const fn of this.#listeners) fn(state);
  }

  reset() { this.#items.clear(); this.#notify(); }
}

// ─── Retry helper ─────────────────────────────────────────────────────────────
async function withRetry(fn, maxAttempts = 3, baseDelayMs = 400) {
  let lastErr;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      if (attempt < maxAttempts - 1) {
        await new Promise(r => setTimeout(r, baseDelayMs * 2 ** attempt));
      }
    }
  }
  throw lastErr;
}

// ─── AssetLoader class ────────────────────────────────────────────────────────
class AssetLoader extends EventTarget {
  #cache    = new LRUCache(512, 0);
  #pending  = new Map();   // key → Promise (in-flight dedup)
  #progress = new ProgressTracker();
  #modelLoader   = null;
  #textureLoader = null;
  #shaderLoader  = null;

  constructor() {
    super();
    this.manifest = ASSET_MANIFEST;
    this.progress = this.#progress;
  }

  // ── Loader injection (called by sub-modules) ──────────────────────────────
  registerModelLoader(loader)   { this.#modelLoader   = loader; }
  registerTextureLoader(loader) { this.#textureLoader = loader; }
  registerShaderLoader(loader)  { this.#shaderLoader  = loader; }

  // ── Core load API ─────────────────────────────────────────────────────────

  /**
   * Load any named asset from the manifest.
   * Returns cached result immediately on subsequent calls.
   */
  async load(key) {
    if (this.#cache.has(key)) return this.#cache.get(key);
    if (this.#pending.has(key)) return this.#pending.get(key);

    const def = this.manifest[key];
    if (!def) throw new Error(`[AssetLoader] Unknown asset key: "${key}"`);

    const promise = this.#fetchAsset(key, def).then(asset => {
      this.#cache.set(key, asset);
      this.#pending.delete(key);
      return asset;
    });

    this.#pending.set(key, promise);
    return promise;
  }

  /**
   * Preload an entire bundle. Returns when all assets complete.
   * Respects per-asset priority ordering within the bundle.
   */
  async preloadBundle(bundleName) {
    const keys = Object.entries(this.manifest)
      .filter(([, def]) => def.bundle === bundleName)
      .sort(([, a], [, b]) => a.priority - b.priority)
      .map(([key]) => key);

    if (keys.length === 0) {
      console.warn(`[AssetLoader] Bundle "${bundleName}" has no assets.`);
      return {};
    }

    const results = await Promise.allSettled(keys.map(k => this.load(k)));
    return Object.fromEntries(
      keys.map((key, i) => [key, results[i].status === 'fulfilled' ? results[i].value : null])
    );
  }

  /**
   * Preload all bundles up to (and including) a given priority level.
   */
  async preloadUpTo(maxPriority = Priority.HIGH) {
    const keys = Object.entries(this.manifest)
      .filter(([, def]) => def.priority <= maxPriority)
      .sort(([, a], [, b]) => a.priority - b.priority)
      .map(([key]) => key);

    return Promise.allSettled(keys.map(k => this.load(k)));
  }

  // ── Convenience wrappers matching the loader API ───────────────────────────

  async loadModel(urlOrKey)   { return this.#loadByTypeOrUrl(urlOrKey, AssetType.MODEL);   }
  async loadTexture(urlOrKey) { return this.#loadByTypeOrUrl(urlOrKey, AssetType.TEXTURE); }
  async loadShader(urlOrKey)  { return this.#loadByTypeOrUrl(urlOrKey, AssetType.SHADER);  }
  async loadEnvmap(urlOrKey)  { return this.#loadByTypeOrUrl(urlOrKey, AssetType.ENVMAP);  }

  // ── Cache management ──────────────────────────────────────────────────────

  isCached(key)   { return this.#cache.has(key); }
  evict(key)      { this.#cache.delete(key); }
  clearCache()    { this.#cache.clear(); }
  get cacheSize() { return this.#cache.size; }
  get cacheKeys() { return this.#cache.keys(); }

  // ── Progress API ──────────────────────────────────────────────────────────

  onProgress(fn)  { return this.#progress.subscribe(fn); }
  get loadState() { return this.#progress.aggregate; }

  // ── Private ───────────────────────────────────────────────────────────────

  async #fetchAsset(key, def) {
    this.#progress.register(key, 100);

    const onProgress = (loaded, total) => this.#progress.update(key, loaded, total);

    try {
      let asset;
      await withRetry(async () => {
        switch (def.type) {
          case AssetType.MODEL:
            if (!this.#modelLoader) throw new Error('[AssetLoader] No ModelLoader registered');
            if (def.source === 'placeholder' || !def.url) {
              onProgress(100, 100);
              asset = this.#modelLoader.buildPlaceholder(def.placeholder ?? key);
            } else {
              asset = await this.#modelLoader.load(def.url, onProgress);
            }
            break;
          case AssetType.TEXTURE:
            if (!this.#textureLoader) throw new Error('[AssetLoader] No TextureLoader registered');
            if (def.source === 'procedural') {
              onProgress(100, 100);
              asset = this.#textureLoader.buildProcedural(def.generator ?? key, def.options ?? {});
            } else {
              asset = await this.#textureLoader.load(def.url, def.options ?? {}, onProgress);
            }
            break;
          case AssetType.SHADER:
            if (!this.#shaderLoader) throw new Error('[AssetLoader] No ShaderLoader registered');
            asset = await this.#shaderLoader.load(def.vertUrl, def.fragUrl, onProgress, key);
            break;
          case AssetType.ENVMAP:
            if (!this.#textureLoader) throw new Error('[AssetLoader] No TextureLoader registered');
            if (def.source === 'procedural') {
              onProgress(100, 100);
              asset = this.#textureLoader.buildEnvironmentMap(def.generator ?? 'space');
            } else {
              asset = await this.#textureLoader.loadHDR(def.url, onProgress);
            }
            break;
          default:
            throw new Error(`[AssetLoader] Unsupported asset type: ${def.type}`);
        }
      });

      this.#progress.complete(key, true);
      this.dispatchEvent(new CustomEvent('assetLoaded', { detail: { key, def } }));
      return asset;
    } catch (err) {
      this.#progress.complete(key, false);
      this.dispatchEvent(new CustomEvent('assetError', { detail: { key, def, err } }));
      throw err;
    }
  }

  async #loadByTypeOrUrl(urlOrKey, expectedType) {
    // Check if it's a manifest key
    if (this.manifest[urlOrKey]) {
      const def = this.manifest[urlOrKey];
      if (def.type !== expectedType) {
        console.warn(`[AssetLoader] Key "${urlOrKey}" is type ${def.type}, expected ${expectedType}`);
      }
      return this.load(urlOrKey);
    }

    // Treat as a raw URL — synthesise a transient key
    const key = `__raw__${urlOrKey}`;
    if (this.#cache.has(key)) return this.#cache.get(key);

    const syntheticDef = { type: expectedType, url: urlOrKey, priority: Priority.NORMAL };
    this.manifest[key] = syntheticDef;
    return this.load(key);
  }
}

// ── Singleton export ──────────────────────────────────────────────────────────
export const assetLoader = new AssetLoader();
export default assetLoader;
