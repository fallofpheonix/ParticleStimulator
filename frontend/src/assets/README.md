# Asset Loading System

Complete asset pipeline for the Particle Stimulator frontend. Handles 3D models, particle textures, GLSL shaders, and HDR environment maps with caching, progress tracking, and lazy loading.

## File Structure

```
assets/
├── AssetLoader.js     Central registry, LRU cache, progress tracker, retry logic
├── ModelLoader.js     GLTF/GLB loader with Draco, instancing, material upgrades
├── TextureLoader.js   PNG/JPG/HDR loader + procedural texture generators
├── ShaderLoader.js    GLSL fetcher, built-in shader library, #include preprocessor
├── AssetManager.jsx   React provider, hooks, loading screen, debug panel
└── index.js           Barrel exports
```

## Quick Start

```jsx
// main.jsx
import { AssetProvider } from './assets';
import App from './App';

<AssetProvider bundles={['core']}>
  <App />
</AssetProvider>
```

```jsx
// Inside a component
import { useTexture, useShaderMaterial, useModel } from './assets';

function ParticleSystem() {
  const { asset: glowTex, loading } = useTexture('particle_glow');
  const heatMat = useShaderMaterial('heatmapShader');

  if (loading) return null;
  // ...
}
```

## Imperative API

```js
import { assetLoader } from './assets';

// Named asset (from manifest)
const tex   = await assetLoader.loadTexture('particle_glow');
const model = await assetLoader.loadModel('detector_atlas');
const prog  = await assetLoader.loadShader('collisionShader');

// Raw URL (auto-keyed)
const raw = await assetLoader.loadTexture('/textures/custom.png');

// Preload a bundle
await assetLoader.preloadBundle('core');

// Cache queries
assetLoader.isCached('particle_glow'); // true
assetLoader.evict('particle_glow');
assetLoader.clearCache();
```

## Built-in Shaders (no network required)

| Key                | Description                                   |
|--------------------|-----------------------------------------------|
| `collisionShader`  | Vertex-coloured burst animation for collision events |
| `heatmapShader`    | 1D LUT energy heatmap with fresnel glow       |
| `trackShader`      | Tapered particle track with momentum colouring |
| `glowShader`       | Additive billboard glow sprite                |
| `volumetricShader` | Raymarched volumetric beam fog                |

```js
import { shaderLoader } from './assets';

// Get a material directly
const mat = shaderLoader.buildMaterial('heatmapShader', {
  uEnergyRamp: { value: myLUT },
  uEnergy:     { value: 0.75 },
});

// Auto-tick time in render loop
shaderLoader.tick([mat], clock.elapsedTime);
```

## Procedural Textures (no network required)

```js
import { textureLoader } from './assets';

const glow    = textureLoader.buildGlowSprite(128);       // Radial glow sprite
const ramp    = textureLoader.buildEnergyRamp(256);       // Blue→cyan→green→yellow→red LUT
const noise   = textureLoader.buildNoiseTexture(256);     // White noise
const checker = textureLoader.buildCheckerTexture(256, 16); // Debug grid
```

## Asset Manifest

All assets are declared in `AssetLoader.js → ASSET_MANIFEST`. To add a new asset:

```js
my_texture: {
  type: AssetType.TEXTURE,
  url: '/assets/textures/my_texture.png',
  priority: Priority.NORMAL,
  bundle: 'core',
  options: { sRGB: true, mipmap: true },
  tags: ['particle'],
},
```

## Priority Levels

| Level      | Value | Use                           |
|------------|-------|-------------------------------|
| `CRITICAL` | 0     | Blocks first render           |
| `HIGH`     | 1     | Load before interaction       |
| `NORMAL`   | 2     | Load during idle              |
| `LAZY`     | 3     | Load on first access          |

## Hooks Reference

```js
useAssetProgress()         // { percent, done, errors, count, complete }
useAsset(key, skip?)       // { asset, loading, error }
useAssets(keys[])          // { assets, loading, error, progress }
useTexture(key, skip?)     // { asset, loading, error }
useModel(key, skip?)       // { asset, loading, error }
useShaderMaterial(key, extraUniforms?)  // THREE.ShaderMaterial (auto-ticks uTime)
useAssetManager()          // { ready, assetLoader, modelLoader, textureLoader, shaderLoader }
```

## LRU Cache

- 512 entry cap (configurable in `AssetLoader.js`)
- In-flight deduplication (concurrent calls to same key share one request)
- Retry: 3 attempts with exponential back-off (400ms, 800ms, 1600ms)

## Dependencies

```json
{
  "three": ">=0.167.0",
  "@react-three/fiber": ">=8.0.0",
  "@react-three/drei": ">=9.0.0",
  "react": ">=18.0.0"
}
```
