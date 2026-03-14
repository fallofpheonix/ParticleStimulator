/**
 * ShaderLoader.js
 * ─────────────────────────────────────────────────────────────────────────────
 * GLSL shader management for the Particle Stimulator visualisation system.
 *
 * Features:
 *   • Fetch .vert / .frag source from URL pairs
 *   • Built-in shader library (no network required for core shaders)
 *   • Simple #include preprocessor for shader chunk composition
 *   • Uniform registry with typed defaults
 *   • ShaderMaterial / RawShaderMaterial factory helpers
 *   • Hot-reload support (invalidates cache, recompiles)
 *
 * Usage:
 *   import { shaderLoader } from './ShaderLoader';
 *   import assetLoader from './AssetLoader';
 *
 *   assetLoader.registerShaderLoader(shaderLoader);
 *
 *   // By named key (uses built-in library)
 *   const program = await shaderLoader.load(null, null, null, 'collisionShader');
 *
 *   // By URL pair
 *   const program = await shaderLoader.load('/shaders/my.vert', '/shaders/my.frag');
 *
 *   // Build a Three.js ShaderMaterial directly
 *   const mat = shaderLoader.buildMaterial('heatmapShader', {
 *     uTime:       { value: 0 },
 *     uEnergyMap:  { value: null },
 *   });
 */

import * as THREE from 'three';

// ─── GLSL chunk library ───────────────────────────────────────────────────────
// Common GLSL snippets included via #include <chunkName>
const GLSL_CHUNKS = {
  'common_uniforms': /* glsl */`
    uniform float uTime;
    uniform float uOpacity;
    uniform vec3  uCameraPosition;
  `,
  'math_utils': /* glsl */`
    #define PI     3.141592653589793
    #define TWO_PI 6.283185307179586
    float remap(float v, float lo, float hi, float tlo, float thi) {
      return tlo + (v - lo) / (hi - lo) * (thi - tlo);
    }
    float smoothstep01(float v) { return v * v * (3.0 - 2.0 * v); }
  `,
  'noise_simplex': /* glsl */`
    // Compact 3D simplex noise (Ashima Arts)
    vec3 mod289(vec3 x) { return x - floor(x*(1./289.))*289.; }
    vec4 mod289(vec4 x) { return x - floor(x*(1./289.))*289.; }
    vec4 permute(vec4 x){ return mod289(((x*34.)+1.)*x); }
    vec4 taylorInvSqrt(vec4 r){ return 1.79284291400159 - 0.85373472095314*r; }
    float snoise(vec3 v){
      const vec2 C=vec2(1./6.,1./3.);
      const vec4 D=vec4(0.,0.5,1.,2.);
      vec3 i=floor(v+dot(v,C.yyy)),x0=v-i+dot(i,C.xxx);
      vec3 g=step(x0.yzx,x0.xyz),l=1.-g,i1=min(g.xyz,l.zxy),i2=max(g.xyz,l.zxy);
      vec3 x1=x0-i1+C.xxx,x2=x0-i2+C.yyy,x3=x0-D.yyy;
      i=mod289(i);
      vec4 p=permute(permute(permute(i.z+vec4(0.,i1.z,i2.z,1.))+i.y+vec4(0.,i1.y,i2.y,1.))+i.x+vec4(0.,i1.x,i2.x,1.));
      float n_=.142857142857;vec3 ns=n_*D.wyz-D.xzx;
      vec4 j=p-49.*floor(p*ns.z*ns.z),x_=floor(j*ns.z),y_=floor(j-7.*x_);
      vec4 x=x_*ns.x+ns.yyyy,y=y_*ns.x+ns.yyyy,h=1.-abs(x)-abs(y);
      vec4 b0=vec4(x.xy,y.xy),b1=vec4(x.zw,y.zw);
      vec4 s0=floor(b0)*2.+1.,s1=floor(b1)*2.+1.,sh=-step(h,vec4(0.));
      vec4 a0=b0.xzyw+s0.xzyw*sh.xxyy,a1=b1.xzyw+s1.xzyw*sh.zzww;
      vec3 p0=vec3(a0.xy,h.x),p1=vec3(a0.zw,h.y),p2=vec3(a1.xy,h.z),p3=vec3(a1.zw,h.w);
      vec4 norm=taylorInvSqrt(vec4(dot(p0,p0),dot(p1,p1),dot(p2,p2),dot(p3,p3)));
      p0*=norm.x;p1*=norm.y;p2*=norm.z;p3*=norm.w;
      vec4 m=max(.6-vec4(dot(x0,x0),dot(x1,x1),dot(x2,x2),dot(x3,x3)),0.);
      m=m*m;return 42.*dot(m*m,vec4(dot(p0,x0),dot(p1,x1),dot(p2,x2),dot(p3,x3)));
    }
  `,
};

// ─── Built-in shader library ──────────────────────────────────────────────────
// All shaders are embedded — zero network requests for core visuals.
export const SHADER_LIBRARY = {

  // ── Collision flash / vertex-coloured burst ─────────────────────────────
  collisionShader: {
    vertexShader: /* glsl */`
      #include <common_uniforms>
      #include <math_utils>
      attribute float aScale;
      attribute float aPhase;
      varying   float vLife;
      varying   vec3  vColor;

      void main() {
        float life = mod(uTime * 0.8 + aPhase, 1.0);
        vLife  = life;
        vColor = mix(vec3(1.0, 0.6, 0.0), vec3(0.0, 0.9, 1.0), life);

        float expand = smoothstep01(life);
        vec3 pos = position + normal * expand * aScale * 2.0;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        gl_PointSize = (1.0 - life) * aScale * 80.0 / -mvPosition.z;
      }
    `,
    fragmentShader: /* glsl */`
      varying float vLife;
      varying vec3  vColor;
      uniform float uOpacity;

      void main() {
        float d = length(gl_PointCoord - 0.5) * 2.0;
        float alpha = (1.0 - d) * (1.0 - vLife) * uOpacity;
        if (alpha < 0.01) discard;
        gl_FragColor = vec4(vColor, alpha);
      }
    `,
    uniforms: {
      uTime:    { value: 0 },
      uOpacity: { value: 1 },
    },
    transparent: true,
    depthWrite: false,
  },

  // ── Energy heatmap — samples 1D LUT by normalised energy ───────────────
  heatmapShader: {
    vertexShader: /* glsl */`
      varying vec2 vUv;
      varying vec3 vNormal;
      void main() {
        vUv     = uv;
        vNormal = normalMatrix * normal;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: /* glsl */`
      uniform sampler2D uEnergyRamp;
      uniform float     uEnergy;
      uniform float     uOpacity;
      uniform float     uTime;
      varying vec2      vUv;
      varying vec3      vNormal;

      void main() {
        float e     = clamp(uEnergy, 0.0, 1.0);
        vec3  color = texture2D(uEnergyRamp, vec2(e, 0.5)).rgb;

        // Edge fresnel glow
        float fresnel = 1.0 - abs(dot(normalize(vNormal), vec3(0.0, 0.0, 1.0)));
        color = mix(color, vec3(1.0), fresnel * 0.3);

        // Pulse on high energy deposits
        float pulse = 1.0 + sin(uTime * 6.0) * 0.15 * step(0.7, e);
        gl_FragColor = vec4(color * pulse, uOpacity);
      }
    `,
    uniforms: {
      uEnergyRamp: { value: null },
      uEnergy:     { value: 0 },
      uOpacity:    { value: 0.9 },
      uTime:       { value: 0 },
    },
    transparent: true,
    depthWrite: false,
  },

  // ── Particle track — tapered line with velocity-hue colouring ──────────
  trackShader: {
    vertexShader: /* glsl */`
      attribute float aProgress;   // 0=start 1=tip
      attribute float aMomentum;   // GeV
      varying   float vProgress;
      varying   float vMomentum;
      void main() {
        vProgress   = aProgress;
        vMomentum   = aMomentum;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = mix(4.0, 1.0, aProgress);
      }
    `,
    fragmentShader: /* glsl */`
      #include <math_utils>
      varying float vProgress;
      varying float vMomentum;
      uniform float uOpacity;

      vec3 momentumColor(float p) {
        // High momentum → cyan; low → warm orange
        return mix(vec3(1.0, 0.5, 0.1), vec3(0.0, 1.0, 0.9), clamp(p / 100.0, 0.0, 1.0));
      }

      void main() {
        float alpha = (1.0 - vProgress) * uOpacity;
        if (alpha < 0.01) discard;
        gl_FragColor = vec4(momentumColor(vMomentum), alpha);
      }
    `,
    uniforms: {
      uOpacity: { value: 0.85 },
    },
    transparent: true,
    depthWrite: false,
  },

  // ── Additive glow — soft billboarded radial bloom ──────────────────────
  glowShader: {
    vertexShader: /* glsl */`
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: /* glsl */`
      #include <math_utils>
      uniform sampler2D uGlowTex;
      uniform vec3      uColor;
      uniform float     uIntensity;
      uniform float     uOpacity;
      uniform float     uTime;
      varying vec2      vUv;

      void main() {
        float glow   = texture2D(uGlowTex, vUv).r;
        float pulse  = 1.0 + sin(uTime * 3.0) * 0.12;
        float alpha  = glow * uOpacity * pulse;
        if (alpha < 0.005) discard;
        gl_FragColor = vec4(uColor * uIntensity * pulse, alpha);
      }
    `,
    uniforms: {
      uGlowTex:   { value: null },
      uColor:     { value: new THREE.Color(0x00ffcc) },
      uIntensity: { value: 1.5 },
      uOpacity:   { value: 0.8 },
      uTime:      { value: 0 },
    },
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  },

  // ── Volumetric beam — raymarched cylinder fog ──────────────────────────
  volumetricShader: {
    vertexShader: /* glsl */`
      varying vec3 vWorldPos;
      varying vec3 vViewDir;
      void main() {
        vec4 worldPos = modelMatrix * vec4(position, 1.0);
        vWorldPos     = worldPos.xyz;
        vViewDir      = cameraPosition - worldPos.xyz;
        gl_Position   = projectionMatrix * viewMatrix * worldPos;
      }
    `,
    fragmentShader: /* glsl */`
      #include <noise_simplex>
      #include <math_utils>
      uniform float uTime;
      uniform float uOpacity;
      uniform vec3  uBeamColor;
      uniform float uRadius;
      varying vec3  vWorldPos;
      varying vec3  vViewDir;

      void main() {
        float dist  = length(vWorldPos.xy);
        float edge  = 1.0 - smoothstep(uRadius * 0.7, uRadius, dist);
        float noise = snoise(vWorldPos * 2.0 + vec3(0.0, 0.0, uTime * 0.5)) * 0.5 + 0.5;
        float alpha = edge * noise * uOpacity;
        if (alpha < 0.01) discard;
        gl_FragColor = vec4(uBeamColor, alpha);
      }
    `,
    uniforms: {
      uTime:      { value: 0 },
      uOpacity:   { value: 0.35 },
      uBeamColor: { value: new THREE.Color(0x0044ff) },
      uRadius:    { value: 0.3 },
    },
    transparent: true,
    depthWrite: false,
    side: THREE.BackSide,
  },
};

// ─── Preprocessor — resolve #include <chunk> directives ──────────────────────
function preprocess(source, chunks = GLSL_CHUNKS) {
  return source.replace(/#include\s+<(\w+)>/g, (_, name) => {
    if (chunks[name]) return chunks[name];
    console.warn(`[ShaderLoader] Unknown GLSL chunk: "${name}"`);
    return `/* missing chunk: ${name} */`;
  });
}

// ─── ShaderLoader class ───────────────────────────────────────────────────────
class ShaderLoader {
  #urlCache = new Map(); // url → source string

  /**
   * Load a shader program.
   * • If vertUrl and fragUrl are provided, fetches GLSL source from those URLs.
   * • If key is provided (or vertUrl is a key in SHADER_LIBRARY), returns built-in.
   * • Returns { vertexShader, fragmentShader, uniforms, ...threeProps }
   */
  async load(vertUrl, fragUrl, onProgress = null, key = null) {
    // Built-in library lookup
    const libKey = key ?? vertUrl;
    if (SHADER_LIBRARY[libKey]) {
      onProgress?.(100, 100);
      return this.#resolveBuiltin(libKey);
    }

    if (!vertUrl || !fragUrl) {
      throw new Error(`[ShaderLoader] Must provide vertUrl+fragUrl or a named shader key.`);
    }

    const [vert, frag] = await Promise.all([
      this.#fetchGLSL(vertUrl),
      this.#fetchGLSL(fragUrl),
    ]);
    onProgress?.(100, 100);

    return {
      vertexShader:   preprocess(vert),
      fragmentShader: preprocess(frag),
      uniforms:       {},
    };
  }

  /**
   * Get a built-in shader program by key without async overhead.
   */
  get(key) {
    if (!SHADER_LIBRARY[key]) throw new Error(`[ShaderLoader] Unknown shader: "${key}"`);
    return this.#resolveBuiltin(key);
  }

  /**
   * Construct a THREE.ShaderMaterial from a library key + extra uniforms.
   */
  buildMaterial(key, extraUniforms = {}, materialProps = {}) {
    const program = this.get(key);
    return new THREE.ShaderMaterial({
      vertexShader:   program.vertexShader,
      fragmentShader: program.fragmentShader,
      uniforms: THREE.UniformsUtils.merge([
        program.uniforms,
        extraUniforms,
      ]),
      transparent: program.transparent ?? false,
      depthWrite:  program.depthWrite  ?? true,
      blending:    program.blending    ?? THREE.NormalBlending,
      side:        program.side        ?? THREE.FrontSide,
      ...materialProps,
    });
  }

  /**
   * Update time uniform across multiple materials efficiently.
   * Call this in your animation loop.
   */
  tick(materials, time) {
    for (const mat of materials) {
      if (mat?.uniforms?.uTime !== undefined) {
        mat.uniforms.uTime.value = time;
      }
    }
  }

  /**
   * Hot-reload: clear cached URL sources so next load re-fetches.
   */
  invalidate(...urls) {
    for (const url of urls) this.#urlCache.delete(url);
  }

  // ── Private ───────────────────────────────────────────────────────────────

  #resolveBuiltin(key) {
    const def = SHADER_LIBRARY[key];
    return {
      ...def,
      vertexShader:   preprocess(def.vertexShader),
      fragmentShader: preprocess(def.fragmentShader),
      uniforms:       THREE.UniformsUtils.clone(def.uniforms ?? {}),
    };
  }

  async #fetchGLSL(url) {
    if (this.#urlCache.has(url)) return this.#urlCache.get(url);
    const res = await fetch(url);
    if (!res.ok) throw new Error(`[ShaderLoader] Failed to fetch: ${url} (${res.status})`);
    const src = await res.text();
    this.#urlCache.set(url, src);
    return src;
  }
}

// ── Singleton export ──────────────────────────────────────────────────────────
export const shaderLoader = new ShaderLoader();
export default shaderLoader;
