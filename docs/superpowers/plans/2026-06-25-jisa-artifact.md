# JISA Reproducibility Artifact Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare a clean local GitHub reproducibility artifact for the JISA defense-boundary manuscript.

**Architecture:** Keep the existing repository layout intact and add reviewer-facing documentation, lightweight checks, wrapper scripts, and CI. Do not move large or license-sensitive data; document missing objects explicitly.

**Tech Stack:** Python standard library for artifact checks, existing Conda `eatvul` environment for full experiments, LaTeX for manuscript compilation, GitHub Actions for lightweight CI.

---

### Task 1: Inventory and Documentation

**Files:**
- Create: `docs/ARTIFACT_INVENTORY.md`
- Create: `docs/TABLE_REPRODUCTION_MAP.md`
- Create: `docs/RUNBOOK.md`
- Create: `docs/LIMITATIONS_FOR_REVIEWERS.md`
- Modify: `README.md`
- Create: `ARTIFACT.md`
- Create: `REPRODUCIBILITY.md`
- Create: `DATA.md`
- Create: `MISSING_OBJECTS.md`

- [x] Map manuscript sources, result files, scripts, datasets, and missing objects.
- [x] Write reviewer-facing scope and reproducibility wording.
- [x] Avoid claims of reliable automatic sanitization.

### Task 2: Validation and Manifest Scripts

**Files:**
- Create: `scripts/check_artifact.py`
- Create: `scripts/build_manifest.py`
- Create: `scripts/make_tables.py`
- Create: `scripts/make_figures.py`

- [x] Check required documentation and result columns.
- [x] Verify unavailable objects are documented.
- [x] Generate SHA256 manifest for key artifact files.

### Task 3: Experiment Wrappers and CI

**Files:**
- Create: `scripts/run_gate.py`
- Create: `scripts/run_anomaly_baselines.py`
- Create: `scripts/run_diagnostic_deletion.py`
- Create: `scripts/run_quarantine_policy.py`
- Create: `.github/workflows/artifact-check.yml`
- Create: `Makefile`
- Create: `requirements.txt`
- Create: `environment.yml`
- Create: `.gitignore`

- [x] Add safe smoke and check targets.
- [x] Keep CI lightweight and avoid large downloads.

### Task 4: Manuscript Wording and Git Readiness

**Files:**
- Modify: `paper_eatvul_defense_framework/latex_submission/main_usenix_style_round3_clean.tex`

- [x] Remove anonymized-artifact claim because the configured remote is personal.
- [x] Keep TODO for final artifact URL until a repository is actually pushed.
- [ ] Commit selected artifact files only.
- [ ] Push only after explicit anonymity confirmation.
