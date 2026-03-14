/**
 * assets/index.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Barrel export for the Particle Stimulator asset pipeline.
 *
 * Quick-start:
 *
 *   // 1. Wrap your app
 *   import { AssetProvider } from './assets';
 *   <AssetProvider bundles={['core']}><App /></AssetProvider>
 *
 *   // 2. Load assets in components
 *   import { useAsset, useShaderMaterial, useTexture } from './assets';
 *   const { asset: glowTex } = useTexture('particle_glow');
 *   const heatMat = useShaderMaterial('heatmapShader');
 *
 *   // 3. Imperative API (outside React)
 *   import { assetLoader } from './assets';
 *   const model = await assetLoader.loadModel('detector_atlas');
 *   const tex   = await assetLoader.loadTexture('particle_glow');
 *   const prog  = await assetLoader.loadShader('collisionShader');
 */

// ── Core loader singletons ────────────────────────────────────────────────────
export { assetLoader } from './AssetLoader';
export { modelLoader } from './ModelLoader';
export { textureLoader } from './TextureLoader';
export { shaderLoader } from './ShaderLoader';

// ── Constants & manifest ──────────────────────────────────────────────────────
export { Priority, AssetType, ASSET_MANIFEST, BUNDLES } from './AssetLoader';
export { WrapMode, setMaxAnisotropy }                   from './TextureLoader';
export { SHADER_LIBRARY }                               from './ShaderLoader';

// ── React layer ───────────────────────────────────────────────────────────────
export {
  AssetProvider,
  AssetLoadingScreen,
  AssetDebugPanel,
  useAssetManager,
  useAssetProgress,
  useAsset,
  useAssets,
  useTexture,
  useModel,
  useShaderMaterial,
} from './AssetManager';
