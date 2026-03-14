# Particle Stimulator

## Status
Current repository status is structural definition plus an executable Python MVP.

## Implemented Scope
- Lorentz-force particle transport in a simplified beamline
- Uniform dipole field, weak quadrupole focusing, and RF cavity acceleration
- Deterministic toy collision synthesis for close, head-on particles
- Silicon tracker hit generation and calorimeter energy deposits
- JSON event logging, text reporting, and example entry points
- Higgs dataset baseline classification pipeline with model artifact export

## Project Structure
```text
src/
├── accelerator/   Beamline, magnets, RF cavity, vacuum aperture
├── core/          Constants, Vector3, Particle
├── detectors/     Tracker, calorimeter, event logger
├── physics/       Relativity, electromagnetism, collision, decay
├── analysis/      Higgs dataset loading, training, evaluation, artifact export
├── simulation/    Time step selection, integration, engine
├── visualization/ Text report and dashboard metrics
└── web/           HTTP server, API serialization, static frontend assets
```

## Runtime
- Python `>=3.11`
- Core simulator: no third-party runtime dependencies
- ML pipeline: `numpy`, `pandas`, `scikit-learn`, `joblib`
- Optional XGBoost backend: install [requirements-xgboost.txt](/Users/fallofpheonix/Project/ParticleStimulator/requirements-xgboost.txt) and satisfy native OpenMP requirements on macOS

## Usage
```bash
PYTHONPATH=src python3 examples/beam_simulation.py
PYTHONPATH=src python3 examples/proton_collision.py
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=src python3 -m web.server
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python machine_learning/event_classifier/higgs_classifier.py \
  --dataset HIGGS.csv.gz \
  --sample-size 5000 \
  --artifact data/processed_events/higgs_baseline.joblib
.venv/bin/pip install -r requirements-xgboost.txt  # optional
```

## Constraints
- This is not a research-grade simulator.
- Collision and detector response are intentionally simplified and deterministic.
- The implementation is designed to establish execution flow, interfaces, and testable structure.
- The ML pipeline prefers `xgboost` but falls back to scikit-learn histogram boosting when the native XGBoost runtime is unavailable.

## Web Dashboard
- Runtime entrypoint: [src/web/server.py](/Users/fallofpheonix/Project/ParticleStimulator/src/web/server.py)
- API serializer: [src/web/service.py](/Users/fallofpheonix/Project/ParticleStimulator/src/web/service.py)
- Static bundle: [src/web/static/index.html](/Users/fallofpheonix/Project/ParticleStimulator/src/web/static/index.html)
- Compatibility wrapper: [backend/server.py](/Users/fallofpheonix/Project/ParticleStimulator/backend/server.py)
- API endpoints:
  - `GET /api/health`
  - `GET /api/defaults`
  - `POST /api/simulate`
- Start with `make run-web`, then open `http://127.0.0.1:8000`
