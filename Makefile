PYTHON   := .venv/bin/python

.PHONY: install test test-legacy run-web fix-dataset

install:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -r requirements-ml.txt
	$(PYTHON) -m pip install -e .

test:
	$(PYTHON) -m unittest discover -s tests/runtime

test-legacy:
	$(PYTHON) -m unittest discover -s tests/legacy

## Run the backend API and frontend dashboard
run-web:
	$(PYTHON) backend/server.py

## Move HIGGS.csv.gz from root to data/ after download completes
fix-dataset:
	@if [ -f HIGGS.csv.gz ]; then mv HIGGS.csv.gz data/HIGGS.csv.gz && echo "Moved HIGGS.csv.gz -> data/HIGGS.csv.gz"; \
	elif [ -f data/HIGGS.csv.gz ]; then echo "data/HIGGS.csv.gz already in place"; \
	else echo "HIGGS.csv.gz not found. Run: bash data/download_higgs_dataset.sh"; fi
