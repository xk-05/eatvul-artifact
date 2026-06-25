.PHONY: check smoke tables figures paper manifest

PYTHON ?= python

check:
	$(PYTHON) scripts/check_artifact.py

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
