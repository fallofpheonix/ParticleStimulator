PYTHON   := .venv/bin/python
PYTHONPATH := src

.PHONY: test test-ml run-collision run-beam run-web fix-dataset

## Run the core simulation test suite (no ML deps needed)
test:
	PYTHONPATH=$(PYTHONPATH) python3 -m unittest discover -s tests

## Run ALL tests including the ML pipeline (requires .venv)
test-all:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m unittest discover -s tests

## Run the proton collision example
run-collision:
	PYTHONPATH=$(PYTHONPATH) python3 examples/proton_collision.py

## Run the beam simulation example
run-beam:
	PYTHONPATH=$(PYTHONPATH) python3 examples/beam_simulation.py

## Run the backend API and frontend dashboard
run-web:
	PYTHONPATH=$(PYTHONPATH) python3 -m web.server

## Train the Higgs baseline classifier (5k rows, fast)
train-higgs-fast:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) machine_learning/event_classifier/higgs_classifier.py \
		--dataset data/HIGGS.csv.gz \
		--sample-size 5000 \
		--artifact data/processed_events/higgs_baseline.joblib

## Train on 1M rows (slower, better accuracy)
train-higgs:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) machine_learning/event_classifier/higgs_classifier.py \
		--dataset data/HIGGS.csv.gz \
		--sample-size 1000000 \
		--artifact data/processed_events/higgs_baseline.joblib

## Move HIGGS.csv.gz from root to data/ after download completes
fix-dataset:
	@if [ -f HIGGS.csv.gz ]; then mv HIGGS.csv.gz data/HIGGS.csv.gz && echo "Moved HIGGS.csv.gz -> data/HIGGS.csv.gz"; \
	elif [ -f data/HIGGS.csv.gz ]; then echo "data/HIGGS.csv.gz already in place"; \
	else echo "HIGGS.csv.gz not found. Run: bash data/download_higgs_dataset.sh"; fi
