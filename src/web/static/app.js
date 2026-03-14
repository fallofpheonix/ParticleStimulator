const state = {
  defaults: null,
  payload: null,
  beamAnimationStart: 0,
  pending: false,
};

const elements = {
  form: document.getElementById("controlForm"),
  runButton: document.getElementById("runButton"),
  resetButton: document.getElementById("resetButton"),
  healthStatus: document.getElementById("healthStatus"),
  simulationStatus: document.getElementById("simulationStatus"),
  metricGrid: document.getElementById("metricGrid"),
  speciesList: document.getElementById("speciesList"),
  collisionList: document.getElementById("collisionList"),
  timelineList: document.getElementById("timelineList"),
  calorimeterBars: document.getElementById("calorimeterBars"),
  beamlineCanvas: document.getElementById("beamlineCanvas"),
  histogramCanvas: document.getElementById("histogramCanvas"),
};

function setStatus(node, text, healthy = true) {
  node.textContent = text;
  node.style.color = healthy ? "#b7ffd3" : "#ffd2d2";
  node.style.borderColor = healthy ? "rgba(120,255,170,0.3)" : "rgba(255,120,120,0.3)";
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.error || `request failed: ${response.status}`);
  }
  return response.json();
}

function syncOutputs() {
  const fields = elements.form.querySelectorAll("input[type='range']");
  for (const field of fields) {
    const output = elements.form.querySelector(`output[data-for="${field.name}"]`);
    if (output) {
      output.value = field.value;
      output.textContent = field.value;
    }
  }
}

function applyDefaults(payload) {
  state.defaults = payload;
  for (const [key, value] of Object.entries(payload)) {
    const field = elements.form.elements.namedItem(key);
    if (field) {
      field.value = value;
    }
  }
  syncOutputs();
}

function collectFormPayload() {
  const formData = new FormData(elements.form);
  return Object.fromEntries(formData.entries());
}

function renderMetrics(summary) {
  const metrics = [
    ["Collisions", summary.metrics.collision_count],
    ["Tracker Hits", summary.metrics.tracker_hit_count],
    ["Calorimeter Hits", summary.metrics.calorimeter_hit_count],
    ["Active Particles", summary.active_particles],
    ["Mean Mass (GeV)", summary.mean_invariant_mass_gev],
    ["Max Mass (GeV)", summary.max_invariant_mass_gev],
  ];
  elements.metricGrid.innerHTML = metrics.map(([label, value]) => `
    <article class="metric-card">
      <strong>${Number(value).toFixed(Number(value) >= 100 ? 0 : 3).replace(/\.000$/, "")}</strong>
      <span>${label}</span>
    </article>
  `).join("");
}

function renderSpecies(summary) {
  const entries = Object.entries(summary.species_counts).sort((left, right) => right[1] - left[1]);
  elements.speciesList.innerHTML = entries.map(([label, value]) => `
    <div class="kv-row">
      <span>${label}</span>
      <strong>${value}</strong>
    </div>
  `).join("") || '<div class="kv-row"><span>No particles</span><strong>0</strong></div>';
}

function renderCollisions(collisions) {
  elements.collisionList.innerHTML = collisions.map((event) => `
    <div class="log-row">
      <strong>Event ${event.event_id}</strong>
      <small>t=${event.time_s}s | mass=${event.invariant_mass_gev} GeV | products=${event.product_species.join(", ")}</small>
    </div>
  `).join("") || '<div class="log-row"><strong>No collisions</strong><small>Raise beam density or reduce spacing.</small></div>';
}

function renderTimeline(entries) {
  elements.timelineList.innerHTML = entries.slice(0, 28).map((entry) => `
    <div class="log-row">
      <strong>${entry.type}</strong>
      <small>${JSON.stringify(entry)}</small>
    </div>
  `).join("") || '<div class="log-row"><strong>No timeline entries</strong></div>';
}

function renderCalorimeter(phiTotals) {
  const maxEnergy = Math.max(1, ...phiTotals.map((row) => row.energy_gev));
  elements.calorimeterBars.innerHTML = phiTotals.map((row) => `
    <div class="bar-row">
      <span>phi ${row.phi_bin}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${(row.energy_gev / maxEnergy) * 100}%"></div></div>
      <strong>${row.energy_gev.toFixed(4)}</strong>
    </div>
  `).join("") || '<div class="log-row"><strong>No calorimeter deposits</strong></div>';
}

function resizeCanvas(canvas) {
  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(rect.width * ratio));
  canvas.height = Math.max(1, Math.floor(rect.height * ratio));
  const context = canvas.getContext("2d");
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  return { context, width: rect.width, height: rect.height };
}

function drawHistogram() {
  const { context, width, height } = resizeCanvas(elements.histogramCanvas);
  context.clearRect(0, 0, width, height);
  context.fillStyle = "rgba(255,255,255,0.05)";
  context.fillRect(0, 0, width, height);

  if (!state.payload) {
    context.fillStyle = "#8aa3c2";
    context.font = '14px "SF Mono", monospace';
    context.fillText("Run a simulation to populate the histogram.", 18, 28);
    return;
  }

  const bins = state.payload.summary.mass_histogram;
  const maxCount = Math.max(1, ...bins.map((bin) => bin.count));
  const chartLeft = 42;
  const chartBottom = height - 28;
  const chartHeight = height - 48;
  const chartWidth = width - 58;
  const barWidth = chartWidth / bins.length;

  context.strokeStyle = "rgba(255,255,255,0.18)";
  context.beginPath();
  context.moveTo(chartLeft, 12);
  context.lineTo(chartLeft, chartBottom);
  context.lineTo(chartLeft + chartWidth, chartBottom);
  context.stroke();

  bins.forEach((bin, index) => {
    const valueHeight = (bin.count / maxCount) * (chartHeight - 20);
    const x = chartLeft + (index * barWidth) + 4;
    const y = chartBottom - valueHeight;
    const gradient = context.createLinearGradient(0, y, 0, chartBottom);
    gradient.addColorStop(0, "#ff8a5b");
    gradient.addColorStop(1, "#6dd5ff");
    context.fillStyle = gradient;
    context.fillRect(x, y, Math.max(8, barWidth - 8), valueHeight);
    context.fillStyle = "#8aa3c2";
    context.font = '11px "SF Mono", monospace';
    context.fillText(String(bin.label), x, chartBottom + 16);
  });
}

function interpolatePoint(start, end, t) {
  return {
    x: start.x + ((end.x - start.x) * t),
    y: start.y + ((end.y - start.y) * t),
    z: start.z + ((end.z - start.z) * t),
  };
}

function buildOrigins(payload) {
  const origins = new Map(payload.initial_particles.map((particle) => [particle.particle_id, particle.position]));
  for (const collision of payload.collisions) {
    for (const productId of collision.product_ids) {
      origins.set(productId, collision.position);
    }
  }
  return origins;
}

function particleColor(particle, initialIds) {
  if (!initialIds.has(particle.particle_id)) {
    return "#b0ff9b";
  }
  return particle.velocity.x >= 0 ? "#5ce1e6" : "#f3a74f";
}

function drawBeamlineFrame(timestamp) {
  const { context, width, height } = resizeCanvas(elements.beamlineCanvas);
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#06121f";
  context.fillRect(0, 0, width, height);

  const chamberTop = height * 0.2;
  const chamberHeight = height * 0.6;
  const trackY = chamberTop + (chamberHeight * 0.5);
  context.strokeStyle = "rgba(140,190,255,0.18)";
  context.lineWidth = 2;
  context.strokeRect(36, chamberTop, width - 72, chamberHeight);

  const cavityWidth = 80;
  context.fillStyle = "rgba(115,180,255,0.16)";
  context.fillRect((width * 0.5) - (cavityWidth * 0.5), chamberTop, cavityWidth, chamberHeight);

  context.strokeStyle = "rgba(255,255,255,0.08)";
  context.beginPath();
  context.moveTo(36, trackY);
  context.lineTo(width - 36, trackY);
  context.stroke();

  if (!state.payload) {
    context.fillStyle = "#8aa3c2";
    context.font = '15px "SF Mono", monospace';
    context.fillText("Waiting for backend payload.", 24, 28);
    requestAnimationFrame(drawBeamlineFrame);
    return;
  }

  const payload = state.payload;
  const origins = buildOrigins(payload);
  const initialIds = new Set(payload.initial_particles.map((particle) => particle.particle_id));
  const animationProgress = (Math.sin((timestamp - state.beamAnimationStart) / 1100) + 1) * 0.5;
  const scaleX = (width - 120) / 0.18;
  const scaleY = (chamberHeight - 60) / 0.18;
  const toCanvas = (point) => ({
    x: width * 0.5 + (point.x * scaleX),
    y: trackY + (point.y * scaleY),
  });

  for (const collision of payload.collisions) {
    const center = toCanvas(collision.position);
    const pulse = 8 + (animationProgress * 14);
    context.beginPath();
    context.fillStyle = "rgba(255,93,115,0.18)";
    context.arc(center.x, center.y, pulse, 0, Math.PI * 2);
    context.fill();
    context.beginPath();
    context.fillStyle = "#ff5d73";
    context.arc(center.x, center.y, 3.6, 0, Math.PI * 2);
    context.fill();
  }

  for (const particle of payload.final_particles) {
    const origin = origins.get(particle.particle_id) || particle.position;
    const position = interpolatePoint(origin, particle.position, animationProgress);
    const screen = toCanvas(position);
    context.beginPath();
    context.fillStyle = particleColor(particle, initialIds);
    context.shadowBlur = 12;
    context.shadowColor = context.fillStyle;
    context.arc(screen.x, screen.y, initialIds.has(particle.particle_id) ? 4 : 3, 0, Math.PI * 2);
    context.fill();
    context.shadowBlur = 0;
  }

  context.fillStyle = "#8aa3c2";
  context.font = '12px "SF Mono", monospace';
  context.fillText(`initial=${payload.initial_particles.length}`, 24, height - 30);
  context.fillText(`final=${payload.final_particles.length}`, 24, height - 14);
  context.fillText(`tracker_hits=${payload.tracker_hits.length}`, width - 176, height - 30);
  context.fillText(`calo_hits=${payload.calorimeter_hits.length}`, width - 176, height - 14);

  requestAnimationFrame(drawBeamlineFrame);
}

function renderPayload(payload) {
  state.payload = payload;
  state.beamAnimationStart = performance.now();
  renderMetrics(payload.summary);
  renderSpecies(payload.summary);
  renderCollisions(payload.collisions);
  renderTimeline(payload.timeline);
  renderCalorimeter(payload.calorimeter_phi_totals);
  drawHistogram();
}

async function checkHealth() {
  try {
    await fetchJson("/api/health");
    setStatus(elements.healthStatus, "Backend: online", true);
  } catch (error) {
    setStatus(elements.healthStatus, `Backend: ${error.message}`, false);
  }
}

async function runSimulation() {
  if (state.pending) {
    return;
  }
  state.pending = true;
  elements.runButton.disabled = true;
  setStatus(elements.simulationStatus, "Simulation: running", true);
  try {
    const payload = await fetchJson("/api/simulate", {
      method: "POST",
      body: JSON.stringify(collectFormPayload()),
    });
    renderPayload(payload);
    setStatus(elements.simulationStatus, "Simulation: complete", true);
  } catch (error) {
    setStatus(elements.simulationStatus, `Simulation: ${error.message}`, false);
  } finally {
    state.pending = false;
    elements.runButton.disabled = false;
  }
}

async function boot() {
  elements.form.addEventListener("input", syncOutputs);
  elements.form.addEventListener("submit", (event) => {
    event.preventDefault();
    runSimulation();
  });
  elements.resetButton.addEventListener("click", () => {
    if (state.defaults) {
      applyDefaults(state.defaults);
    }
  });
  window.addEventListener("resize", drawHistogram);

  await checkHealth();
  try {
    const defaults = await fetchJson("/api/defaults");
    applyDefaults(defaults);
    await runSimulation();
  } catch (error) {
    setStatus(elements.simulationStatus, `Simulation: ${error.message}`, false);
  }
  requestAnimationFrame(drawBeamlineFrame);
}

boot();
