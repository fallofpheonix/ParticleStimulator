# Particle Stimulator

## Authoritative Runtime

```text
src/
  web/               HTTP API, websocket stream, ML service, static serving
  simulation_core/   Integrated simulation pipeline
  analysis/          Offline Higgs training utilities

frontend/
  src/               React/Vite frontend runtime

backend/
  server.py          Thin launcher for web.server + web.socket_server

tests/
  runtime/           Active runtime validation
  legacy/            Archived test coverage for removed systems

archive/
  backend_platform/  Orphan backend platform tree
  legacy_simulator/  Pre-simulation_core engine and examples
  frontend_artifacts/
```

## Active Entry Points

- Backend HTTP API: [server.py](/Users/fallofpheonix/Project/ParticleStimulator/src/web/server.py)
- Backend event stream: [socket_server.py](/Users/fallofpheonix/Project/ParticleStimulator/src/web/socket_server.py)
- Backend simulation adapter: [service.py](/Users/fallofpheonix/Project/ParticleStimulator/src/web/service.py)
- Simulation engine: [simulation_core](/Users/fallofpheonix/Project/ParticleStimulator/src/simulation_core)
- Analysis package: [analysis](/Users/fallofpheonix/Project/ParticleStimulator/src/analysis)
- Frontend runtime: [frontend/src](/Users/fallofpheonix/Project/ParticleStimulator/frontend/src)
- Backend launcher: [backend/server.py](/Users/fallofpheonix/Project/ParticleStimulator/backend/server.py)

## API Surface

- `GET /api/health`
- `GET /api/defaults`
- `GET /api/events/recent`
- `GET /api/ml/status`
- `POST /api/simulate`
- `POST /api/ml/train`
- `POST /api/ml/predict`
- `ws://127.0.0.1:8001/events`

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
