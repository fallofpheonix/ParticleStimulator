# Particle Stimulator

A Monte Carlo particle physics simulator modelling proton-proton collisions at LHC energies. The pipeline covers beam generation, accelerator transport, hard scattering (QCD 2→2), parton shower, hadronisation, detector simulation, event reconstruction, and physics analysis. A React/Three.js frontend streams live results via WebSocket.

## Architecture

```text
src/
  simulation_core/   Full simulation pipeline (beam → collision → detector → analysis)
  web/               HTTP API, WebSocket event stream, ML service, static file serving
  analysis/          Offline Higgs classifier training utilities

frontend/
  src/               React/Vite visualisation and control surface

backend/
  server.py          Entry point: starts web.server + web.socket_server

tests/
  runtime/           Active integration and unit tests
  legacy/            Archived tests for removed subsystems

archive/
  backend_platform/  Decommissioned FastAPI backend
  legacy_simulator/  Pre-simulation_core engine prototypes
  frontend_artifacts/
```

The simulation pipeline is a single-pass staged design. Each stage (`BeamSource → BeamDynamics → CollisionEngine → DetectorSimulator → EventReconstructor → PhysicsAnalyser`) is self-contained and communicates only through `simulation_core.core_models` types — no stage imports from another stage's internals. This keeps the data flow explicit and makes individual stages testable in isolation.

The HTTP API is a plain `ThreadingHTTPServer` (no framework dependency). The WebSocket event stream uses `websockets`. The ML service wraps scikit-learn/XGBoost behind a training thread so inference never blocks the API.

## Active Entry Points

- HTTP API: [`src/web/server.py`](src/web/server.py)
- WebSocket event stream: [`src/web/socket_server.py`](src/web/socket_server.py)
- Simulation adapter: [`src/web/service.py`](src/web/service.py)
- Simulation pipeline: [`src/simulation_core/`](src/simulation_core/)
- Higgs analysis: [`src/analysis/`](src/analysis/)
- Frontend: [`frontend/src/`](frontend/src/)
- Server launcher: [`backend/server.py`](backend/server.py)

## API Surface

- `GET /api/health` — liveness + component status
- `GET /api/defaults` — default simulation parameters
- `GET /api/events/recent` — last N collision events
- `GET /api/ml/status` — training job status and metrics
- `POST /api/simulate` — run a simulation and return results
- `POST /api/ml/train` — start a background training job
- `POST /api/ml/predict` — classify a single event (requires trained model)
- `ws://127.0.0.1:8001/events` — live event stream

## Packaging

- Runtime packages are installed from `src/` via `setup.py`.
- Active imports use package names only:
  - `web.*`
  - `simulation_core.*`
  - `analysis.*`
- No active runtime path should depend on `PYTHONPATH=src`.

## Install

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -r requirements-ml.txt
.venv/bin/python -m pip install -e .
```

Optional platform dependencies:

```bash
.venv/bin/python -m pip install -r requirements-optional.txt
```

## Run

Backend:

```bash
.venv/bin/python backend/server.py
```

Direct package entrypoint:

```bash
.venv/bin/python -m web.server
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Validation

Runtime tests:

```bash
.venv/bin/python -m unittest discover -s tests/runtime
```

Frontend build:

```bash
cd frontend
npm run build
```

## Archived Systems

- `archive/backend_platform/`: unused backend API/config/data pipeline/event stream/infrastructure tree
- `archive/legacy_simulator/`: pre-`simulation_core` engine packages and examples
- `archive/frontend_artifacts/`: old frontend dumps and static prototypes
