import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler

from eatvul_defense import (
    AST_STRUCT_TOKENS,
    CONTROL_TOKENS,
    DATASETS,
    ROOT,
    TYPE_TOKENS,
    BackgroundStats,
    detector_predict,
    load_jsonl,
    name_like,
    texts_labels,
    train_detector,
    train_target,
)
from eatvul_localize_sanitize import window_features


OUT_DIR = ROOT / "results" / "eatvul_component_defense"

TOP_LEVEL_TYPES = {
    "FUNCTION_DEF",
    "SIMPLE_DECL",
    "CLASS_DEF",
    "VAR_DECL",
    "EXPR_STATEMENT",
    "SELECTION",
    "ITERATION",
    "JUMP_STATEMENT",
}


FEATURE_NAMES = [
    "rare_ratio",
    "unseen_ratio",
    "mean_idf",
    "p95_idf",
    "bigram_nll",
    "name_ratio",
    "isolated_name_ratio",
    "struct_ratio",
    "leaf_ratio",
    "decl_ratio",
    "function_def_ratio",
    "control_ratio",
    "type_ratio",
    "max_depth",
    "log_length",
    "external_name_overlap",
    "pdg_isolation",
    "kind_function",
    "kind_decl",
    "kind_control",
]


def structural_depth_positions(tokens):
    positions = []
    for idx, tok in enumerate(tokens[:-1]):
        if tok in TOP_LEVEL_TYPES and tokens[idx + 1].isdigit():
            positions.append((idx, tok, int(tokens[idx + 1])))
    return positions


def top_level_components(tokens, min_tokens=16):
    positions = [(idx, tok) for idx, tok, depth in structural_depth_positions(tokens) if depth == 1]
    if not positions:
        return [(0, len(tokens), "WHOLE_FUNC")] if len(tokens) >= min_tokens else []

    spans = []
    if positions[0][0] > min_tokens:
        spans.append((0, positions[0][0], "PREFIX"))
    for pos_idx, (start, kind) in enumerate(positions):
        end = positions[pos_idx + 1][0] if pos_idx + 1 < len(positions) else len(tokens)
        if end - start >= min_tokens:
            spans.append((start, end, kind))
    return spans


def clustered_components(tokens, max_cluster=4, min_tokens=16, max_tokens=6000):
    base = top_level_components(tokens, min_tokens=min_tokens)
    spans = []
    for i in range(len(base)):
        for size in range(1, max_cluster + 1):
            group = base[i : i + size]
            if len(group) != size:
                break
            start = group[0][0]
            end = group[-1][1]
            if end - start > max_tokens:
                break
            kind = "+".join(item[2] for item in group[:3])
            if len(group) > 3:
                kind += "+..."
            spans.append((start, end, kind))
    return spans


def names_in(tokens):
    return [tok for tok in tokens if name_like(tok)]


def component_features(tokens, start, end, kind, background, full_counts=None):
    base = window_features(tokens, start, end, background, full_counts)
    component_tokens = tokens[start:end]
    length = max(1, len(component_tokens))
    inside_names = set(names_in(component_tokens))
    outside_names = set(names_in(tokens[:start] + tokens[end:]))
    overlap = len(inside_names & outside_names) / max(1, len(inside_names))
    pdg_isolation = 1.0 - overlap
    kind_function = 1.0 if "FUNCTION_DEF" in kind else 0.0
    kind_decl = 1.0 if any(k in kind for k in ["SIMPLE_DECL", "VAR_DECL", "CLASS_DEF"]) else 0.0
    kind_control = 1.0 if any(k in kind for k in ["SELECTION", "ITERATION", "JUMP_STATEMENT"]) else 0.0
    extra = np.asarray(
        [
            np.log1p(length),
            overlap,
            pdg_isolation,
            kind_function,
            kind_decl,
            kind_control,
        ],
        dtype=np.float32,
    )
    return np.concatenate([base, extra])


def collect_component_matrix(items, background, max_cluster, max_components_per_item=64):
    rows = []
    for item in items:
        tokens = item["func"].split()
        full_counts = Counter(tokens)
        for idx, (start, end, kind) in enumerate(clustered_components(tokens, max_cluster=max_cluster)):
            if idx >= max_components_per_item:
                break
            rows.append(component_features(tokens, start, end, kind, background, full_counts))
    if not rows:
        return np.zeros((0, len(FEATURE_NAMES)), dtype=np.float32)
    return np.vstack(rows)


class ComponentLocator:
    def __init__(self, background, scaler, weights, threshold, max_cluster):
        self.background = background
        self.scaler = scaler
        self.weights = weights
        self.threshold = threshold
        self.max_cluster = max_cluster

    @classmethod
    def fit(cls, clean_items, background, max_cluster, clean_component_fpr, calibration_items):
        calibration_slice = clean_items[:calibration_items] if calibration_items else clean_items
        x_clean = collect_component_matrix(calibration_slice, background, max_cluster)
        scaler = StandardScaler()
        x_scaled = scaler.fit_transform(x_clean)
        weights = np.asarray(
            [
                1.10,
                1.10,
                0.90,
                0.70,
                0.90,
                0.20,
                0.85,
                0.20,
                0.10,
                0.70,
                0.45,
                -0.20,
                0.15,
                0.10,
                0.15,
                -0.65,
                1.05,
                0.20,
                0.40,
                -0.20,
            ],
            dtype=np.float32,
        )
        scores = np.maximum(x_scaled, -3.0).dot(weights)
        threshold = float(np.quantile(scores, 1.0 - clean_component_fpr))
        return cls(background, scaler, weights, threshold, max_cluster)

    def score_components(self, text):
        tokens = text.split()
        spans = clustered_components(tokens, max_cluster=self.max_cluster)
        if not spans:
            return tokens, []
        full_counts = Counter(tokens)
        x = np.vstack([component_features(tokens, start, end, kind, self.background, full_counts) for start, end, kind in spans])
        scaled = self.scaler.transform(x)
        scores = np.maximum(scaled, -3.0).dot(self.weights)
        return tokens, [
            {
                "start": int(start),
                "end": int(end),
                "kind": kind,
                "score": float(score),
            }
            for (start, end, kind), score in zip(spans, scores)
        ]

    def sanitize_guided(self, item, target, max_spans, candidate_components, min_prob_gain, min_score_margin):
        tokens, scored = self.score_components(item["func"])
        if not scored:
            return dict(item), empty_meta()

        base_prob = float(target.predict_proba([item["func"]])[0, 1])
        threshold = self.threshold + min_score_margin
        above_threshold = [row for row in scored if row["score"] >= threshold]
        top_ranked = sorted(scored, key=lambda row: row["score"], reverse=True)[:candidate_components]
        candidate_by_span = {(row["start"], row["end"]): row for row in above_threshold + top_ranked}
        candidates = sorted(candidate_by_span.values(), key=lambda row: row["score"], reverse=True)

        evaluated = []
        trial_rows = []
        trial_texts = []
        for row in candidates:
            start, end = row["start"], row["end"]
            if row["score"] < threshold:
                continue
            trial_tokens = [tok for idx, tok in enumerate(tokens) if not (start <= idx < end)]
            trial_rows.append(row)
            trial_texts.append(" ".join(trial_tokens))
        trial_probs = target.predict_proba(trial_texts)[:, 1] if trial_texts else []
        for row, trial_prob in zip(trial_rows, trial_probs):
            gain = trial_prob - base_prob
            if gain >= min_prob_gain:
                enriched = dict(row)
                enriched["vuln_prob_gain"] = float(gain)
                evaluated.append(enriched)

        selected = []
        gains = []
        for row in sorted(evaluated, key=lambda r: (r["vuln_prob_gain"], r["score"]), reverse=True):
            if len(selected) >= max_spans:
                break
            start, end = row["start"], row["end"]
            if any(max(0, min(end, old["end"]) - max(start, old["start"])) > 0 for old in selected):
                continue
            selected.append(row)
            gains.append(row["vuln_prob_gain"])

        if not selected:
            return dict(item), {
                **empty_meta(),
                "top_score": max([row["score"] for row in scored], default=float("-inf")),
            }

        keep = np.ones(len(tokens), dtype=bool)
        for row in selected:
            keep[row["start"] : row["end"]] = False
        sanitized_tokens = [tok for tok, flag in zip(tokens, keep) if flag]
        sanitized = dict(item)
        sanitized["func"] = " ".join(sanitized_tokens)
        sanitized["localized_components"] = [
            {
                "token_start": row["start"],
                "token_end": row["end"],
                "kind": row["kind"],
                "score": row["score"],
                "vuln_prob_gain": row["vuln_prob_gain"],
            }
            for row in sorted(selected, key=lambda r: r["start"])
        ]
        removed = len(tokens) - len(sanitized_tokens)
        return sanitized, {
            "num_spans": len(selected),
            "removed_tokens": removed,
            "removed_ratio": removed / max(1, len(tokens)),
            "top_score": max([row["score"] for row in scored], default=float("-inf")),
            "mean_prob_gain": float(np.mean(gains)) if gains else 0.0,
        }


def empty_meta():
    return {
        "num_spans": 0,
        "removed_tokens": 0,
        "removed_ratio": 0.0,
        "top_score": float("-inf"),
        "mean_prob_gain": 0.0,
    }


def save_jsonl(path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def mean_meta(meta, key):
    return float(np.mean([item[key] for item in meta])) if meta else 0.0


def sample_gate_masks(name, clean_texts, clean_y, adv_texts, args):
    if not args.sample_gate:
        return None, None, 0.0
    gate_train_items = []
    gate_adv_items = []
    for other, other_paths in DATASETS.items():
        if other == name:
            continue
        gate_train_items.extend(load_jsonl(other_paths["test"]))
        gate_adv_items.extend(load_jsonl(other_paths["adv"]))
    gate_background = BackgroundStats([item["func"] for item in gate_train_items])
    gate_detector = train_detector(gate_train_items, gate_adv_items, gate_background)
    gate_train_texts, gate_train_y = texts_labels(gate_train_items)
    gate_train_prob, _ = detector_predict(gate_detector, gate_train_texts, gate_background)
    non_vul_scores = gate_train_prob[gate_train_y == 0]
    threshold = float(np.quantile(non_vul_scores, 1.0 - args.sample_gate_fpr)) if len(non_vul_scores) else 0.5
    clean_prob, _ = detector_predict(gate_detector, clean_texts, gate_background)
    adv_prob, _ = detector_predict(gate_detector, adv_texts, gate_background)
    return clean_prob >= threshold, adv_prob >= threshold, threshold


def sanitize_items(items, locator, target, args, allowed_mask=None, initial_pred=None):
    sanitized = []
    meta = []
    for idx, item in enumerate(items):
        if allowed_mask is not None and not bool(allowed_mask[idx]):
            sanitized.append(dict(item))
            meta.append(empty_meta())
            continue
        if args.gate_on_benign and initial_pred is not None and int(initial_pred[idx]) == 1:
            sanitized.append(dict(item))
            meta.append(empty_meta())
            continue
        if args.gate_on_benign and initial_pred is None and int(target.predict([item["func"]])[0]) == 1:
            sanitized.append(dict(item))
            meta.append(empty_meta())
            continue
        new_item, item_meta = locator.sanitize_guided(
            item,
            target,
            args.max_spans,
            args.candidate_components,
            args.min_prob_gain,
            args.min_score_margin,
        )
        sanitized.append(new_item)
        meta.append(item_meta)
    return sanitized, meta


def evaluate_dataset(name, args):
    paths = DATASETS[name]
    train_items = load_jsonl(paths["train"])
    test_items = load_jsonl(paths["test"])
    adv_items = load_jsonl(paths["adv"])

    background = BackgroundStats([item["func"] for item in train_items])
    target = train_target(train_items)
    locator = ComponentLocator.fit(
        train_items,
        background,
        args.max_cluster,
        args.calibrate_component_fpr,
        args.calibration_items,
    )

    clean_texts, clean_y = texts_labels(test_items)
    adv_texts, _ = texts_labels(adv_items)
    clean_pred = target.predict(clean_texts)
    adv_pred = target.predict(adv_texts)

    clean_allowed, adv_allowed, sample_gate_threshold = sample_gate_masks(name, clean_texts, clean_y, adv_texts, args)
    clean_sanitized, clean_meta = sanitize_items(test_items, locator, target, args, clean_allowed, clean_pred)
    adv_sanitized, adv_meta = sanitize_items(adv_items, locator, target, args, adv_allowed, adv_pred)

    clean_sanitized_texts, _ = texts_labels(clean_sanitized)
    adv_sanitized_texts, _ = texts_labels(adv_sanitized)
    clean_sanitized_pred = target.predict(clean_sanitized_texts)
    adv_sanitized_pred = target.predict(adv_sanitized_texts)

    out_prefix = f"{name}_component_fpr{args.calibrate_component_fpr:g}_cluster{args.max_cluster}"
    if args.sample_gate:
        out_prefix += f"_samplegate{args.sample_gate_fpr:g}"
    save_jsonl(OUT_DIR / f"{out_prefix}_adv_sanitized.json", adv_sanitized)
    save_jsonl(OUT_DIR / f"{out_prefix}_clean_sanitized.json", clean_sanitized)

    baseline_asr = float(np.mean(adv_pred == 0))
    sanitized_asr = float(np.mean(adv_sanitized_pred == 0))
    row = {
        "dataset": name,
        "component_threshold": locator.threshold,
        "sample_gate_threshold": sample_gate_threshold,
        "target_clean_acc": accuracy_score(clean_y, clean_pred),
        "target_clean_f1": f1_score(clean_y, clean_pred, zero_division=0),
        "component_clean_f1": f1_score(clean_y, clean_sanitized_pred, zero_division=0),
        "baseline_asr": baseline_asr,
        "component_asr": sanitized_asr,
        "asr_reduction": baseline_asr - sanitized_asr,
        "clean_modified_rate": float(np.mean([m["num_spans"] > 0 for m in clean_meta])) if clean_meta else 0.0,
        "adv_modified_rate": float(np.mean([m["num_spans"] > 0 for m in adv_meta])) if adv_meta else 0.0,
        "clean_removed_ratio": mean_meta(clean_meta, "removed_ratio"),
        "adv_removed_ratio": mean_meta(adv_meta, "removed_ratio"),
        "adv_avg_removed_tokens": mean_meta(adv_meta, "removed_tokens"),
        "adv_mean_prob_gain": mean_meta(adv_meta, "mean_prob_gain"),
    }
    return row


def fmt(value):
    return f"{value:.3f}" if isinstance(value, float) else str(value)


def print_markdown_table(rows):
    headers = [
        "dataset",
        "target_clean_f1",
        "component_clean_f1",
        "baseline_asr",
        "component_asr",
        "asr_reduction",
        "adv_modified_rate",
        "adv_removed_ratio",
        "clean_modified_rate",
    ]
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        print("| " + " | ".join(fmt(row[h]) for h in headers) + " |")


def run(args):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    names = args.datasets or list(DATASETS)
    rows = [evaluate_dataset(name, args) for name in names]
    sample_suffix = f"sample_gate{args.sample_gate_fpr:g}" if args.sample_gate else "no_sample_gate"
    gate_suffix = "benign_gate" if args.gate_on_benign else "all"
    out_csv = OUT_DIR / (
        f"component_sanitize_fpr{args.calibrate_component_fpr:g}_cluster{args.max_cluster}_"
        f"max{args.max_spans}_{gate_suffix}_{sample_suffix}_results.csv"
    )
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print_markdown_table(rows)
    print(f"\nSaved: {out_csv}")


def main():
    parser = argparse.ArgumentParser(
        description="Sanitize EaTVul adversarial inserts using AST component/PDG-isolation style boundaries."
    )
    parser.add_argument("--datasets", nargs="*", choices=DATASETS.keys())
    parser.add_argument("--calibrate-component-fpr", type=float, default=0.01)
    parser.add_argument("--max-cluster", type=int, default=4)
    parser.add_argument("--calibration-items", type=int, default=1200)
    parser.add_argument("--max-spans", type=int, default=2)
    parser.add_argument("--candidate-components", type=int, default=48)
    parser.add_argument("--min-prob-gain", type=float, default=0.005)
    parser.add_argument("--min-score-margin", type=float, default=0.0)
    gate_group = parser.add_mutually_exclusive_group()
    gate_group.add_argument("--gate-on-benign", dest="gate_on_benign", action="store_true", default=True)
    gate_group.add_argument("--no-gate-on-benign", dest="gate_on_benign", action="store_false")
    parser.add_argument("--sample-gate", action="store_true")
    parser.add_argument("--sample-gate-fpr", type=float, default=0.50)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
