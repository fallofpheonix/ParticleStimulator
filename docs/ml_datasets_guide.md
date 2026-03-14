# Machine Learning Datasets for Particle Physics

This document outlines the primary datasets used for training Machine Learning models in particle physics simulating LHC experiments.

## 1. Higgs Boson Dataset (Best for ML Beginners)
Created from simulations of proton collisions similar to the LHC.
* **Contains**: ~11 million collision events (UCI Machine Learning Repository) or the Kaggle Challenge subset.
* **Features**: 28 physics features (lepton momentum, missing energy, jet counts, invariant mass).
* **Label**: Higgs signal vs background.
* **ML Tasks**: Classification, anomaly detection, feature importance.
* **Models**: Random Forest, XGBoost, Neural Networks.

## 2. LHC Open Data
Real experimental data released by CERN.
* **Contains**: Proton collision events, particle tracks, detector signals.
* **ML Tasks**: Particle classification, track reconstruction, jet tagging.

## 3. Jet Tagging Dataset
Used to classify particle jets from collisions.
* **Features**: Jet momentum, energy, particle multiplicity, angular distributions.
* **ML Tasks**: Quark vs gluon classification, jet flavor tagging.
* **Models**: Graph Neural Networks (GNNs), CNNs, Transformers.

## 4. Track Reconstruction Dataset
Used to reconstruct particle trajectories in detectors.
* **Features**: Detector hits, sensor coordinates, time measurements.
* **ML Tasks**: Track reconstruction, vertex prediction.

## 5. Synthetic Collision Dataset
Generated via our own particle simulator Python/C++ engine.
* **Advantages**: Unlimited data, custom physics scenarios.

## 6. Recommended ML Pipeline
```text
collision dataset -> feature extraction -> training dataset -> ML model training -> event classification
```

## 7. Best Dataset Choice (Recommendation)
* **Beginner**: Higgs Boson Dataset
* **Intermediate**: Jet tagging datasets
* **Advanced**: LHC Open Data

**Ultimate Project Goal**: Train a model that successfully detects the Higgs boson from simulated collision events produced like those at the Large Hadron Collider.

## 8. Current Repository Implementation
- Loader accepts `HIGGS.csv` and `HIGGS.csv.gz`.
- Dataset discovery checks `data/` first, then the repository root.
- Baseline training entry point:
  - `.venv/bin/python machine_learning/event_classifier/higgs_classifier.py --dataset HIGGS.csv.gz --sample-size 5000 --artifact data/processed_events/higgs_baseline.joblib`
- Backend selection:
  - `auto`: use XGBoost when the native library is loadable
  - `hist_gbdt`: force scikit-learn histogram gradient boosting
  - `xgboost`: require XGBoost and fail fast if its native runtime is broken
- Dependency split:
  - `requirements.txt`: runtime dependencies
  - `requirements-ml.txt`: ML training dependencies
  - `requirements-optional.txt`: optional platform dependencies
