from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from threading import Lock, Thread
from typing import Any

from analysis.higgs import (
    FEATURE_NAMES,
    HiggsTrainingConfig,
    _evaluate_model,
    _prepare_training_frame,
    _require_training_deps,
    _train_gradient_model,
    discover_higgs_dataset,
    load_higgs_dataframe,
    save_training_artifact,
)


def _artifact_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "processed_events" / "higgs_latest.joblib"


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _particle_momentum(particle: dict[str, Any]) -> float:
    px = _coerce_float(particle.get("px"))
    py = _coerce_float(particle.get("py"))
    pz = _coerce_float(particle.get("pz"))
    return (px * px + py * py + pz * pz) ** 0.5


def _feature_map_from_event(event: dict[str, Any]) -> dict[str, float]:
    particles = list(event.get("particles") or [])
    ordered = sorted(particles, key=_particle_momentum, reverse=True)
    jets = int(event.get("jets") or event.get("collision", {}).get("jets") or 0)
    mass = _coerce_float(event.get("collision", {}).get("mass"))
    energy = _coerce_float(event.get("collision_energy"))
    muons = sum(1 for particle in particles if str(particle.get("type", "")).startswith("muon"))
    leptons = [particle for particle in ordered if str(particle.get("type", "")) in {"electron", "muon", "positron"}]
    leading_lepton = leptons[0] if leptons else {}

    def component(source: dict[str, Any], key: str) -> float:
        return _coerce_float(source.get(key))

    def jet_particle(index: int) -> dict[str, Any]:
        return ordered[index] if index < len(ordered) else {}

    features = {
        "lepton_pt": _particle_momentum(leading_lepton),
        "lepton_eta": component(leading_lepton, "pz"),
        "lepton_phi": component(leading_lepton, "py"),
        "missing_energy_magnitude": max(0.0, energy - sum(_particle_momentum(particle) for particle in ordered[:4])),
        "missing_energy_phi": component(leading_lepton, "px"),
        "jet1_pt": _particle_momentum(jet_particle(0)),
        "jet1_eta": component(jet_particle(0), "pz"),
        "jet1_phi": component(jet_particle(0), "py"),
        "jet1_b_tag": 1.0 if "b" in str(jet_particle(0).get("type", "")) else 0.0,
        "jet2_pt": _particle_momentum(jet_particle(1)),
        "jet2_eta": component(jet_particle(1), "pz"),
        "jet2_phi": component(jet_particle(1), "py"),
        "jet2_b_tag": 1.0 if "b" in str(jet_particle(1).get("type", "")) else 0.0,
        "jet3_pt": _particle_momentum(jet_particle(2)),
        "jet3_eta": component(jet_particle(2), "pz"),
        "jet3_phi": component(jet_particle(2), "py"),
        "jet3_b_tag": 1.0 if "b" in str(jet_particle(2).get("type", "")) else 0.0,
        "jet4_pt": _particle_momentum(jet_particle(3)),
        "jet4_eta": component(jet_particle(3), "pz"),
        "jet4_phi": component(jet_particle(3), "py"),
        "jet4_b_tag": 1.0 if "b" in str(jet_particle(3).get("type", "")) else 0.0,
        "m_jj": mass,
        "m_jjj": mass + jets,
        "m_lv": energy / 1000.0,
        "m_jlv": (mass + energy / 1000.0) / 2.0,
        "m_bb": float(muons),
        "m_wbb": float(jets),
        "m_wwbb": float(len(particles)),
    }
    return {name: float(features.get(name, 0.0)) for name in FEATURE_NAMES}


def _synthetic_higgs_dataframe(sample_size: int):
    deps = _require_training_deps()
    rows = max(1000, sample_size)
    rng = deps.np.random.default_rng(42)
    labels = rng.integers(0, 2, size=rows)
    features = rng.normal(0.0, 1.0, size=(rows, len(FEATURE_NAMES))).astype(deps.np.float32)
    features[:, 0] += labels * 1.8
    features[:, 5] += labels * 1.2
    features[:, 21] += labels * 0.9
    features[:, 26] += labels * 1.1
    dataframe = deps.pd.DataFrame(features, columns=FEATURE_NAMES)
    dataframe.insert(0, "label", labels)
    return dataframe


class MLService:
    def __init__(self) -> None:
        self._lock = Lock()
        self._thread: Thread | None = None
        self._model: Any | None = None
        self._scaler: Any | None = None
        self._status: dict[str, Any] = {
            "status": "idle",
            "progress": 0.0,
            "dataset_path": None,
            "artifact_path": None,
            "metrics": None,
            "error": None,
        }
        self._try_load_artifact()

    def start_training(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return dict(self._status)
            self._status = {
                "status": "queued",
                "progress": 0.0,
                "dataset_path": None,
                "artifact_path": None,
                "metrics": None,
                "error": None,
            }
            self._thread = Thread(target=self._run_training, args=(payload or {},), daemon=True)
            self._thread.start()
            return dict(self._status)

    def status(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._status)

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            model = self._model
            scaler = self._scaler
        if model is None or scaler is None:
            raise RuntimeError("model is not trained")

        features = payload.get("features")
        if isinstance(features, dict):
            feature_map = {name: _coerce_float(features.get(name)) for name in FEATURE_NAMES}
        elif isinstance(features, list):
            feature_map = {name: _coerce_float(value) for name, value in zip(FEATURE_NAMES, features)}
        else:
            feature_map = _feature_map_from_event(payload.get("event") or payload)

        ordered = [feature_map[name] for name in FEATURE_NAMES]
        prepared = scaler.transform([ordered])
        probabilities = model.predict_proba(prepared)[0]
        signal_probability = float(probabilities[1])
        prediction = int(signal_probability >= 0.5)

        return {
            "prediction": prediction,
            "label": "signal" if prediction else "background",
            "probability_signal": signal_probability,
            "probability_background": float(probabilities[0]),
            "features": feature_map,
        }

    def _run_training(self, payload: dict[str, Any]) -> None:
        deps = _require_training_deps()
        try:
            from sklearn.metrics import confusion_matrix, precision_score, recall_score

            self._set_status(status="running", progress=0.1)
            config = HiggsTrainingConfig(
                model_backend=str(payload.get("backend", "auto")),
                sample_size=int(payload["sample_size"]) if payload.get("sample_size") else 25_000,
                n_estimators=int(payload.get("estimators", 48)),
                max_depth=int(payload.get("max_depth", 6)),
                random_state=int(payload.get("random_state", 42)),
            )

            dataset_hint = payload.get("dataset")
            try:
                dataset = discover_higgs_dataset(dataset_hint)
                dataframe = load_higgs_dataframe(dataset, config.sample_size)
                dataset_label = str(dataset)
            except FileNotFoundError:
                dataframe = _synthetic_higgs_dataframe(config.sample_size or 25_000)
                dataset_label = "synthetic://higgs"

            self._set_status(dataset_path=dataset_label, progress=0.2)
            self._set_status(progress=0.45)
            prepared = _prepare_training_frame(dataframe, config)
            model, backend = _train_gradient_model(prepared, config)
            self._set_status(progress=0.75)
            metrics = _evaluate_model(model, prepared, dataframe, backend)
            predictions = model.predict(prepared["x_test"])
            confusion = confusion_matrix(prepared["y_test"], predictions).tolist()
            precision = float(precision_score(prepared["y_test"], predictions))
            recall = float(recall_score(prepared["y_test"], predictions))
            artifact_path = save_training_artifact(model, prepared["scaler"], metrics, _artifact_path())

            with self._lock:
                self._model = model
                self._scaler = prepared["scaler"]
                self._status = {
                    "status": "completed",
                    "progress": 1.0,
                    "dataset_path": dataset_label,
                    "artifact_path": str(artifact_path),
                    "metrics": {
                        **asdict(metrics),
                        "precision": precision,
                        "recall": recall,
                        "confusion_matrix": confusion,
                    },
                    "error": None,
                }
        except Exception as exc:  # pragma: no cover - defensive top-level status management
            self._set_status(status="error", progress=1.0, error=str(exc))

    def _try_load_artifact(self) -> None:
        artifact_path = _artifact_path()
        if not artifact_path.exists():
            return
        try:
            deps = _require_training_deps()
            artifact = deps.joblib.load(artifact_path)
            self._model = artifact.get("model")
            self._scaler = artifact.get("scaler")
            self._status = {
                "status": "completed",
                "progress": 1.0,
                "dataset_path": None,
                "artifact_path": str(artifact_path),
                "metrics": artifact.get("metrics"),
                "error": None,
            }
        except Exception:
            return

    def _set_status(self, **patch: Any) -> None:
        with self._lock:
            self._status = {
                **self._status,
                **patch,
            }


ml_service = MLService()
