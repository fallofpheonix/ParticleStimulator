# Particle Stimulator

## Runtime Architecture

Authoritative runtime layout:

```text
src/
├── web/               HTTP API, event stream, ML service, static serving
├── simulation_core/   Integrated research-grade simulation pipeline from files.zip
├── accelerator/       Legacy MVP physics modules still used by unit tests
├── analysis/
├── core/
├── detectors/
├── physics/
├── simulation/
├── visualization/
├── models/            Reserved adapter package
├── services/          Reserved adapter package
└── utils/             Reserved utility package

frontend/
├── src/               React/Vite application
├── public/
└── simulation_dashboard/  Legacy static prototype reference

tests/

backend/
└── server.py          Launcher shim only
```

Removed architectural drift:
- duplicate backend API/controller tree under `backend/api_server/`
- duplicate cached tree under `backend/src/`
- all active backend execution now resolves from `src/`

## Active Entry Points

- Backend HTTP server: [src/web/server.py](/Users/fallofpheonix/Project/ParticleStimulator/src/web/server.py)
- Backend simulation adapter: [src/web/service.py](/Users/fallofpheonix/Project/ParticleStimulator/src/web/service.py)
- Integrated simulation core: [src/simulation_core](/Users/fallofpheonix/Project/ParticleStimulator/src/simulation_core)
- Frontend app: [frontend/src](/Users/fallofpheonix/Project/ParticleStimulator/frontend/src)
- Optional launcher: [backend/server.py](/Users/fallofpheonix/Project/ParticleStimulator/backend/server.py)

## Simulation Core

`files.zip` is vendored under `src/simulation_core/` and exposed through the existing HTTP service layer. No second API controller is used.

Pipeline:

```text
beam generation
→ accelerator transport
→ collision generation
→ detector simulation
→ event reconstruction
→ physics analysis
→ JSON payload adaptation in src/web/service.py
```

The frontend contract remains the same:
- `summary`
- `initial_particles`
- `final_particles`
- `collisions`
- `tracker_hits`
- `calorimeter_hits`
- `detector_hits`
- `timeline`

## API

- `GET /api/health`
- `GET /api/defaults`
- `GET /api/ml/status`
- `GET /api/events/recent`
- `POST /api/simulate`
- `POST /api/ml/train`
- `POST /api/ml/predict`

If `frontend/dist/index.html` exists, the backend serves the built React app. Otherwise it falls back to `src/web/static/`.

## Local Run

Backend:

```bash
python3 backend/server.py
```

Frontend dev:

```bash
cd frontend
npm install
npm run dev
```

Frontend production build:

```bash
cd frontend
npm install
npm run build
```

Tests:

```bash
python3 -m unittest discover -s tests
```

## Packaging

`src/` is now a real Python package root. Runtime and tests import `src.*` directly. `setup.py` packages `src` and `src.*` and declares the backend runtime dependencies.
