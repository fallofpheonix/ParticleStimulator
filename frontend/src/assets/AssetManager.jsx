/**
 * AssetManager.jsx
 * ─────────────────────────────────────────────────────────────────────────────
 * React integration layer for the asset loading pipeline.
 *
 * Exports:
 *   <AssetProvider bundles={['core']} fallback={<Spinner />}>
 *     — Wraps the app, preloads named bundles, shows loading UI until complete.
 *
 *   useAsset(key)          — Lazy-load a single named asset, returns { asset, loading, error }
 *   useAssets(keys[])      — Load multiple assets, returns { assets, loading, progress, error }
 *   useAssetProgress()     — Subscribe to global loading progress
 *   useShaderMaterial(key) — Build and auto-tick a ShaderMaterial
 *   useTexture(key)        — Load a texture (wraps useAsset)
 *   useModel(key)          — Load a model scene (wraps useAsset)
 *
 *   <AssetLoadingScreen /> — Standalone loading overlay (used by AssetProvider)
 *   <AssetDebugPanel />    — Dev-mode cache inspector overlay
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { useFrame } from '@react-three/fiber';

import assetLoader, { Priority, BUNDLES }  from './AssetLoader';
import { modelLoader }   from './ModelLoader';
import { textureLoader } from './TextureLoader';
import { shaderLoader }  from './ShaderLoader';

// ── Register loaders with the central manager ─────────────────────────────────
assetLoader.registerModelLoader(modelLoader);
assetLoader.registerTextureLoader(textureLoader);
assetLoader.registerShaderLoader(shaderLoader);

// ─── Context ─────────────────────────────────────────────────────────────────
const AssetContext = createContext(null);

// ─── useAssetProgress ────────────────────────────────────────────────────────
/**
 * Subscribe to global asset loading progress.
 * Returns { percent, done, errors, count, complete }
 */
export function useAssetProgress() {
  const [state, setState] = useState(() => assetLoader.loadState);
  useEffect(() => {
    return assetLoader.onProgress(({ aggregate }) => setState(aggregate));
  }, []);
  return state;
}

// ─── useAsset ────────────────────────────────────────────────────────────────
/**
 * Lazy-load a single named asset from the manifest.
 * @param {string} key   Manifest key, e.g. 'particle_glow'
 * @param {boolean} skip  Set true to defer loading
 */
export function useAsset(key, skip = false) {
  const [asset,   setAsset]   = useState(() => assetLoader.isCached(key) ? assetLoader.load(key) : null);
  const [loading, setLoading] = useState(!assetLoader.isCached(key) && !skip);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    if (skip || assetLoader.isCached(key)) return;
    let cancelled = false;
    setLoading(true);
    assetLoader.load(key)
      .then(a => { if (!cancelled) { setAsset(a); setLoading(false); } })
      .catch(e => { if (!cancelled) { setError(e); setLoading(false); } });
    return () => { cancelled = true; };
  }, [key, skip]);

  return { asset, loading, error };
}

// ─── useAssets ───────────────────────────────────────────────────────────────
/**
 * Load multiple assets simultaneously.
 */
export function useAssets(keys) {
  const [assets,   setAssets]   = useState({});
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState(null);
  const progress = useAssetProgress();

  useEffect(() => {
    if (!keys?.length) { setLoading(false); return; }
    let cancelled = false;
    setLoading(true);

    Promise.allSettled(keys.map(k => assetLoader.load(k))).then(results => {
      if (cancelled) return;
      const map = {};
      let firstErr = null;
      results.forEach((r, i) => {
        if (r.status === 'fulfilled') map[keys[i]] = r.value;
        else firstErr = firstErr ?? r.reason;
      });
      setAssets(map);
      setError(firstErr);
      setLoading(false);
    });

    return () => { cancelled = true; };
  }, [keys?.join(',')]);

  return { assets, loading, error, progress };
}

// ─── useTexture / useModel ────────────────────────────────────────────────────
export function useTexture(key, skip = false) { return useAsset(key, skip); }
export function useModel(key, skip = false)   { return useAsset(key, skip); }

// ─── useShaderMaterial ───────────────────────────────────────────────────────
/**
 * Build a ShaderMaterial from the library and auto-tick its uTime uniform.
 */
export function useShaderMaterial(key, extraUniforms = {}) {
  const material = useMemo(() => {
    try {
      return shaderLoader.buildMaterial(key, extraUniforms);
    } catch {
      return null;
    }
  }, [key]);

  // Auto-tick uTime in the render loop
  useFrame(({ clock }) => {
    if (material?.uniforms?.uTime !== undefined) {
      material.uniforms.uTime.value = clock.getElapsedTime();
    }
  });

  return material;
}

// ─── Loading screen component ─────────────────────────────────────────────────

function ProgressBar({ percent, color = '#00ffcc' }) {
  return (
    <div style={{
      width: '100%',
      height: '3px',
      background: 'rgba(255,255,255,0.08)',
      borderRadius: '2px',
      overflow: 'hidden',
    }}>
      <div style={{
        width: `${percent}%`,
        height: '100%',
        background: `linear-gradient(90deg, ${color}88, ${color})`,
        borderRadius: '2px',
        transition: 'width 0.25s ease',
        boxShadow: `0 0 8px ${color}66`,
      }} />
    </div>
  );
}

function StatusDot({ status }) {
  const colors = { pending: '#444', loading: '#00aaff', done: '#00ffcc', error: '#ff4455' };
  const color  = colors[status] ?? '#444';
  return (
    <span style={{
      display: 'inline-block',
      width: '6px', height: '6px',
      borderRadius: '50%',
      background: color,
      boxShadow: status === 'loading' ? `0 0 5px ${color}` : 'none',
      flexShrink: 0,
    }} />
  );
}

/**
 * Full-screen loading overlay shown while bundles are initializing.
 */
export function AssetLoadingScreen({ progress, items }) {
  const { percent, count, done, errors } = progress;

  const itemEntries = Object.entries(items ?? {}).slice(0, 18);

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'radial-gradient(ellipse at 40% 30%, #040e1c, #020810)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      fontFamily: "'Share Tech Mono', 'Courier New', monospace",
    }}>
      {/* Particle grid bg */}
      <div style={{
        position: 'absolute', inset: 0, opacity: 0.12,
        backgroundImage: 'radial-gradient(circle, #00ffcc 1px, transparent 1px)',
        backgroundSize: '40px 40px',
      }} />

      <div style={{ width: '480px', maxWidth: '90vw', position: 'relative' }}>

        {/* Header */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{
            fontSize: '10px', letterSpacing: '0.3em', color: 'rgba(0,255,204,0.45)',
            marginBottom: '8px',
          }}>
            PARTICLE STIMULATOR
          </div>
          <div style={{
            fontFamily: "'Orbitron', 'Courier New', monospace",
            fontSize: 'clamp(18px, 4vw, 26px)',
            fontWeight: 700,
            color: '#00ffcc',
            letterSpacing: '0.06em',
            lineHeight: 1.2,
          }}>
            LOADING ASSETS
          </div>
          <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.2)', marginTop: '6px', letterSpacing: '0.1em' }}>
            INITIALISING VISUALISATION PIPELINE
          </div>
        </div>

        {/* Main progress */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
            marginBottom: '10px',
          }}>
            <span style={{ fontSize: '11px', color: 'rgba(0,255,204,0.6)', letterSpacing: '0.1em' }}>
              PIPELINE PROGRESS
            </span>
            <span style={{
              fontFamily: "'Orbitron', monospace",
              fontSize: '20px',
              color: '#00ffcc',
              fontWeight: 700,
            }}>
              {percent}%
            </span>
          </div>
          <ProgressBar percent={percent} color="#00ffcc" />
          <div style={{
            display: 'flex', justifyContent: 'space-between',
            marginTop: '8px',
            fontSize: '9px', color: 'rgba(255,255,255,0.25)', letterSpacing: '0.1em',
          }}>
            <span>{done} / {count} ASSETS</span>
            {errors > 0 && <span style={{ color: '#ff4455' }}>{errors} ERRORS</span>}
          </div>
        </div>

        {/* Per-asset list */}
        <div style={{
          background: 'rgba(0,0,0,0.3)',
          border: '1px solid rgba(0,255,204,0.1)',
          borderRadius: '8px',
          padding: '12px',
          maxHeight: '260px',
          overflowY: 'auto',
          scrollbarWidth: 'thin',
        }}>
          {itemEntries.length === 0 ? (
            <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.2)', textAlign: 'center', padding: '20px' }}>
              Registering assets…
            </div>
          ) : itemEntries.map(([key, item]) => (
            <div key={key} style={{
              display: 'flex', alignItems: 'center', gap: '10px',
              padding: '5px 4px',
              borderBottom: '1px solid rgba(255,255,255,0.04)',
            }}>
              <StatusDot status={item.status} />
              <span style={{
                flex: 1, fontSize: '10px', letterSpacing: '0.05em',
                color: item.status === 'done'
                  ? 'rgba(0,255,204,0.7)'
                  : item.status === 'error'
                  ? '#ff4455'
                  : 'rgba(255,255,255,0.35)',
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {key.replace('__raw__', '')}
              </span>
              {item.status === 'loading' && (
                <div style={{ width: '60px', flexShrink: 0 }}>
                  <ProgressBar
                    percent={item.total > 0 ? Math.round(item.loaded / item.total * 100) : 0}
                    color="#00aaff"
                  />
                </div>
              )}
              {item.status === 'done' && (
                <span style={{ fontSize: '9px', color: 'rgba(0,255,204,0.4)', letterSpacing: '0.06em' }}>OK</span>
              )}
              {item.status === 'error' && (
                <span style={{ fontSize: '9px', color: '#ff4455', letterSpacing: '0.06em' }}>ERR</span>
              )}
            </div>
          ))}
        </div>

        {/* Hint */}
        <div style={{
          marginTop: '20px', textAlign: 'center',
          fontSize: '9px', color: 'rgba(255,255,255,0.12)', letterSpacing: '0.12em',
        }}>
          {errors > 0
            ? 'SOME ASSETS FAILED — PROCEEDING WITH FALLBACKS'
            : percent < 100
            ? 'PLEASE WAIT…'
            : 'COMPLETE — LAUNCHING VISUALISATION'}
        </div>
      </div>
    </div>
  );
}

// ─── AssetDebugPanel ──────────────────────────────────────────────────────────
/**
 * Dev-mode panel showing cache contents and loader state.
 * Render anywhere in your app during development.
 */
export function AssetDebugPanel({ position = 'bottom-right' }) {
  const progress   = useAssetProgress();
  const [open, setOpen] = useState(false);

  const posStyles = {
    'bottom-right': { bottom: '16px', right: '16px' },
    'bottom-left':  { bottom: '16px', left:  '16px' },
    'top-right':    { top:    '16px', right: '16px' },
  }[position] ?? { bottom: '16px', right: '16px' };

  return (
    <div style={{
      position: 'fixed', zIndex: 10000,
      fontFamily: "'Share Tech Mono', monospace",
      ...posStyles,
    }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          padding: '6px 12px', fontSize: '10px', letterSpacing: '0.1em',
          background: 'rgba(0,0,0,0.8)', border: '1px solid rgba(0,255,204,0.3)',
          color: '#00ffcc', cursor: 'pointer', borderRadius: '4px',
          marginBottom: open ? '8px' : 0, display: 'block',
        }}
      >
        {open ? '▲' : '▼'} ASSET DEBUG ({progress.done}/{progress.count})
      </button>

      {open && (
        <div style={{
          background: 'rgba(2,8,18,0.97)', border: '1px solid rgba(0,255,204,0.15)',
          borderRadius: '6px', padding: '12px', width: '320px',
          maxHeight: '400px', overflowY: 'auto',
          fontSize: '10px', lineHeight: 1.6,
        }}>
          <div style={{ color: 'rgba(0,255,204,0.5)', marginBottom: '8px', letterSpacing: '0.12em' }}>
            ASSET CACHE — {assetLoader.cacheSize} ENTRIES
          </div>
          <div style={{ marginBottom: '10px' }}>
            <ProgressBar percent={progress.percent} color="#00ffcc" />
            <div style={{ color: 'rgba(255,255,255,0.3)', marginTop: '4px' }}>
              {progress.percent}% · {progress.done} done · {progress.errors} errors
            </div>
          </div>
          {assetLoader.cacheKeys.map(key => (
            <div key={key} style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              padding: '3px 0', borderBottom: '1px solid rgba(255,255,255,0.04)',
              color: 'rgba(0,255,204,0.6)',
            }}>
              <span style={{ fontSize: '8px', color: 'rgba(0,255,204,0.3)' }}>■</span>
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                {key.replace('__raw__', '~')}
              </span>
              <button
                onClick={() => assetLoader.evict(key)}
                style={{
                  background: 'none', border: 'none', color: '#ff4455',
                  cursor: 'pointer', fontSize: '9px', padding: '0 4px', flexShrink: 0,
                }}
              >
                ✕
              </button>
            </div>
          ))}
          <div style={{ marginTop: '10px', display: 'flex', gap: '8px' }}>
            <button
              onClick={() => assetLoader.clearCache()}
              style={{
                flex: 1, padding: '5px', fontSize: '9px', letterSpacing: '0.08em',
                background: 'rgba(255,68,85,0.1)', border: '1px solid rgba(255,68,85,0.3)',
                color: '#ff4455', cursor: 'pointer', borderRadius: '3px',
              }}
            >
              CLEAR CACHE
            </button>
            <button
              onClick={() => assetLoader.preloadUpTo(Priority.HIGH)}
              style={{
                flex: 1, padding: '5px', fontSize: '9px', letterSpacing: '0.08em',
                background: 'rgba(0,255,204,0.08)', border: '1px solid rgba(0,255,204,0.2)',
                color: '#00ffcc', cursor: 'pointer', borderRadius: '3px',
              }}
            >
              PRELOAD HIGH
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── AssetProvider ────────────────────────────────────────────────────────────
/**
 * Top-level provider. Preloads named bundles, shows loading screen until complete.
 *
 * @param {string[]} bundles   Bundle keys to preload (e.g. ['core'])
 * @param {number}   priority  Max priority level to preload (default: HIGH)
 * @param {ReactNode} fallback  Override loading screen
 * @param {boolean}   debug    Show debug panel in dev mode
 */
export function AssetProvider({
  children,
  bundles     = ['core'],
  priority    = Priority.HIGH,
  fallback    = null,
  debug       = Boolean(import.meta.env?.DEV),
}) {
  const progress = useAssetProgress();
  const [ready,  setReady]  = useState(false);
  const [items,  setItems]  = useState({});
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;

    // Subscribe to per-item updates
    const unsub = assetLoader.onProgress(({ items: i }) => {
      if (mountedRef.current) setItems({ ...i });
    });

    // Fire preloads
    const tasks = bundles.map(b => assetLoader.preloadBundle(b));
    if (!bundles.length) {
      tasks.push(assetLoader.preloadUpTo(priority));
    }

    Promise.allSettled(tasks).then(() => {
      if (mountedRef.current) setReady(true);
    });

    return () => {
      mountedRef.current = false;
      unsub();
    };
  }, [bundles.join(','), priority]);

  const contextValue = useMemo(() => ({
    ready,
    assetLoader,
    modelLoader,
    textureLoader,
    shaderLoader,
  }), [ready]);

  return (
    <AssetContext.Provider value={contextValue}>
      {!ready
        ? (fallback ?? <AssetLoadingScreen progress={progress} items={items} />)
        : children
      }
      {debug && <AssetDebugPanel />}
    </AssetContext.Provider>
  );
}

// ─── useAssetManager ─────────────────────────────────────────────────────────
export function useAssetManager() {
  const ctx = useContext(AssetContext);
  if (!ctx) throw new Error('useAssetManager must be used inside <AssetProvider>');
  return ctx;
}

// ─── Convenience re-exports ───────────────────────────────────────────────────
export { assetLoader, modelLoader, textureLoader, shaderLoader };
export default AssetProvider;
