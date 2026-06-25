import argparse
import csv
import json
import random
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline

from eatvul_defense import (
    ROOT,
    BackgroundStats,
    detector_predict,
    texts_labels,
    train_detector,
)


OUT_DIR = ROOT / "results" / "extension_experiments"
EXT_DATA_DIR = ROOT / "data" / "extension_projects"
DEFAULT_PROJECTS = ["chrome", "linux", "android", "tcpdump", "php-src", "imagemagick", "ffmpeg"]

AST_MARKERS = {
    "FUNCTION_DEF",
    "SIMPLE_DECL",
    "VAR_DECL",
    "EXPR_STATEMENT",
    "SELECTION",
    "ITERATION",
    "JUMP_STATEMENT",
    "FUNCTION_CALL",
    "PARAMETER_DECL",
    "RETURN_TYPE",
    "TYPE_NAME",
    "LEAF_NODE",
}


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)


def iter_jsonl(path):
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def save_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_item(item, project, split, idx):
    func = item.get("func") or item.get("function") or item.get("code") or item.get("before") or ""
    target = item.get("target", item.get("label", item.get("vul", 0)))
    normalized = {
        "idx": int(item.get("idx", idx)),
        "project": item.get("project", project),
        "func": str(func),
        "target": int(target),
        "split": item.get("split", split),
    }
    for key in ["source_path", "commit", "cve", "insertion_meta", "data_source"]:
        if key in item:
            normalized[key] = item[key]
    return normalized


def external_paths(project):
    base = EXT_DATA_DIR / project
    return {
        "train": base / "train.jsonl",
        "test": base / "test.jsonl",
        "adv": base / "adv.jsonl",
    }


def load_project_split(project, split, limit=None):
    paths = external_paths(project)
    if all(path.exists() for path in paths.values()):
        source = "external_project_jsonl"
        rows = [normalize_item(item, project, split, idx) for idx, item in enumerate(iter_jsonl(paths[split]))]
    else:
        expected = ", ".join(str(path) for path in paths.values())
        raise FileNotFoundError(f"No source-level extension data found for {project}: expected {expected}")
    if limit is not None:
        rows = rows[:limit]
    for row in rows:
        row["data_source"] = source
    return rows, source


def balanced_subset(items, max_train, seed):
    if max_train is None or len(items) <= max_train:
        return list(items)
    rng = random.Random(seed)
    by_label = {0: [], 1: []}
    for item in items:
        by_label[int(item["target"])].append(item)
    per_class = max(1, max_train // 2)
    chosen = []
    for label in [0, 1]:
        values = list(by_label[label])
        rng.shuffle(values)
        chosen.extend(values[:per_class])
    if len(chosen) < max_train:
        remaining = [item for item in items if item not in chosen]
        rng.shuffle(remaining)
        chosen.extend(remaining[: max_train - len(chosen)])
    rng.shuffle(chosen)
    return chosen


def train_tfidf_victim(train_items):
    texts, labels = texts_labels(train_items)
    model = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    tokenizer=str.split,
                    preprocessor=None,
                    token_pattern=None,
                    ngram_range=(1, 2),
                    min_df=1,
                    max_features=50000,
                    sublinear_tf=True,
                ),
            ),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", n_jobs=1)),
        ]
    )
    model.fit(texts, labels)
    return model


def train_transformer_victim(train_items, args, model_kind):
    import torch
    from torch.utils.data import DataLoader, Dataset
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    model_name = args.linevul_model if model_kind == "linevul" else args.graphcodebert_model
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=args.local_files_only)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=2,
        local_files_only=args.local_files_only,
    )
    device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
    model.to(device)
    torch.manual_seed(args.seed)

    class CodeDataset(Dataset):
        def __init__(self, rows):
            self.rows = rows

        def __len__(self):
            return len(self.rows)

        def __getitem__(self, idx):
            row = self.rows[idx]
            enc = tokenizer(
                row["func"],
                max_length=args.max_len,
                truncation=True,
                padding="max_length",
                return_tensors="pt",
            )
            return {
                "input_ids": enc["input_ids"].squeeze(0),
                "attention_mask": enc["attention_mask"].squeeze(0),
                "labels": torch.tensor(int(row["target"]), dtype=torch.long),
            }

    loader = DataLoader(CodeDataset(train_items), batch_size=args.batch_size, shuffle=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    model.train()
    for _epoch in range(args.epochs):
        for batch in loader:
            optimizer.zero_grad()
            batch = {key: value.to(device) for key, value in batch.items()}
            loss = model(**batch).loss
            loss.backward()
            optimizer.step()

    def predict(rows):
        pred_loader = DataLoader(CodeDataset(rows), batch_size=args.batch_size, shuffle=False)
        preds = []
        probs = []
        model.eval()
        with torch.no_grad():
            for batch in pred_loader:
                batch.pop("labels")
                batch = {key: value.to(device) for key, value in batch.items()}
                logits = model(**batch).logits
                softmax = torch.softmax(logits, dim=1)
                probs.extend(softmax[:, 1].cpu().numpy().tolist())
                preds.extend(torch.argmax(logits, dim=1).cpu().numpy().tolist())
        return np.asarray(preds, dtype=int), np.asarray(probs, dtype=float)

    return predict


def train_gate_for_project(project, target_clean_items, args):
    gate_train_items = []
    gate_adv_items = []
    gate_sources = []
    for other in args.datasets:
        if other == project:
            continue
        other_clean, clean_source = load_project_split(other, "test", args.limit_test)
        other_adv, adv_source = load_project_split(other, "adv", args.limit_adv)
        gate_train_items.extend(other_clean)
        gate_adv_items.extend(other_adv)
        gate_sources.append(f"{other}:{clean_source}/{adv_source}")
    if not gate_train_items or not gate_adv_items:
        gate_train_items, clean_source = load_project_split(project, "train", args.limit_train)
        gate_adv_items, adv_source = load_project_split(project, "adv", args.limit_adv)
        gate_sources.append(f"{project}:{clean_source}/{adv_source}:fallback")

    background = BackgroundStats([item["func"] for item in gate_train_items])
    gate = train_detector(gate_train_items, gate_adv_items, background)
    clean_texts, clean_y = texts_labels(target_clean_items)
    clean_scores, _ = detector_predict(gate, clean_texts, background)
    clean_non_vul = clean_scores[clean_y == 0]
    threshold = float(np.quantile(clean_non_vul, 1.0 - args.gate_fpr)) if len(clean_non_vul) else 0.5
    return gate, background, threshold, ";".join(gate_sources)


def gate_scores(gate, background, rows):
    texts = [row["func"] for row in rows]
    scores, flags = detector_predict(gate, texts, background)
    return scores, flags


def token_pool(train_items):
    counts = Counter()
    for item in train_items:
        counts.update(tok for tok in item["func"].split() if tok and tok not in AST_MARKERS)
    common = [tok for tok, _ in counts.most_common(256)]
    return common or ["int", "tmp", "0", ";"]


def project_mimicry_snippet(pool, rng, length):
    body = [rng.choice(pool) for _ in range(max(4, length))]
    return ["EXPR_STATEMENT", "1"] + body + ["LEAF_NODE", "1", ";"]


def fragmented_snippet(pool, rng, fragments, length):
    out = []
    frag_len = max(2, length // max(1, fragments))
    for frag_idx in range(fragments):
        out.extend(["SIMPLE_DECL", "1"])
        out.extend(rng.choice(pool) for _ in range(frag_len))
        out.extend(["LEAF_NODE", "1", ";"])
        if frag_idx + 1 < fragments:
            out.extend(["EXPR_STATEMENT", "1"])
    return out


def insert_tokens(tokens, snippet, rng, fragments=1):
    if fragments <= 1:
        pos = rng.randint(0, len(tokens))
        return tokens[:pos] + snippet + tokens[pos:], [{"token_start": pos, "token_end": pos + len(snippet)}]
    pieces = np.array_split(snippet, fragments)
    positions = sorted(rng.sample(range(len(tokens) + 1), k=min(fragments, len(tokens) + 1)), reverse=True)
    out = list(tokens)
    meta = []
    for pos, piece in zip(positions, pieces):
        piece = list(piece)
        out[pos:pos] = piece
        meta.append({"token_start": int(pos), "token_end": int(pos + len(piece))})
    return out, sorted(meta, key=lambda row: row["token_start"])


def resolve_compiler(compiler):
    if compiler == "none":
        return None, "compiler_not_requested"
    candidates = ["clang", "gcc"] if compiler == "auto" else [compiler]
    for candidate in candidates:
        path = shutil.which(candidate)
        if path:
            return path, "compiler_available"
    return None, "compiler_unavailable"


def balanced_braces(text):
    depth = 0
    for char in text:
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def compile_check(func_text, compiler_path, timeout=8):
    if compiler_path is None:
        return False, "compiler_unavailable"
    with tempfile.TemporaryDirectory(prefix="eatvul_compile_") as tmp:
        path = Path(tmp) / "sample.c"
        path.write_text(func_text, encoding="utf-8", errors="ignore")
        cmd = [compiler_path, "-fsyntax-only", "-x", "c", str(path)]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return False, "compiler_timeout"
    return result.returncode == 0, "compiler_valid" if result.returncode == 0 else "compiler_failed"


def source_snippet(attack, idx):
    if attack == "dead_branch":
        return (
            "\n"
            f"    if (0) {{ volatile int eatvul_dead_{idx} = 0; "
            f"eatvul_dead_{idx} += 1; }}\n"
        )
    if attack == "guarded_noop":
        return (
            "\n"
            f"    {{ volatile int eatvul_noop_{idx} = 0; "
            f"eatvul_noop_{idx} = eatvul_noop_{idx}; }}\n"
        )
    raise ValueError(f"Unknown source-level attack: {attack}")


def insert_source_snippet(func_text, snippet):
    brace = func_text.find("{")
    if brace < 0:
        return func_text, {"char_start": -1, "char_end": -1, "line": -1}, "no_insertion_point"
    insert_at = brace + 1
    out = func_text[:insert_at] + snippet + func_text[insert_at:]
    line = func_text[:insert_at].count("\n") + 1
    span = {"char_start": insert_at, "char_end": insert_at + len(snippet), "line": line}
    return out, span, "inserted_after_opening_brace"


def make_source_level_adv(project, attack, test_items, args):
    rng = random.Random(args.seed)
    vulnerable = [item for item in test_items if int(item["target"]) == 1]
    rng.shuffle(vulnerable)
    if args.limit_adv is not None:
        vulnerable = vulnerable[: args.limit_adv]
    compiler_path, compiler_state = resolve_compiler(args.compiler)
    rows = []
    for idx, item in enumerate(vulnerable):
        snippet = source_snippet(attack, idx)
        original_func = item["func"]
        new_func, span, insertion_status = insert_source_snippet(original_func, snippet)
        parser_status = "balanced_braces" if balanced_braces(new_func) else "unbalanced_braces"
        compiler_ok, compiler_status = compile_check(new_func, compiler_path, args.compile_timeout)
        if compiler_state == "compiler_not_requested":
            compiler_status = compiler_state
        elif compiler_state == "compiler_unavailable":
            compiler_status = compiler_state
        validation_status = "compiler_valid" if compiler_ok else compiler_status
        if parser_status != "balanced_braces":
            validation_status = "parser_failed"
        row = dict(item)
        row["idx"] = int(item.get("idx", idx))
        row["split"] = "adv"
        row["func"] = new_func
        row["target"] = 1
        row["insertion_meta"] = {
            "attack": attack,
            "template": attack,
            "generator": "source-level-conservative",
            "spans": [span],
            "insertion_status": insertion_status,
            "parser_status": parser_status,
            "compiler": args.compiler,
            "compiler_state": compiler_state,
            "validation_status": validation_status,
            "semantic_assumption": "unreachable or local volatile no-op; compiler validation is syntax-only",
        }
        rows.append(row)
    return rows, f"generated:{attack}"


def make_adaptive_adv(project, attack, train_items, test_items, args):
    if attack == "original":
        adv_items, source = load_project_split(project, "adv", args.limit_adv)
        return adv_items, source
    if attack in {"dead_branch", "guarded_noop"}:
        return make_source_level_adv(project, attack, test_items, args)
    rng = random.Random(args.seed)
    pool = token_pool(train_items)
    vulnerable = [item for item in test_items if int(item["target"]) == 1]
    if args.limit_adv is not None:
        vulnerable = vulnerable[: args.limit_adv]
    rows = []
    for idx, item in enumerate(vulnerable):
        tokens = item["func"].split()
        if attack == "project_mimicry":
            snippet = project_mimicry_snippet(pool, rng, args.insert_tokens)
            new_tokens, spans = insert_tokens(tokens, snippet, rng, fragments=1)
        elif attack == "fragmented":
            snippet = fragmented_snippet(pool, rng, args.fragments, args.insert_tokens)
            new_tokens, spans = insert_tokens(tokens, snippet, rng, fragments=args.fragments)
        else:
            raise ValueError(f"Unknown attack: {attack}")
        row = dict(item)
        row["idx"] = int(item.get("idx", idx))
        row["split"] = "adv"
        row["func"] = " ".join(new_tokens)
        row["target"] = 1
        row["insertion_meta"] = {
            "attack": attack,
            "snippet_tokens": len(snippet),
            "fragments": len(spans),
            "spans": spans,
            "generator": "project-token-pool",
            "validation_status": "not_compiler_validated",
        }
        rows.append(row)
    return rows, f"generated:{attack}"


def predict_tfidf(model, rows):
    texts = [row["func"] for row in rows]
    preds = model.predict(texts)
    probs = model.predict_proba(texts)[:, 1]
    return np.asarray(preds, dtype=int), np.asarray(probs, dtype=float)


def validation_status(row):
    meta = row.get("insertion_meta") or {}
    return meta.get("validation_status", "original_or_clean")


def count_validated(rows):
    return sum(1 for row in rows if validation_status(row) == "compiler_valid")


def write_predictions(path, project, victim, attack, rows, y_true, preds, probs, gate_score, gate_flag):
    out = []
    for row, true, pred, prob, score, flag in zip(rows, y_true, preds, probs, gate_score, gate_flag):
        out.append(
            {
                "idx": int(row["idx"]),
                "project": project,
                "victim": victim,
                "attack": attack,
                "split": row.get("split", "unknown"),
                "target": int(true),
                "pred": int(pred),
                "vulnerable_prob": float(prob),
                "gate_score": float(score),
                "gate_flag": int(flag),
                "data_source": row.get("data_source", ""),
                "validation_status": validation_status(row),
                "insertion_meta": row.get("insertion_meta"),
            }
        )
    save_jsonl(path, out)


def evaluate_one(project, victim, attack, args):
    train_items, train_source = load_project_split(project, "train", args.limit_train)
    test_items, test_source = load_project_split(project, "test", args.limit_test)
    train_items = balanced_subset(train_items, args.max_train, args.seed)
    adv_items, adv_source = make_adaptive_adv(project, attack, train_items, test_items, args)

    if victim == "tfidf":
        model = train_tfidf_victim(train_items)
        clean_pred, clean_prob = predict_tfidf(model, test_items)
        adv_pred, adv_prob = predict_tfidf(model, adv_items)
    else:
        predictor = train_transformer_victim(train_items, args, victim)
        clean_pred, clean_prob = predictor(test_items)
        adv_pred, adv_prob = predictor(adv_items)

    gate, background, threshold, gate_train_source = train_gate_for_project(project, test_items, args)
    clean_gate_score, clean_gate_flag = gate_scores(gate, background, test_items)
    adv_gate_score, adv_gate_flag = gate_scores(gate, background, adv_items)

    clean_texts, clean_y = texts_labels(test_items)
    adv_y = np.asarray([int(row["target"]) for row in adv_items], dtype=int)
    bypass = adv_pred == 0
    defended_pred = adv_pred.copy()
    defended_pred[adv_gate_score >= threshold] = 1
    clean_defended = clean_pred.copy()
    clean_defended[clean_gate_score >= threshold] = 1
    clean_non_vul = clean_y == 0

    pred_dir = Path(args.output_dir) / "predictions"
    write_predictions(
        pred_dir / f"{project}_{victim}_{attack}_clean.jsonl",
        project,
        victim,
        attack,
        test_items,
        clean_y,
        clean_pred,
        clean_prob,
        clean_gate_score,
        clean_gate_score >= threshold,
    )
    write_predictions(
        pred_dir / f"{project}_{victim}_{attack}_adv.jsonl",
        project,
        victim,
        attack,
        adv_items,
        adv_y,
        adv_pred,
        adv_prob,
        adv_gate_score,
        adv_gate_score >= threshold,
    )
    if attack != "original":
        save_jsonl(Path(args.output_dir) / "adaptive_samples" / f"{project}_{attack}.jsonl", adv_items)

    return {
        "project": project,
        "victim": victim,
        "attack": attack,
        "train_n": len(train_items),
        "clean_test_n": len(test_items),
        "adv_n": len(adv_items),
        "validated_adv_n": count_validated(adv_items),
        "evidence_role": "small_case" if project == "ffmpeg" or len(adv_items) < 10 else "generalization",
        "data_status": "source_level_external",
        "train_source": train_source,
        "test_source": test_source,
        "adv_source": adv_source,
        "gate_train_source": gate_train_source,
        "clean_acc": accuracy_score(clean_y, clean_pred),
        "clean_f1": f1_score(clean_y, clean_pred, zero_division=0),
        "defended_clean_f1": f1_score(clean_y, clean_defended, zero_division=0),
        "baseline_asr": float(np.mean(bypass)) if len(adv_pred) else 0.0,
        "defended_asr": float(np.mean(defended_pred == 0)) if len(defended_pred) else 0.0,
        "asr_reduction": float(np.mean(bypass) - np.mean(defended_pred == 0)) if len(defended_pred) else 0.0,
        "adv_bypassed": int(np.sum(bypass)),
        "gate_threshold": threshold,
        "gate_recall_all_adv": float(np.mean(adv_gate_score >= threshold)) if len(adv_gate_score) else 0.0,
        "gate_recall_on_bypassed": float(np.mean((adv_gate_score >= threshold)[bypass])) if np.any(bypass) else 0.0,
        "clean_non_vul_fpr": float(np.mean((clean_gate_score >= threshold)[clean_non_vul])) if np.any(clean_non_vul) else 0.0,
        "quarantine_rate_clean": float(np.mean(clean_gate_score >= threshold)) if len(clean_gate_score) else 0.0,
        "f1_drop": f1_score(clean_y, clean_pred, zero_division=0)
        - f1_score(clean_y, clean_defended, zero_division=0),
    }


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def dataset_summary(args):
    rows = []
    for project in args.datasets:
        for split in ["train", "test", "adv"]:
            items, source = load_project_split(project, split, args.limit_test if split != "train" else args.limit_train)
            counts = Counter(int(item["target"]) for item in items)
            rows.append(
                {
                    "project": project,
                    "split": split,
                    "n": len(items),
                    "label_0": counts.get(0, 0),
                    "label_1": counts.get(1, 0),
                    "source": source,
                }
            )
    write_csv(Path(args.output_dir) / "dataset_summary.csv", rows)
    for row in rows:
        print(row)


def validate_adaptive(args):
    rows = []
    for project in args.datasets:
        train_items, _source = load_project_split(project, "train", args.limit_train)
        test_items, _test_source = load_project_split(project, "test", args.limit_test)
        for attack in args.attack:
            adv_items, source = make_adaptive_adv(project, attack, train_items, test_items, args)
            missing_meta = sum(1 for item in adv_items if "insertion_meta" not in item)
            wrong_label = sum(1 for item in adv_items if int(item["target"]) != 1)
            compiler_valid = count_validated(adv_items)
            validation_counts = Counter(validation_status(item) for item in adv_items)
            rows.append(
                {
                    "project": project,
                    "attack": attack,
                    "n": len(adv_items),
                    "validated_adv_n": compiler_valid,
                    "validation_counts": json.dumps(dict(validation_counts), sort_keys=True),
                    "source": source,
                    "missing_meta": missing_meta,
                    "wrong_label": wrong_label,
                }
            )
    write_csv(Path(args.output_dir) / "adaptive_validation.csv", rows)
    for row in rows:
        print(row)


def run(args):
    set_seed(args.seed)
    rows = []
    for project in args.datasets:
        for victim in args.victims:
            for attack in args.attack:
                print(f"Running project={project} victim={victim} attack={attack}")
                rows.append(evaluate_one(project, victim, attack, args))
    out_path = Path(args.output_dir) / "extension_results.csv"
    write_csv(out_path, rows)
    print(f"Saved: {out_path}")
    for row in rows:
        print(
            row["project"],
            row["victim"],
            row["attack"],
            f"clean_f1={float(row['clean_f1']):.3f}",
            f"asr={float(row['baseline_asr']):.3f}",
            f"def_asr={float(row['defended_asr']):.3f}",
            f"status={row['data_status']}",
        )


def main():
    parser = argparse.ArgumentParser(description="Extension experiments for EaTVul defense evaluation.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_common(p):
        p.add_argument("--datasets", nargs="+", default=DEFAULT_PROJECTS)
        p.add_argument("--output-dir", default=str(OUT_DIR))
        p.add_argument("--seed", type=int, default=7)
        p.add_argument("--limit-train", type=int)
        p.add_argument("--limit-test", type=int)
        p.add_argument("--compiler", choices=["auto", "clang", "gcc", "none"], default="auto")
        p.add_argument("--compile-timeout", type=int, default=8)

    p = sub.add_parser("dataset-summary")
    add_common(p)
    p.set_defaults(func=dataset_summary)

    p = sub.add_parser("validate-adaptive")
    add_common(p)
    p.add_argument("--attack", nargs="+", default=["dead_branch", "guarded_noop"])
    p.add_argument("--limit-adv", type=int, default=20)
    p.add_argument("--insert-tokens", type=int, default=48)
    p.add_argument("--fragments", type=int, default=4)
    p.set_defaults(func=validate_adaptive)

    p = sub.add_parser("run")
    add_common(p)
    p.add_argument("--victims", nargs="+", choices=["tfidf", "linevul", "graphcodebert"], default=["tfidf"])
    p.add_argument(
        "--attack",
        nargs="+",
        choices=["original", "project_mimicry", "fragmented", "dead_branch", "guarded_noop"],
        default=["original"],
    )
    p.add_argument("--max-train", type=int, default=160)
    p.add_argument("--limit-adv", type=int)
    p.add_argument("--gate-fpr", type=float, default=0.10)
    p.add_argument("--insert-tokens", type=int, default=48)
    p.add_argument("--fragments", type=int, default=4)
    p.add_argument("--linevul-model", default=str(ROOT / "models" / "codebert-base"))
    p.add_argument("--graphcodebert-model", default="microsoft/graphcodebert-base")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--no-cuda", action="store_true")
    p.add_argument("--epochs", type=int, default=1)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--max-len", type=int, default=256)
    p.add_argument("--lr", type=float, default=2e-5)
    p.set_defaults(func=run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
