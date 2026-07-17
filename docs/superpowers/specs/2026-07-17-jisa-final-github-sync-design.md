# JISA Final Google Drive to GitHub Sync Design

Date: 2026-07-17

## Objective

Synchronize the final JISA submission artifacts from the Google Drive folder
`JISA-Final-2026-07-17` into the public GitHub artifact repository while keeping
the repository reproducible, reviewable, and within the paper's stated data
availability boundary.

The synchronization will update the existing branch
`codex/sync-google-drive-20260717` and draft pull request #1. It will not publish
`Code and Dataset.zip` or any raw AST-token dataset.

## Source of Truth

The authoritative source is the Google Drive folder:

- `JISA-Final-2026-07-17`
- Final manuscript: `Xie_JISA_manuscript.pdf`
- Submission package: `JISA_submission_package.zip`
- Authoring source: `manuscript-tex/`
- Final derived evidence: `experiment-outputs/`
- Provenance and environment records: `run-manifests/`

Where the current repository conflicts with these files, the final Drive
package takes precedence. Hashes recorded in the final manifests and hashes of
the Drive files will be used to detect incomplete or accidental changes.

## Chosen Approach

Use a non-destructive overlay. Final JISA artifacts become canonical at their
normal repository locations, while older files that remain useful and do not
contradict the final paper are retained. Stale documentation, generated tables,
figures, checks, and claims will be revised rather than kept as competing
canonical versions.

This approach preserves useful history and supporting material without placing
the final release in a confusing nested subdirectory or deleting the repository
wholesale.

## Publication Boundary

The public repository will include:

- final manuscript PDF and TeX sources;
- bibliography, highlights, cover letter, and declaration drafts when present
  in the final submission package;
- final aggregate and derived experiment outputs used by the paper;
- run manifests, dependency pins, hashes, and environment metadata;
- reproduction and evidence-materialization scripts;
- tests needed to validate the released evidence;
- updated artifact, data, submission, citation, and reproduction documentation.

The public repository will exclude:

- `Code and Dataset.zip`;
- raw AST-token samples and any dataset material excluded by the manuscript's
  data-availability statement;
- credentials, machine-local paths, caches, `__pycache__`, `.pytest_cache`, TeX
  build intermediates, and other temporary files;
- duplicate archives when their extracted, reviewable contents are committed.

The repository documentation will explicitly distinguish public derived
evidence from non-public raw data.

## Repository Mapping

The final package's existing internal layout will be preserved when it already
matches the repository. Otherwise, artifacts will be mapped as follows:

- manuscript PDF, `main_jisa.tex`, bibliography, generated table fragments,
  and paper figures: `paper_eatvul_defense_framework/latex_submission/`;
- final aggregate CSV and JSON evidence: a clearly identified final-results
  location under `results/`, with links from the reproduction map;
- run manifests and dependency metadata: a clearly identified final-manifest
  location under the repository, retaining their original filenames;
- reproduction/materialization scripts: `scripts/`;
- validation tests: `tests/`.

Exact destinations will favor paths referenced by the final package's scripts
and tests so that unnecessary path rewrites are avoided.

## Documentation Changes

The following public entry points will be reconciled with the final paper:

- `README.md`
- `ARTIFACT.md`
- `DATA.md`
- `REPRODUCIBILITY.md`
- `SUBMISSION_JISA.md`
- `CITATION.cff`
- `docs/TABLE_REPRODUCTION_MAP.md`
- `results/per_sample/README.md`

They will describe the final three research questions, the released evidence,
the non-public data boundary, exact reproduction commands, and the relationship
between Tables 2--9 and their backing outputs. References to the superseded
six-RQ manuscript or old table numbering will be removed or clearly labeled as
historical where retention is useful.

## Validation Design

Validation will be evidence-driven and will cover:

1. **Source integrity:** compare imported files with Drive/package hashes and
   check the final PDF identity.
2. **Data boundary:** scan the staged change for `Code and Dataset.zip`, raw
   data, secrets, caches, and machine-local paths.
3. **Reported values:** revise the repository checker to validate the final
   paper's Tables 2--9 against released CSV/JSON/generated TeX evidence.
4. **Automated tests:** run the final package tests and the compatible existing
   test suite.
5. **Evidence materialization:** run the supplied materialization workflow and
   confirm that generated artifacts are stable or that differences are
   explained.
6. **Manuscript verification:** compile the final TeX when the available runtime
   supports it; in all cases, verify and render the supplied final PDF for a
   visual smoke check.
7. **Repository review:** inspect the final diff, regenerated artifact manifest,
   documentation links, and Git working-tree state before publication.

If a validation cannot run because of an unavailable optional runtime, the pull
request will state that limitation and provide the strongest available
substitute evidence. A failing check will be fixed or documented before push;
it will not be silently ignored.

## GitHub Delivery

Implementation will be committed in coherent units on
`codex/sync-google-drive-20260717`, pushed to the existing remote branch, and
added to draft pull request #1. The pull request title and description will be
updated from the initial housekeeping-only scope to the complete final JISA
artifact synchronization, including:

- included artifact classes;
- explicit exclusions and data boundary;
- validation commands and results;
- any remaining reproducibility limitations.

No merge to `main` is part of this operation.

## Acceptance Criteria

The synchronization is complete when:

- GitHub contains the final manuscript-facing artifacts from Drive;
- the public repository does not contain `Code and Dataset.zip` or prohibited
  raw data;
- repository documentation and citation metadata match the final manuscript;
- the table reproduction map and reported-value checks match Tables 2--9;
- manifests and hashes provide traceable provenance;
- relevant tests and validation checks pass, or any unavoidable environmental
  limitation is disclosed in the pull request;
- the existing draft pull request accurately summarizes the final change and is
  ready for human review.
