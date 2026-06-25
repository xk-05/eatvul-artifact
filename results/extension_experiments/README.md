# EaTVul Extension Experiments

This folder stores LineVul Big-Vul source-level extension experiment outputs.

## Data

The project JSONL files are prepared from LineVul's Big-Vul function-level CSV:

```powershell
python scripts\prepare_linevul_extension_data.py `
  --csv data\linevul_bigvul\test.csv `
  --projects chrome linux android tcpdump php-src imagemagick ffmpeg `
  --out-dir data\extension_projects `
  --train-frac 0.70
```

Current summary:

- Chrome: 7,670 functions, 5,368 train, 2,302 clean test, 106 vulnerable test seeds.
- Linux: 4,769 functions, 3,338 train, 1,431 clean test, 64 vulnerable test seeds.
- Android: 858 functions, 599 train, 259 clean test, 38 vulnerable test seeds.
- php-src: 152 functions, 105 train, 47 clean test, 9 vulnerable test seeds.
- tcpdump: 87 functions, 60 train, 27 clean test, 9 vulnerable test seeds.
- ImageMagick: 295 functions, 206 train, 89 clean test, 7 vulnerable test seeds.
- FFmpeg: 185 functions, 129 train, 56 clean test, 4 vulnerable test seeds.

FFmpeg, ImageMagick, tcpdump, and php-src are reported as small-case stress
checks, not as broad generalization evidence. Each JSONL row includes `idx`,
`project`, `func`, `target`, `split`, and source metadata where available.

## Runs

Dataset summary:

```powershell
python scripts\eatvul_extension_experiments.py dataset-summary `
  --datasets chrome linux android tcpdump php-src imagemagick ffmpeg `
  --output-dir results\extension_experiments\multi_project_summary
```

Source-level generator validation:

```powershell
python scripts\eatvul_extension_experiments.py validate-adaptive `
  --datasets chrome linux android tcpdump php-src imagemagick ffmpeg `
  --attack dead_branch guarded_noop `
  --limit-adv 10 `
  --output-dir results\extension_experiments\multi_project_validation
```

Full TF-IDF extension rows:

```powershell
python scripts\eatvul_extension_experiments.py run `
  --datasets chrome linux android tcpdump php-src imagemagick ffmpeg `
  --victims tfidf `
  --attack original dead_branch guarded_noop `
  --max-train 800 `
  --output-dir results\extension_experiments\multi_project_tfidf
```

The `dead_branch` and `guarded_noop` generators insert conservative source-level
snippets and record insertion spans, parser status, compiler state, and
validation status in `insertion_meta`. If no local C compiler is available, rows
are marked `compiler_unavailable` and are not counted as compiler-validated.

## Hugging Face / Transformer Rows

GraphCodeBERT model files were downloaded into `models/graphcodebert-base` with:

```powershell
python scripts\download_hf_model_files.py `
  --repo microsoft/graphcodebert-base `
  --out-dir models\graphcodebert-base
```

Official LineVul checkpoint rows retained in `official_linevul` use the public
12-head checkpoint on the earlier Linux/FFmpeg adaptive CSVs. The summarizer now
also propagates `validated_adv_n` from gate prediction logs:

```powershell
python scripts\summarize_official_linevul.py `
  --prediction-dir results\extension_experiments\official_linevul\predictions `
  --gate-dir results\extension_experiments\multi_project_tfidf\predictions `
  --out-csv results\extension_experiments\official_linevul\official_linevul_results.csv
```

Run official checkpoint inference before using that summarizer for new projects
or new attacks, because it expects matching `*_raw_preds.csv` files.

## Interpretation

The TF-IDF rows are the full multi-project source-level baseline. They broaden
external-validity inspection but show modest protection, not broad robustness.
The official LineVul rows are checkpoint-based stress checks where raw
predictions already exist. The GraphCodeBERT-style rows are CPU smoke-scale
checks with newly initialized classification heads; they prove that the runner
executes on real project splits, but they are not optimized GraphCodeBERT
vulnerability-detector benchmarks.
