# EaTVul Reproduction Notes

This repository contains a partial release of the USENIX Security 2024 paper:
EaTVul: ChatGPT-based Evasion Attack Against Software Vulnerability Detection.

The paper pipeline has two phases:

1. Adversarial data generation
   - train a surrogate BiLSTM + attention model
   - use SVM support vectors to find important non-vulnerable samples
   - use attention weights to find important tokens/features
   - prompt ChatGPT to generate and optimize dead-code adversarial snippets
   - filter snippets and build a preserved attack pool
2. Adversarial learning / evasion
   - use FGA to select adversarial snippets from the pool
   - insert snippets into vulnerable samples
   - query a target vulnerability detector
   - compute ASR: vulnerable samples predicted as non-vulnerable / vulnerable samples

## What Is Runnable Here

The released repository includes:

- AST datasets and released adversarial datasets:
  - `Code and Dataset/file/data/*_ast_train.json`
  - `Code and Dataset/file/data/*_ast_test.json`
  - `Code and Dataset/file/data/*_ast_test_ADV.json`
- CodeBERT target-model training/evaluation:
  - `model/model/ori_model_run.py`
  - `model/model/ori_model.py`
- FGA helper functions:
  - `Code and Dataset/file/code/fga_selection.py`
- ChatGPT prompt helper:
  - `Code and Dataset/file/code/adversarial_code_generation.py`
- Surrogate-model scripts:
  - `model/model/surrogate_train.py`
  - `model/model/surrogate_test.py`
  - `model/model/sur_model.py`

The following paper components are not fully released as directly runnable artifacts:

- complete preserved attack pool before final `*_ADV.json` files
- target checkpoints for all baselines in the paper
- Comex-based snippet filtering workflow
- real CSV/token paths required by `surrogate_train.py`
- full baseline implementations for AST-EVD, Asteria, LineVul, Poster-Lin, MDVD, CodeGen, FUNDED, and VDet

Therefore this workspace focuses on a reproducible core loop:

`target detector -> released adversarial set -> predictions -> ASR`

## Environment

Use the existing Conda environment:

```powershell
conda run -n eatvul python --version
```

Expected:

```text
Python 3.7.16
```

The local CodeBERT files are stored in:

```text
models/codebert-base
```

## Reproduction Helper

Use:

```powershell
python scripts\eatvul_reproduce.py plan
python scripts\eatvul_reproduce.py dataset-summary
```

Generate a small smoke dataset:

```powershell
python scripts\eatvul_reproduce.py make-smoke --dataset openssl --rows 4
```

Run a smoke target-model training pass:

```powershell
python scripts\eatvul_reproduce.py train-codebert --dataset openssl --smoke --run-name repro_smoke --epoch 1 --logging-steps 1 --save-steps 1 --train-batch-size 1 --eval-batch-size 1
```

Run evasion evaluation on the released adversarial samples:

```powershell
python scripts\eatvul_reproduce.py test-codebert --dataset openssl --smoke --run-name repro_smoke --adv --eval-batch-size 1
```

Compute ASR:

```powershell
python scripts\eatvul_reproduce.py asr --predictions "model\model\saved_newbap_models\repro_smoke\predictions.txt" --adv-file "smoke_data\openssl\adv.json"
```

The smoke run is only a pipeline check, not a paper-number reproduction.

## Full Dataset Run

On this machine CUDA is not available, so full CodeBERT training is CPU-only and slow.

Example for OpenSSL:

```powershell
python scripts\eatvul_reproduce.py train-codebert --dataset openssl --run-name openssl_codebert --epoch 10 --train-batch-size 1 --eval-batch-size 1 --save-steps 50 --logging-steps 50
python scripts\eatvul_reproduce.py test-codebert --dataset openssl --run-name openssl_codebert --adv --eval-batch-size 1
python scripts\eatvul_reproduce.py asr --predictions "model\model\saved_newbap_models\openssl_codebert\predictions.txt" --adv-file "Code and Dataset\file\data\openssl_ast_test_ADV.json"
```

For paper-scale results, repeat for:

- `asterisk`
- `openssl`
- `cwe119`
- `cwe399`

## Paper-to-Code Map

| Paper stage | Local file/status |
| --- | --- |
| SVM important sample identification | `get_support_vector_idx` in `model/model/ori_model_run.py` |
| BiLSTM + attention surrogate | `model/model/sur_model.py`, `surrogate_train.py`, `surrogate_test.py` |
| Key-token extraction | `model/model/key_token_capture.py` |
| ChatGPT snippet generation | `Code and Dataset/file/code/adversarial_code_generation.py` |
| Preserved attack pool | Not released directly; final `*_ADV.json` files are released |
| FGA seed selection | `Code and Dataset/file/code/fga_selection.py` |
| Evasion attack | run target detector on `*_ADV.json` |
| ASR metric | `scripts/eatvul_reproduce.py asr` |

## Important Caveats

The paper reports attack results against multiple victim models. This repo does not include runnable versions or checkpoints for all those victim models, so exact Table 5-8 reproduction requires collecting or rebuilding those baselines separately.

`surrogate_train.py` still contains placeholder data paths (`PATH of the FILE`). It now imports under TensorFlow/Keras 2.10, but it needs the real CSV/token files used by the authors before it can train the surrogate model.
