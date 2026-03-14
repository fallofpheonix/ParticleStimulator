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

## Legacy Files
- `simulation_dashboard/`: plain-JS prototype retained for reference
- `event_viewer/`: reserved placeholder
- `ui_controls/`: reserved placeholder
