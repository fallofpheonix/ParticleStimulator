from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd


FEATURE_NAMES = [
    "lepton_pt",
    "lepton_eta",
    "lepton_phi",
    "missing_energy_magnitude",
    "missing_energy_phi",
    "jet1_pt",
    "jet1_eta",
    "jet1_phi",
    "jet1_b_tag",
    "jet2_pt",
    "jet2_eta",
    "jet2_phi",
    "jet2_b_tag",
    "jet3_pt",
    "jet3_eta",
    "jet3_phi",
    "jet3_b_tag",
    "jet4_pt",
    "jet4_eta",
    "jet4_phi",
    "jet4_b_tag",
    "m_jj",
    "m_jjj",
    "m_lv",
    "m_jlv",
    "m_bb",
    "m_wbb",
    "m_wwbb",
]

_DEFAULT_DATASET_CANDIDATES = (
    "data/HIGGS.csv",
    "data/HIGGS.csv.gz",
    "HIGGS.csv",
    "HIGGS.csv.gz",
)


@dataclass(frozen=True, slots=True)
class HiggsTrainingConfig:
    model_backend: str = "auto"
    sample_size: int | None = 250_000
    test_size: float = 0.2
    random_state: int = 42
    n_estimators: int = 120
    max_depth: int = 6
    learning_rate: float = 0.1
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    n_jobs: int = 1


_DEFAULT_TRAINING_CONFIG = HiggsTrainingConfig()


@dataclass(frozen=True, slots=True)
class HiggsTrainingMetrics:
    model_backend: str
    accuracy: float
    roc_auc: float
    rows_loaded: int
    signal_fraction: float


@dataclass(frozen=True, slots=True)
class HiggsTrainingResult:
    dataset_path: Path
    metrics: HiggsTrainingMetrics
    artifact_path: Path | None = None


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _require_training_deps() -> SimpleNamespace:
    import joblib
    import numpy as np
    import pandas as pd
    from sklearn.metrics import accuracy_score, roc_auc_score
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    return SimpleNamespace(
        joblib=joblib,
        np=np,
        pd=pd,
        accuracy_score=accuracy_score,
        hist_gradient_boosting=HistGradientBoostingClassifier,
        roc_auc_score=roc_auc_score,
        train_test_split=train_test_split,
        standard_scaler=StandardScaler,
    )


def _try_import_xgboost() -> Any | None:
    try:
        import xgboost as xgb
    except Exception:
        return None
    return xgb


def _xgboost_runtime_error() -> RuntimeError:
    return RuntimeError(
        "xgboost backend requested but the native XGBoost runtime could not be loaded. "
        "Install the OpenMP runtime required by XGBoost on macOS (for example `brew install libomp`) "
        "or rerun with `--backend hist_gbdt`."
    )


def discover_higgs_dataset(dataset_path: str | Path | None = None, project_root: str | Path | None = None) -> Path:
    if dataset_path is not None:
        resolved = Path(dataset_path).expanduser().resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"HIGGS dataset not found: {resolved}")
        return resolved

    root = Path(project_root).expanduser().resolve() if project_root is not None else _project_root()
    for candidate in _DEFAULT_DATASET_CANDIDATES:
        path = root / candidate
        if path.exists():
            return path.resolve()
    raise FileNotFoundError(
        "HIGGS dataset not found. Checked: "
        + ", ".join(str((root / candidate).resolve()) for candidate in _DEFAULT_DATASET_CANDIDATES)
    )


def load_higgs_dataframe(dataset_path: str | Path, sample_size: int | None) -> "pd.DataFrame":
    deps = _require_training_deps()
    columns = ["label"] + FEATURE_NAMES
    return deps.pd.read_csv(dataset_path, header=None, names=columns, nrows=sample_size)


def _prepare_training_frame(dataframe: "pd.DataFrame", config: HiggsTrainingConfig) -> dict[str, Any]:
    deps = _require_training_deps()
    features = dataframe[FEATURE_NAMES].values.astype(deps.np.float32)
    labels = dataframe["label"].values.astype(deps.np.int32)

    x_train, x_test, y_train, y_test = deps.train_test_split(
        features,
        labels,
        test_size=config.test_size,
        random_state=config.random_state,
        stratify=labels,
    )

    scaler = deps.standard_scaler()
    x_train = scaler.fit_transform(x_train)
    x_test = scaler.transform(x_test)
    return {
        "x_train": x_train,
        "x_test": x_test,
        "y_train": y_train,
        "y_test": y_test,
        "scaler": scaler,
    }


def _train_gradient_model(prepared: dict[str, Any], config: HiggsTrainingConfig) -> tuple[Any, str]:
    deps = _require_training_deps()
    backend = config.model_backend
    if backend not in {"auto", "xgboost", "hist_gbdt"}:
        raise ValueError(f"unsupported model backend: {backend}")

    xgb = _try_import_xgboost()
    if backend in {"auto", "xgboost"} and xgb is not None:
        model = xgb.XGBClassifier(
            n_estimators=config.n_estimators,
            max_depth=config.max_depth,
            learning_rate=config.learning_rate,
            subsample=config.subsample,
            colsample_bytree=config.colsample_bytree,
            eval_metric="logloss",
            random_state=config.random_state,
            n_jobs=config.n_jobs,
            verbosity=0,
        )
        resolved_backend = "xgboost"
    elif backend == "xgboost":
        raise _xgboost_runtime_error()
    else:
        model = deps.hist_gradient_boosting(
            learning_rate=config.learning_rate,
            max_depth=config.max_depth,
            max_iter=config.n_estimators,
            random_state=config.random_state,
        )
        resolved_backend = "hist_gbdt"

    model.fit(prepared["x_train"], prepared["y_train"])
    return model, resolved_backend


def _evaluate_model(
    model: Any,
    prepared: dict[str, Any],
    dataframe: "pd.DataFrame",
    backend: str,
) -> HiggsTrainingMetrics:
    deps = _require_training_deps()
    y_prob = model.predict_proba(prepared["x_test"])[:, 1]
    y_pred = model.predict(prepared["x_test"])
    return HiggsTrainingMetrics(
        model_backend=backend,
        accuracy=float(deps.accuracy_score(prepared["y_test"], y_pred)),
        roc_auc=float(deps.roc_auc_score(prepared["y_test"], y_prob)),
        rows_loaded=int(len(dataframe)),
        signal_fraction=float(dataframe["label"].mean()),
    )


def save_training_artifact(
    model: Any,
    scaler: Any,
    metrics: HiggsTrainingMetrics,
    output_path: str | Path,
) -> Path:
    deps = _require_training_deps()
    artifact = {
        "model": model,
        "scaler": scaler,
        "feature_names": FEATURE_NAMES,
        "metrics": asdict(metrics),
    }
    resolved = Path(output_path).expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    deps.joblib.dump(artifact, resolved)
    return resolved


def train_higgs_baseline(
    dataset_path: str | Path | None = None,
    config: HiggsTrainingConfig | None = None,
    artifact_path: str | Path | None = None,
) -> HiggsTrainingResult:
    effective_config = config or HiggsTrainingConfig()
    resolved_dataset = discover_higgs_dataset(dataset_path)
    dataframe = load_higgs_dataframe(resolved_dataset, effective_config.sample_size)
    prepared = _prepare_training_frame(dataframe, effective_config)
    model, backend = _train_gradient_model(prepared, effective_config)
    metrics = _evaluate_model(model, prepared, dataframe, backend)

    saved_artifact: Path | None = None
    if artifact_path is not None:
        saved_artifact = save_training_artifact(model, prepared["scaler"], metrics, artifact_path)

    return HiggsTrainingResult(
        dataset_path=resolved_dataset,
        metrics=metrics,
        artifact_path=saved_artifact,
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a Higgs signal/background baseline classifier.")
    parser.add_argument("--dataset", type=Path, default=None, help="Path to HIGGS.csv or HIGGS.csv.gz")
    parser.add_argument("--sample-size", type=int, default=_DEFAULT_TRAINING_CONFIG.sample_size, help="Rows to load")
    parser.add_argument("--artifact", type=Path, default=None, help="Optional output path for a joblib artifact")
    parser.add_argument(
        "--backend",
        choices=("auto", "xgboost", "hist_gbdt"),
        default=_DEFAULT_TRAINING_CONFIG.model_backend,
        help="Training backend",
    )
    parser.add_argument("--estimators", type=int, default=_DEFAULT_TRAINING_CONFIG.n_estimators, help="Boosting iterations")
    parser.add_argument("--max-depth", type=int, default=_DEFAULT_TRAINING_CONFIG.max_depth, help="Tree max depth")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    config = HiggsTrainingConfig(
        model_backend=args.backend,
        sample_size=args.sample_size,
        n_estimators=args.estimators,
        max_depth=args.max_depth,
    )
    result = train_higgs_baseline(args.dataset, config, args.artifact)
    print(
        json.dumps(
            {
                "dataset_path": str(result.dataset_path),
                "artifact_path": str(result.artifact_path) if result.artifact_path is not None else None,
                "metrics": asdict(result.metrics),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
