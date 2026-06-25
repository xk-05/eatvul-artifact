.PHONY: check reported-values feature-importance smoke tables figures paper manifest

PYTHON ?= python

check:
	$(PYTHON) scripts/check_artifact.py

reported-values:
	$(PYTHON) scripts/check_reported_values.py

feature-importance:
	$(PYTHON) scripts/export_gate_feature_importance.py

smoke: check
	$(PYTHON) scripts/eatvul_reproduce.py dataset-summary

tables:
	$(PYTHON) scripts/make_tables.py

figures:
	$(PYTHON) scripts/make_figures.py

paper:
	cd paper_eatvul_defense_framework/latex_submission && tectonic main.tex

manifest:
	$(PYTHON) scripts/build_manifest.py
