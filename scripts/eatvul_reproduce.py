import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Code and Dataset" / "file" / "data"
MODEL_DIR = ROOT / "models" / "codebert-base"
CODE_DIR = ROOT / "model" / "model"
DEFAULT_OUT = CODE_DIR / "saved_newbap_models"

DATASETS = {
    "asterisk": {
        "train": DATA_DIR / "asterisk_ast_train.json",
        "test": DATA_DIR / "asterisk_ast_test.json",
        "adv": DATA_DIR / "asterisk_ast_test_ADV.json",
    },
    "openssl": {
        "train": DATA_DIR / "openssl_ast_train.json",
        "test": DATA_DIR / "openssl_ast_test.json",
        "adv": DATA_DIR / "openssl_ast_test_ADV.json",
    },
    "cwe119": {
        "train": DATA_DIR / "cwe119_ast_train.json",
        "test": DATA_DIR / "cwe119_ast_test.json",
        "adv": DATA_DIR / "cwe119_ast_test_ADV.json",
    },
    "cwe399": {
        "train": DATA_DIR / "cwe399_ast_train.json",
        "test": DATA_DIR / "cwe399_ast_test.json",
        "adv": DATA_DIR / "cwe399_ast_test_ADV.json",
    },
}


def iter_jsonl(path):
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def label_counts(path):
    counts = {}
    total = 0
    for item in iter_jsonl(path):
        label = item.get("target")
        counts[label] = counts.get(label, 0) + 1
        total += 1
    return total, counts


def dataset_summary(_args):
    print("dataset,split,total,label_0,label_1")
    for name, paths in DATASETS.items():
        for split, path in paths.items():
            total, counts = label_counts(path)
            print(f"{name},{split},{total},{counts.get(0, 0)},{counts.get(1, 0)}")


def make_smoke(args):
    dataset = DATASETS[args.dataset]
    out_dir = ROOT / "smoke_data" / args.dataset
    out_dir.mkdir(parents=True, exist_ok=True)
    for split in ["train", "test", "adv"]:
        out_file = out_dir / f"{split}.json"
        with dataset[split].open(encoding="utf-8") as src, out_file.open("w", encoding="utf-8") as dst:
            for idx, line in enumerate(src):
                if idx >= args.rows:
                    break
                dst.write(line)
    print(out_dir)


def conda_python():
    return ["conda", "run", "-n", "eatvul", "python"]


def ori_model_base(output_dir, train_file, eval_file, test_file, args):
    return [
        *conda_python(),
        "ori_model_run.py",
        "--output_dir",
        str(output_dir),
        "--model_type",
        "roberta",
        "--tokenizer_name",
        str(MODEL_DIR),
        "--model_name_or_path",
        str(MODEL_DIR),
        "--train_data_file",
        str(train_file),
        "--eval_data_file",
        str(eval_file),
        "--test_data_file",
        str(test_file),
        "--block_size",
        str(args.block_size),
        "--train_batch_size",
        str(args.train_batch_size),
        "--eval_batch_size",
        str(args.eval_batch_size),
        "--no_cuda",
    ]


def selected_paths(args):
    paths = DATASETS[args.dataset]
    if getattr(args, "smoke", False):
        smoke_dir = ROOT / "smoke_data" / args.dataset
        return {
            "train": smoke_dir / "train.json",
            "test": smoke_dir / "test.json",
            "adv": smoke_dir / "adv.json",
        }
    return paths


def run_command(cmd):
    print(" ".join(f'"{x}"' if " " in x else x for x in cmd))
    subprocess.run(cmd, cwd=str(CODE_DIR), check=True)


def train_codebert(args):
    paths = selected_paths(args)
    out = DEFAULT_OUT / args.run_name
    cmd = ori_model_base(out, paths["train"], paths["test"], paths["test"], args)
    cmd.extend(
        [
            "--do_train",
            "--epoch",
            str(args.epoch),
            "--logging_steps",
            str(args.logging_steps),
            "--save_steps",
            str(args.save_steps),
        ]
    )
    if args.evaluate_during_training:
        cmd.append("--evaluate_during_training")
    run_command(cmd)


def test_codebert(args):
    paths = selected_paths(args)
    test_file = paths["adv"] if args.adv else paths["test"]
    out = DEFAULT_OUT / args.run_name
    cmd = ori_model_base(out, paths["train"], paths["test"], test_file, args)
    cmd.append("--do_test")
    run_command(cmd)


def asr(args):
    preds = {}
    for line in Path(args.predictions).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        idx, pred = line.split("\t")
        preds[int(idx)] = int(pred)

    total = 0
    bypass = 0
    missing = 0
    for item in iter_jsonl(args.adv_file):
        if item.get("target") != 1:
            continue
        total += 1
        pred = preds.get(int(item["idx"]))
        if pred is None:
            missing += 1
        elif pred == 0:
            bypass += 1

    rate = bypass / total if total else 0.0
    print(json.dumps({"total_vulnerable": total, "bypassed": bypass, "missing_predictions": missing, "asr": rate}, indent=2))


def show_plan(_args):
    print(
        "\n".join(
            [
                "EaTVul reproduction stages:",
                "1. Train/load target detector: CodeBERT via model/model/ori_model_run.py.",
                "2. Surrogate stage: BiLSTM+attention scripts exist, but the released script still requires real CSV/token paths.",
                "3. Attack pool: use released *_ADV.json files as the preserved adversarial sets, or replace with ChatGPT-generated snippets.",
                "4. Seed selection: Code and Dataset/file/code/fga_selection.py implements the paper fitness/FGA helpers.",
                "5. Evasion attack: run target detector on *_ADV.json.",
                "6. Metrics: ASR = vulnerable samples predicted as non-vulnerable / vulnerable samples.",
            ]
        )
    )


def main():
    parser = argparse.ArgumentParser(description="EaTVul reproduction helper")
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("plan")
    p.set_defaults(func=show_plan)

    p = sub.add_parser("dataset-summary")
    p.set_defaults(func=dataset_summary)

    p = sub.add_parser("make-smoke")
    p.add_argument("--dataset", choices=DATASETS.keys(), default="openssl")
    p.add_argument("--rows", type=int, default=8)
    p.set_defaults(func=make_smoke)

    def add_model_args(p):
        p.add_argument("--dataset", choices=DATASETS.keys(), default="openssl")
        p.add_argument("--run-name", default="openssl_codebert")
        p.add_argument("--smoke", action="store_true", help="Use smoke_data/<dataset> generated by make-smoke.")
        p.add_argument("--block-size", type=int, default=400)
        p.add_argument("--train-batch-size", type=int, default=1)
        p.add_argument("--eval-batch-size", type=int, default=1)

    p = sub.add_parser("train-codebert")
    add_model_args(p)
    p.add_argument("--epoch", type=int, default=10)
    p.add_argument("--logging-steps", type=int, default=50)
    p.add_argument("--save-steps", type=int, default=50)
    p.add_argument("--evaluate-during-training", action="store_true")
    p.set_defaults(func=train_codebert)

    p = sub.add_parser("test-codebert")
    add_model_args(p)
    p.add_argument("--adv", action="store_true")
    p.set_defaults(func=test_codebert)

    p = sub.add_parser("asr")
    p.add_argument("--predictions", required=True)
    p.add_argument("--adv-file", required=True)
    p.set_defaults(func=asr)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
