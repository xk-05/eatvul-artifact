.PHONY: check verify text-integrity compile artifact reported-values feature-importance dataset-summary smoke tables figures paper manifest

PYTHON ?= python

check: text-integrity compile reported-values smoke

verify: check feature-importance

text-integrity:
	$(PYTHON) scripts/check_text_integrity.py

compile:
	$(PYTHON) -m compileall scripts

artifact:
	$(PYTHON) scripts/check_artifact.py

reported-values:
	$(PYTHON) scripts/check_reported_values.py

feature-importance:
	$(PYTHON) scripts/export_gate_feature_importance.py

dataset-summary:
	$(PYTHON) scripts/eatvul_reproduce.py dataset-summary

smoke: artifact dataset-summary

tables:
	$(PYTHON) scripts/make_tables.py

figures:
	$(PYTHON) scripts/make_figures.py

paper:
	cd paper_eatvul_defense_framework/latex_submission && tectonic main.tex

manifest:
	$(PYTHON) scripts/build_manifest.py
