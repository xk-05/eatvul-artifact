# JISA Final Google Drive to GitHub Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the final JISA manuscript, TeX, derived evidence, run manifests, reproduction scripts, tests, and corrected documentation from Google Drive to the existing GitHub draft pull request without publishing the raw dataset archive.

**Architecture:** Treat `JISA-Final-2026-07-17` as the immutable release source and overlay its reviewable files onto the current artifact repository. Preserve the package's working paths for scripts, results, generated tables, and figures; add Drive-level provenance under `manifests/jisa_final/`; then make the repository entry points and validation tools describe and verify the final three-RQ, Tables 2--9 manuscript.

**Tech Stack:** Python 3.9+, pandas, NumPy, scikit-learn, pytest, SHA-256, Elsevier CAS LaTeX, Git, GitHub CLI.

## Global Constraints

- Source of truth: Google Drive folder `JISA-Final-2026-07-17`.
- Continue on branch `codex/sync-google-drive-20260717` and draft pull request #1.
- Never add `Code and Dataset.zip`, raw AST-token splits, credentials, caches, or machine-local paths.
- Commit extracted reviewable files, not duplicate source archives.
- Preserve package paths when scripts and tests depend on them.
- Make the final PDF, `main_jisa.tex`, generated Tables 2--9, and JISA figures canonical.
- Do not merge to `main`.

## File Structure

Files copied unchanged from the final submission package:

- `paper_eatvul_defense_framework/latex_submission/main_jisa.tex`
- `paper_eatvul_defense_framework/latex_submission/main_jisa.pdf`
- `paper_eatvul_defense_framework/latex_submission/references.bib`
- `paper_eatvul_defense_framework/latex_submission/{README.md,highlights.txt,cover_letter_jisa.txt,elsevier_declarations_draft.txt}`
- `paper_eatvul_defense_framework/latex_submission/{cas-dc.cls,cas-common.sty,cas-model2-names.bst}`
- `paper_eatvul_defense_framework/latex_submission/thumbnails/*.jpeg`
- `paper_eatvul_defense_framework/latex_submission/generated/jisa_*.tex`
- `paper_eatvul_defense_framework/figures_submission_jisa/*.pdf`
- `results/jisa_matched_budget_summary.csv`
- `results/jisa_evidence_bundle.json`
- `results/jisa_confidence_sensitivity/{run_manifest.json,confidence_adv_samples.csv,duplicate_sensitivity.csv,token_length_profile.csv,confidence_summary.csv}`
- `scripts/materialize_jisa_evidence.py`
- `scripts/jisa_confidence_sensitivity.py`
- `tests/test_materialize_jisa_evidence.py`
- `tests/test_jisa_confidence_sensitivity.py`
- `requirements_jisa.txt`
- `JISA_REVISION_NOTES.md`

Files added from the Drive-level run-manifest folder:

- `manifests/jisa_final/FINAL_RUN_MANIFEST.json`
- `manifests/jisa_final/confidence_run_manifest.json`

Files created or modified for repository integration:

- Create `tests/test_jisa_release_boundary.py`: enforce canonical release files and exclusions.
- Modify `scripts/check_reported_values.py`: verify final Tables 2--9 instead of superseded tables.
- Modify `tests/test_artifact_checks.py`: assert the final checker reports Tables 2--9.
- Modify `scripts/check_artifact.py`: require the final JISA release structure.
- Modify `scripts/check_text_integrity.py`: include the final JSON/CSV/TeX inputs in parseability checks if its current discovery rules omit them.
- Modify `scripts/build_manifest.py`: include final release files and exclude local worktrees/caches.
- Modify `README.md`, `ARTIFACT.md`, `DATA.md`, `REPRODUCIBILITY.md`, `SUBMISSION_JISA.md`, and `CITATION.cff`: make the final manuscript and data boundary canonical.
- Modify `docs/TABLE_REPRODUCTION_MAP.md`, `docs/ARTIFACT_INVENTORY.md`, `docs/RUNBOOK.md`, and `docs/LIMITATIONS_FOR_REVIEWERS.md`: reconcile reviewer guidance.
- Modify `results/per_sample/README.md`: identify the released sample-level confidence rows and remaining gaps.
- Regenerate `artifact_manifest.json`.

---

### Task 1: Stage and verify the authorized Drive release

**Files:**
- Source: Google Drive `JISA-Final-2026-07-17/JISA_submission_package.zip`
- Source: Google Drive `JISA-Final-2026-07-17/Xie_JISA_manuscript.pdf`
- Source: Google Drive `JISA-Final-2026-07-17/run-manifests/*.json`
- Create: `tests/test_jisa_release_boundary.py`
- Create/import: final manuscript and package files listed in **File Structure**

**Interfaces:**
- Consumes: authorized Google Drive file IDs and the package's internal relative paths.
- Produces: a raw-data-free canonical JISA release tree used by all later tasks.

- [ ] **Step 1: Record source metadata and SHA-256 values before import**

Fetch the three authorized release sources through the Drive connector, save only the submission package, final manuscript, and run-manifest files to a temporary staging directory, and run:

```powershell
$staging = Join-Path $env:TEMP "jisa-source"
Get-FileHash (Join-Path $staging "JISA_submission_package.zip") -Algorithm SHA256
Get-FileHash (Join-Path $staging "Xie_JISA_manuscript.pdf") -Algorithm SHA256
```

Expected: both commands return one SHA-256 value; the package size is 756225 bytes and the Drive manuscript size is 405979 bytes.

- [ ] **Step 2: Write the failing release-boundary test**

Create `tests/test_jisa_release_boundary.py` with:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "paper_eatvul_defense_framework/latex_submission/main_jisa.tex",
    "paper_eatvul_defense_framework/latex_submission/main_jisa.pdf",
    "paper_eatvul_defense_framework/figures_submission_jisa/action_boundary.pdf",
    "results/jisa_evidence_bundle.json",
    "results/jisa_matched_budget_summary.csv",
    "results/jisa_confidence_sensitivity/confidence_adv_samples.csv",
    "manifests/jisa_final/FINAL_RUN_MANIFEST.json",
    "scripts/materialize_jisa_evidence.py",
]


def test_final_jisa_release_files_are_present() -> None:
    assert not [path for path in REQUIRED if not (ROOT / path).is_file()]


def test_private_archive_and_raw_splits_are_not_published() -> None:
    names = {path.name for path in ROOT.rglob("*") if ".git" not in path.parts}
    assert "Code and Dataset.zip" not in names
    assert not list(ROOT.glob("Code and Dataset/file/data/*_ast_*.json"))


def test_final_manuscript_is_the_three_rq_version() -> None:
    source = (ROOT / "paper_eatvul_defense_framework/latex_submission/main_jisa.tex").read_text(encoding="utf-8")
    assert "Evidence Boundaries of AST-Token-Only Defenses" in source
    assert all(f"RQ{number}" in source for number in range(1, 4))
    assert "RQ4" not in source
```

- [ ] **Step 3: Run the boundary test and verify it fails before import**

Run: `python -m pytest tests/test_jisa_release_boundary.py -v`

Expected: FAIL because `main_jisa.tex` and the final evidence files are not yet present.

- [ ] **Step 4: Import the allowlisted package files**

Extract `JISA_submission_package.zip` to temporary staging, copy the allowlisted files from **File Structure** into the repository with their package-relative paths, and copy the Drive manuscript only after confirming it is byte-identical to package `main_jisa.pdf` or documenting the difference. Copy the two Drive run manifests into `manifests/jisa_final/`. Do not copy `.pytest_cache/`, `__pycache__/`, the package archive, or `Code and Dataset.zip`.

- [ ] **Step 5: Run the boundary test and inspect the imported file list**

Run:

```powershell
python -m pytest tests/test_jisa_release_boundary.py -v
git status --short
git diff --check
```

Expected: 3 tests pass; the status lists only the allowlisted release files and the new test; `git diff --check` emits no errors.

- [ ] **Step 6: Commit the canonical release files**

```powershell
git add paper_eatvul_defense_framework results/jisa_* scripts/materialize_jisa_evidence.py scripts/jisa_confidence_sensitivity.py tests/test_jisa_release_boundary.py tests/test_materialize_jisa_evidence.py tests/test_jisa_confidence_sensitivity.py requirements_jisa.txt JISA_REVISION_NOTES.md manifests/jisa_final
git commit -m "feat: import final JISA release artifacts"
```

### Task 2: Validate evidence materialization and confidence controls

**Files:**
- Test: `tests/test_materialize_jisa_evidence.py`
- Test: `tests/test_jisa_confidence_sensitivity.py`
- Verify: `scripts/materialize_jisa_evidence.py`
- Verify: `scripts/jisa_confidence_sensitivity.py`
- Verify: `results/jisa_evidence_bundle.json`
- Verify: `results/jisa_confidence_sensitivity/*`

**Interfaces:**
- Consumes: imported evidence bundle, confidence sample rows, and deterministic tie policy.
- Produces: independently tested derived tables and figures for manuscript verification.

- [ ] **Step 1: Run the focused package tests**

Run:

```powershell
python -m pytest tests/test_jisa_confidence_sensitivity.py tests/test_materialize_jisa_evidence.py -v
```

Expected: 4 tests pass, including the exact-k tie policy, whitespace-normalized hashes, recomputation from sample rows, and the complete 100-row matched-budget grid.

- [ ] **Step 2: Run the supplied confidence verifier**

Run: `python scripts/jisa_confidence_sensitivity.py verify`

Expected: exit code 0 and a message confirming that the confidence outputs recompute from `confidence_adv_samples.csv`.

- [ ] **Step 3: Check materialization idempotence**

Run:

```powershell
git status --short
python scripts/materialize_jisa_evidence.py
git diff --exit-code -- paper_eatvul_defense_framework/latex_submission/generated paper_eatvul_defense_framework/figures_submission_jisa results/jisa_matched_budget_summary.csv
```

Expected: materialization exits 0 and the final diff command exits 0, proving that committed generated evidence is stable.

- [ ] **Step 4: Commit only if compatibility edits were required**

If the focused tests required repository-integration edits, stage only those edits and run:

```powershell
git add scripts/materialize_jisa_evidence.py scripts/jisa_confidence_sensitivity.py tests/test_materialize_jisa_evidence.py tests/test_jisa_confidence_sensitivity.py pyproject.toml
git commit -m "test: integrate JISA evidence verification"
```

Expected: a commit is created only when an integration change exists; otherwise leave Task 1's package files unchanged.

### Task 3: Replace stale reported-value and structure checks

**Files:**
- Modify: `scripts/check_reported_values.py`
- Modify: `scripts/check_artifact.py`
- Modify: `scripts/check_text_integrity.py`
- Modify: `tests/test_artifact_checks.py`

**Interfaces:**
- Consumes: final generated TeX fragments, final CSV/JSON evidence, and release manifests.
- Produces: deterministic validation output naming Tables 2--9 and rejecting stale or incomplete releases.

- [ ] **Step 1: Update the failing checker assertion**

Replace the reported-values assertion in `tests/test_artifact_checks.py` with:

```python
def test_reported_values_check_passes() -> None:
    result = run_script("scripts/check_reported_values.py")
    assert "Reported-value check passed" in result.stdout
    assert "Tables 2-9" in result.stdout
```

Run: `python -m pytest tests/test_artifact_checks.py::test_reported_values_check_passes -v`

Expected: FAIL because the current checker reports superseded Tables 4, 6, 7, 8, 9, 10, 11, and 15.

- [ ] **Step 2: Replace the old table map in the checker**

Implement `FINAL_TABLE_FRAGMENTS` in `scripts/check_reported_values.py` with the final package hashes:

```python
FINAL_TABLE_FRAGMENTS = {
    "Table 2": ("jisa_dataset_profile.tex", "20e19997b8088660206ce71be786c33a1e448cf036acc5354cff052cdaafa41e"),
    "Table 3": ("jisa_matched_budget_5.tex", "6077325b98242f69d9d2793ec4de8363943f5f48d168d1ec080f1818e35b4298"),
    "Table 4": ("jisa_confidence_baseline.tex", "4f6ed50cc2706b85f19e7657329d7a8c39739a2000c6bb339950a4c6ab79d865"),
    "Table 5": ("jisa_duplicate_sensitivity.tex", "d06494f247b46eae43c08b38c6066df91928a1e13f769ddb0b968b10aeb52546"),
    "Table 6": ("jisa_screening_stability.tex", "ba8f99560ab6842a0625d964f51d58d04d11f67a238dc2949ae487a1d041b8ad"),
    "Table 7": ("jisa_codebert_results.tex", "36f47e54d80b3c97c7b666b7fc010bc1cd0b845409d267d3e73b782a0c5c0c89"),
    "Table 8": ("jisa_token_length.tex", "5fb7a278eccadef0742680d2428f15545643fc143444008393117639e298624b"),
    "Table 9": ("jisa_deletion_sensitivity.tex", "db2478893c65d25dd8480cdd51045e3ea5e7283b53c834b6e3e42d1d7cd2c60f"),
}
```

For each entry, read from `paper_eatvul_defense_framework/latex_submission/generated/`, calculate SHA-256, and fail with the table number, expected hash, and actual hash on mismatch. Also load `results/jisa_evidence_bundle.json`, require `verified is True`, require 100 matched-budget rows through `matched_summary()`, and parse all four final confidence CSVs with pandas. Print exactly `Reported-value check passed: final Tables 2-9 match the verified JISA evidence.` on success.

- [ ] **Step 3: Make the artifact validator require the final release**

Add the required paths from `tests/test_jisa_release_boundary.py` to `scripts/check_artifact.py`, require the eight generated table fragments, and validate that `results/jisa_confidence_sensitivity/confidence_summary.csv` contains all datasets `{asterisk, openssl, cwe119, cwe399}` and budgets `{0.01, 0.03, 0.05, 0.10, 0.15}`.

- [ ] **Step 4: Extend text-integrity discovery if necessary**

Run `python scripts/check_text_integrity.py`. If final `.tex`, `.json`, and `.csv` files are already discovered, make no edit. Otherwise extend its existing suffix/path allowlists to include `manifests/`, `results/jisa_*`, and `paper_eatvul_defense_framework/latex_submission/generated/` without scanning `.git`, `.worktrees`, caches, or binary PDFs.

- [ ] **Step 5: Run all integration checks**

Run:

```powershell
python -m pytest tests/test_artifact_checks.py tests/test_jisa_release_boundary.py -v
python scripts/check_text_integrity.py
python scripts/check_artifact.py
python scripts/check_reported_values.py
```

Expected: all tests pass; each script exits 0; the reported-value checker names `Tables 2-9`.

- [ ] **Step 6: Commit the final validators**

```powershell
git add scripts/check_reported_values.py scripts/check_artifact.py scripts/check_text_integrity.py tests/test_artifact_checks.py
git commit -m "test: validate final JISA evidence tables"
```

### Task 4: Reconcile public documentation and citation metadata

**Files:**
- Modify: `README.md`
- Modify: `ARTIFACT.md`
- Modify: `DATA.md`
- Modify: `REPRODUCIBILITY.md`
- Modify: `SUBMISSION_JISA.md`
- Modify: `CITATION.cff`
- Modify: `docs/TABLE_REPRODUCTION_MAP.md`
- Modify: `docs/ARTIFACT_INVENTORY.md`
- Modify: `docs/RUNBOOK.md`
- Modify: `docs/LIMITATIONS_FOR_REVIEWERS.md`
- Modify: `results/per_sample/README.md`

**Interfaces:**
- Consumes: final manuscript terminology, final paths, verified evidence, and the publication boundary.
- Produces: one consistent reviewer-facing description of the final artifact.

- [ ] **Step 1: Rewrite the repository entry points around the final manuscript**

Use the exact title `Evidence Boundaries of AST-Token-Only Defenses against EaTVul-Style Insertion Evasion`. State that the final study has three research questions, that screening/review routing is supported, and that label correction, localization, and automatic sanitization are outside the evidence boundary. Point the quick path to:

```powershell
python -m pytest tests/test_jisa_confidence_sensitivity.py tests/test_materialize_jisa_evidence.py tests/test_artifact_checks.py -v
python scripts/jisa_confidence_sensitivity.py verify
python scripts/materialize_jisa_evidence.py
python scripts/check_reported_values.py
```

- [ ] **Step 2: Document the final data boundary and provenance**

In `DATA.md`, `ARTIFACT.md`, and the limitations/inventory files, distinguish:

- public derived evidence in `results/jisa_*`;
- public run provenance in `manifests/jisa_final/` and `results/jisa_confidence_sensitivity/run_manifest.json`;
- non-public raw AST-token splits and `Code and Dataset.zip`;
- the incomplete historical backup limitation recorded in `JISA_REVISION_NOTES.md`.

- [ ] **Step 3: Replace the table reproduction map**

Map the final items exactly:

| Item | Canonical generated file |
| --- | --- |
| Table 2 | `generated/jisa_dataset_profile.tex` |
| Table 3 | `generated/jisa_matched_budget_5.tex` |
| Table 4 | `generated/jisa_confidence_baseline.tex` |
| Table 5 | `generated/jisa_duplicate_sensitivity.tex` |
| Table 6 | `generated/jisa_screening_stability.tex` |
| Table 7 | `generated/jisa_codebert_results.tex` |
| Table 8 | `generated/jisa_token_length.tex` |
| Table 9 | `generated/jisa_deletion_sensitivity.tex` |
| Figures 2--3 | `figures_submission_jisa/capture_vs_review.pdf`, `residual_vs_review.pdf` |

Also map Figure 1 to `figures_submission_jisa/action_boundary.pdf` and name each backing CSV/JSON source and materialization command.

- [ ] **Step 4: Update submission and citation metadata**

Set `CITATION.cff` title to the final title, version to `1.0-jisa-final`, and release date to `2026-07-17`. Update `SUBMISSION_JISA.md` so the canonical source/PDF are `main_jisa.tex` and `main_jisa.pdf`, the template is Elsevier CAS double-column, figures come from `figures_submission_jisa/`, and generated tables come from `latex_submission/generated/`.

- [ ] **Step 5: Scan for stale canonical claims**

Run:

```powershell
rg -n "Detection, Not Sanitization|RQ4|RQ5|RQ6|main_usenix_style_round3_clean|Table 10|Table 11|Table 15|calib_fpr_0\.1" README.md ARTIFACT.md DATA.md REPRODUCIBILITY.md SUBMISSION_JISA.md CITATION.cff docs results/per_sample/README.md
```

Expected: no stale claim remains in a canonical description; any retained historical mention is explicitly labeled historical and does not appear in the quick path or final table map.

- [ ] **Step 6: Run documentation-linked checks and commit**

```powershell
python scripts/check_text_integrity.py
python scripts/check_artifact.py
python scripts/check_reported_values.py
git diff --check
git add README.md ARTIFACT.md DATA.md REPRODUCIBILITY.md SUBMISSION_JISA.md CITATION.cff docs results/per_sample/README.md JISA_REVISION_NOTES.md
git commit -m "docs: align artifact with final JISA manuscript"
```

Expected: checks exit 0 and the documentation commit contains no raw data or generated cache files.

### Task 5: Regenerate provenance, verify the manuscript, and update GitHub

**Files:**
- Modify: `artifact_manifest.json`
- Verify: `paper_eatvul_defense_framework/latex_submission/main_jisa.tex`
- Verify: `paper_eatvul_defense_framework/latex_submission/main_jisa.pdf`
- Update externally: GitHub draft pull request #1

**Interfaces:**
- Consumes: the completed repository overlay and every validation result.
- Produces: a clean pushed branch and an accurate reviewer-ready draft pull request.

- [ ] **Step 1: Regenerate and verify the artifact manifest**

Run:

```powershell
python scripts/build_manifest.py
python scripts/check_artifact.py
git diff --check
```

Expected: `artifact_manifest.json` changes to include the final JISA files and excludes `.git`, `.worktrees`, caches, temporary staging, and private/raw data.

- [ ] **Step 2: Run the full automated validation suite**

Run:

```powershell
python -m pytest -v
python -m compileall scripts
python scripts/check_text_integrity.py
python scripts/check_artifact.py
python scripts/check_reported_values.py
python scripts/jisa_confidence_sensitivity.py verify
python scripts/materialize_jisa_evidence.py
git diff --exit-code -- paper_eatvul_defense_framework/latex_submission/generated paper_eatvul_defense_framework/figures_submission_jisa results/jisa_matched_budget_summary.csv
```

Expected: pytest passes, all scripts exit 0, compileall reports no syntax error, and materialization leaves no diff.

- [ ] **Step 3: Compile or verify the final manuscript**

From `paper_eatvul_defense_framework/latex_submission/`, run:

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error main_jisa.tex
```

Expected when TeX Live is available: exit 0, ten-page `main_jisa.pdf`, and no undefined citations or references. If `latexmk` is unavailable, record that fact, compare the tracked PDF hash with the Drive final PDF, render all ten pages, and visually inspect title, tables, figures, references, clipping, and blank pages.

- [ ] **Step 4: Perform the publication-boundary scan**

Run:

```powershell
git status --short --untracked-files=all
git ls-files | rg "Code and Dataset|__pycache__|\.pytest_cache|\.zip$|_ast_.*\.json$"
$pathPattern = "[A-Za-z]:" + "\x5c"
$credentialPattern = @(("gh" + "p_"), ("github" + "_pat_"), ("AI" + "za")) -join "|"
rg -n -P "$pathPattern|$credentialPattern" --glob "!*.pdf" --glob "!artifact_manifest.json" .
```

Expected: no tracked private archive, raw split, cache, credential, or machine-local path. Review any match rather than suppressing it.

- [ ] **Step 5: Commit the regenerated manifest and final corrections**

```powershell
git add artifact_manifest.json
git commit -m "chore: finalize JISA artifact manifest"
git status --short --branch
```

Expected: the worktree is clean and the branch is ahead of `artifact-origin/codex/sync-google-drive-20260717` by the new synchronization commits.

- [ ] **Step 6: Push the branch and update draft pull request #1**

Use an authenticated GitHub CLI session, then run:

Create `$env:TEMP\jisa-pr-body.md` with this reviewed body, changing a validation line only when the recorded command output requires an accurate qualification:

```markdown
## Summary

- synchronize the final JISA manuscript PDF, Elsevier CAS TeX, generated Tables 2--9, and submission figures from the authorized Google Drive release
- publish the final derived evidence, confidence-sensitivity rows, run manifests, reproduction scripts, and focused tests
- align artifact documentation, citation metadata, table mapping, and validators with the final three-RQ manuscript

## Data boundary

- does not publish `Code and Dataset.zip`
- does not publish raw AST-token dataset splits, model caches, credentials, or machine-local build files
- retains aggregate and sample-level derived evidence required to audit the reported results

## Validation

- full pytest suite passes
- final confidence outputs recompute from the released sample rows
- evidence materialization is idempotent
- final Tables 2--9 match the verified generated fragments
- artifact structure, text integrity, Python compilation, provenance manifest, and publication-boundary scans pass
- final ten-page manuscript PDF matches the authorized Drive release and passes visual inspection

This pull request remains draft for author review and does not merge into `main`.
```

```powershell
$prBody = Join-Path $env:TEMP "jisa-pr-body.md"
git push artifact-origin codex/sync-google-drive-20260717
gh pr edit 1 --repo xk-05/eatvul-jisa-artifact --title "Sync final JISA manuscript and reproducibility evidence" --body-file $prBody
gh pr view 1 --repo xk-05/eatvul-jisa-artifact --json url,title,isDraft,headRefName,files,commits
```

The reviewed PR body must enumerate the final manuscript/TeX, derived outputs, manifests, scripts/tests, documentation changes, explicit exclusion of `Code and Dataset.zip` and raw AST-token data, and the exact validation results from Steps 2--4.

Expected: push succeeds; PR #1 remains draft; its head is `codex/sync-google-drive-20260717`; its title and description reflect the full final JISA synchronization.
