# Frontend Workspace

This directory now contains the unified React application for the simulator UI.

## Source Of Truth
- `src/`: integrated React frontend application
- `package.json`: single dependency graph for `react`, `three`, `zustand`, `d3`, and build tooling
- `vite.config.js`: alias map and `/api` proxy to the Python backend at `127.0.0.1:8000`

## Integrated Architecture
```text
src/
  app/
  layout/
  renderer/
  ui/
  analytics/
  events/
  detector/
  timeline/
  config/
  debug/
  assets/
  collaboration/
  experiments/
  ml/
  settings/
  store/
  services/
```

## Runtime
```bash
npm install
npm run dev
```

## Backend Contract
- `GET /api/health`
- `GET /api/defaults`
- `POST /api/simulate`
- `GET /api/events/recent`
- `POST /api/ml/train`
- `GET /api/ml/status`
- `POST /api/ml/predict`
- `ws://127.0.0.1:8001/events`

## New Frontend Systems
- `experiments/`: run registry and export surface
- `ml/`: model training, metrics, and event prediction
- `settings/`: theme, API/WebSocket connection settings, persisted simulation defaults
- `services/exportService.js`: JSON/CSV/PNG export helpers

## Legacy Files
- `simulation_dashboard/`: plain-JS prototype retained for reference
- `event_viewer/`: reserved placeholder
- `ui_controls/`: reserved placeholder
- `../frontendofpraticlestimulator/`: legacy AI-generated component dump used as adapter input for replay and event-inspection components; not a runtime application
