import argparse
import csv
import json
import math
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


OUT_DIR = ROOT / "results" / "eatvul_local_defense"


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
]


def iter_windows(tokens, window, stride):
    if not tokens:
        return
    if len(tokens) <= window:
        yield 0, len(tokens)
        return
    for start in range(0, len(tokens), stride):
        end = min(len(tokens), start + window)
        if end - start < max(16, window // 4) and start > 0:
            break
        yield start, end
        if end == len(tokens):
            break


def max_numeric_depth(tokens):
    numeric = [int(tok) for tok in tokens if tok.isdigit()]
    return max(numeric) if numeric else 0


def window_features(tokens, start, end, background, full_counts=None):
    window_tokens = tokens[start:end]
    length = max(1, len(window_tokens))
    full_counts = full_counts or Counter(tokens)
    local_counts = Counter(window_tokens)

    idfs = [background.token_idf(tok) for tok in window_tokens]
    names = [tok for tok in window_tokens if name_like(tok)]
    rare_count = sum(1 for tok in window_tokens if tok in background.rare or background.unigram.get(tok, 0) == 0)
    unseen_count = sum(1 for tok in window_tokens if background.unigram.get(tok, 0) == 0)
    isolated_names = sum(
        1
        for tok in names
        if background.unigram.get(tok, 0) <= 1 and full_counts.get(tok, 0) == local_counts.get(tok, 0)
    )
    decl_count = sum(
        1
        for tok in window_tokens
        if tok in {"SIMPLE_DECL", "VAR_DECL", "PARAMETER_DECL", "CLASS_DEF", "STRUCT_DECL"}
    )

    return np.asarray(
        [
            rare_count / length,
            unseen_count / length,
            float(np.mean(idfs)) if idfs else 0.0,
            float(np.percentile(idfs, 95)) if idfs else 0.0,
            background.bigram_nll(window_tokens),
            len(names) / length,
            isolated_names / max(1, len(names)),
            sum(tok in AST_STRUCT_TOKENS for tok in window_tokens) / length,
            window_tokens.count("LEAF_NODE") / length,
            decl_count / length,
            window_tokens.count("FUNCTION_DEF") / length,
            sum(tok in CONTROL_TOKENS for tok in window_tokens) / length,
            sum(tok in TYPE_TOKENS for tok in window_tokens) / length,
            max_numeric_depth(window_tokens),
        ],
        dtype=np.float32,
    )


def collect_window_matrix(items, background, window, stride, max_windows_per_item=64):
    rows = []
    for item in items:
        tokens = item["func"].split()
        full_counts = Counter(tokens)
        for idx, (start, end) in enumerate(iter_windows(tokens, window, stride)):
            if idx >= max_windows_per_item:
                break
            rows.append(window_features(tokens, start, end, background, full_counts))
    if not rows:
        return np.zeros((0, len(FEATURE_NAMES)), dtype=np.float32)
    return np.vstack(rows)


class LocalWindowLocator:
    def __init__(self, background, scaler, weights, threshold, window, stride):
        self.background = background
        self.scaler = scaler
        self.weights = weights
        self.threshold = threshold
        self.window = window
        self.stride = stride

    @classmethod
    def fit(cls, clean_items, background, window, stride, clean_window_fpr):
        x_clean = collect_window_matrix(clean_items, background, window, stride)
        scaler = StandardScaler()
        x_scaled = scaler.fit_transform(x_clean)

        weights = np.asarray(
            [
                1.20,  # rare_ratio
                1.20,  # unseen_ratio
                1.00,  # mean_idf
                0.80,  # p95_idf
                1.00,  # bigram_nll
                0.25,  # name_ratio
                0.90,  # isolated_name_ratio
                0.35,  # struct_ratio
                0.20,  # leaf_ratio
                0.60,  # decl_ratio
                0.65,  # function_def_ratio
                -0.15,  # control_ratio: standalone benign snippets often have little control/data logic
                0.15,  # type_ratio
                0.15,  # max_depth
            ],
            dtype=np.float32,
        )
        scores = np.maximum(x_scaled, -3.0).dot(weights)
        threshold = float(np.quantile(scores, 1.0 - clean_window_fpr))
        return cls(background, scaler, weights, threshold, window, stride)

    def score_windows(self, text):
        tokens = text.split()
        full_counts = Counter(tokens)
        rows = []
        spans = []
        for start, end in iter_windows(tokens, self.window, self.stride):
            rows.append(window_features(tokens, start, end, self.background, full_counts))
            spans.append((start, end))
        if not rows:
            return tokens, []
        x = self.scaler.transform(np.vstack(rows))
        scores = np.maximum(x, -3.0).dot(self.weights)
        return tokens, [(span[0], span[1], float(score)) for span, score in zip(spans, scores)]

    def suspicious_spans(self, text, max_spans, min_score_margin):
        tokens, scored = self.score_windows(text)
        candidates = [
            (start, end, score)
            for start, end, score in scored
            if score >= self.threshold + min_score_margin
        ]
        candidates.sort(key=lambda item: item[2], reverse=True)

        selected = []
        for start, end, score in candidates:
            if len(selected) >= max_spans:
                break
            overlap_too_large = False
            for s_start, s_end, _ in selected:
                overlap = max(0, min(end, s_end) - max(start, s_start))
                if overlap / max(1, min(end - start, s_end - s_start)) > 0.5:
                    overlap_too_large = True
                    break
            if not overlap_too_large:
                selected.append((start, end, score))

        if not selected:
            return tokens, [], scored

        selected.sort()
        merged = []
        cur_start, cur_end, cur_score = selected[0]
        for start, end, score in selected[1:]:
            if start <= cur_end:
                cur_end = max(cur_end, end)
                cur_score = max(cur_score, score)
            else:
                merged.append((cur_start, cur_end, cur_score))
                cur_start, cur_end, cur_score = start, end, score
        merged.append((cur_start, cur_end, cur_score))
        return tokens, merged, scored

    def sanitize(self, item, max_spans, min_score_margin):
        tokens, spans, scored = self.suspicious_spans(item["func"], max_spans, min_score_margin)
        if not spans:
            return dict(item), {
                "num_spans": 0,
                "removed_tokens": 0,
                "removed_ratio": 0.0,
                "top_score": max([score for _, _, score in scored], default=float("-inf")),
            }

        keep = np.ones(len(tokens), dtype=bool)
        for start, end, _ in spans:
            keep[start:end] = False
        sanitized_tokens = [tok for tok, flag in zip(tokens, keep) if flag]
        sanitized = dict(item)
        sanitized["func"] = " ".join(sanitized_tokens)
        sanitized["localized_spans"] = [
            {"token_start": int(start), "token_end": int(end), "score": float(score)}
            for start, end, score in spans
        ]
        removed = len(tokens) - len(sanitized_tokens)
        return sanitized, {
            "num_spans": len(spans),
            "removed_tokens": removed,
            "removed_ratio": removed / max(1, len(tokens)),
            "top_score": max([score for _, _, score in scored], default=float("-inf")),
        }

    def sanitize_guided(
        self,
        item,
        target,
        max_spans,
        min_score_margin,
        candidate_windows,
        min_prob_gain,
    ):
        tokens, scored = self.score_windows(item["func"])
        if not scored:
            return dict(item), {
                "num_spans": 0,
                "removed_tokens": 0,
                "removed_ratio": 0.0,
                "top_score": float("-inf"),
                "mean_prob_gain": 0.0,
            }

        base_prob = float(target.predict_proba([item["func"]])[0, 1])
        threshold = self.threshold + min_score_margin
        ranked = sorted(scored, key=lambda row: row[2], reverse=True)
        candidate_map = {(start, end): score for start, end, score in ranked[:candidate_windows]}
        candidate_map.update({(start, end): score for start, end, score in ranked if score >= threshold})
        candidates = [(start, end, score) for (start, end), score in candidate_map.items()]

        selected = []
        gains = []
        for start, end, score in sorted(candidates, key=lambda row: row[2], reverse=True):
            if len(selected) >= max_spans:
                break
            if any(max(0, min(end, s_end) - max(start, s_start)) > 0 for s_start, s_end, _, _ in selected):
                continue
            trial_tokens = [
                tok
                for idx, tok in enumerate(tokens)
                if not (start <= idx < end) and all(not (s_start <= idx < s_end) for s_start, s_end, _, _ in selected)
            ]
            trial_prob = float(target.predict_proba([" ".join(trial_tokens)])[0, 1])
            gain = trial_prob - base_prob
            if gain >= min_prob_gain and score >= threshold:
                selected.append((start, end, score, gain))
                gains.append(gain)

        if not selected:
            return dict(item), {
                "num_spans": 0,
                "removed_tokens": 0,
                "removed_ratio": 0.0,
                "top_score": max([score for _, _, score in scored], default=float("-inf")),
                "mean_prob_gain": 0.0,
            }

        keep = np.ones(len(tokens), dtype=bool)
        for start, end, _, _ in selected:
            keep[start:end] = False
        sanitized_tokens = [tok for tok, flag in zip(tokens, keep) if flag]
        sanitized = dict(item)
        sanitized["func"] = " ".join(sanitized_tokens)
        sanitized["localized_spans"] = [
            {
                "token_start": int(start),
                "token_end": int(end),
                "score": float(score),
                "vuln_prob_gain": float(gain),
            }
            for start, end, score, gain in sorted(selected)
        ]
        removed = len(tokens) - len(sanitized_tokens)
        return sanitized, {
            "num_spans": len(selected),
            "removed_tokens": removed,
            "removed_ratio": removed / max(1, len(tokens)),
            "top_score": max([score for _, _, score in scored], default=float("-inf")),
            "mean_prob_gain": float(np.mean(gains)) if gains else 0.0,
        }


def sanitize_items(items, locator, max_spans, min_score_margin, target=None, args=None, allowed_mask=None):
    sanitized = []
    meta = []
    for idx, item in enumerate(items):
        if allowed_mask is not None and not bool(allowed_mask[idx]):
            sanitized.append(dict(item))
            meta.append(
                {
                    "num_spans": 0,
                    "removed_tokens": 0,
                    "removed_ratio": 0.0,
                    "top_score": float("-inf"),
                    "mean_prob_gain": 0.0,
                }
            )
            continue
        if target is not None and args is not None and args.gate_on_benign:
            initial_pred = int(target.predict([item["func"]])[0])
            if initial_pred == 1:
                sanitized.append(dict(item))
                meta.append(
                    {
                        "num_spans": 0,
                        "removed_tokens": 0,
                        "removed_ratio": 0.0,
                        "top_score": float("-inf"),
                        "mean_prob_gain": 0.0,
                    }
                )
                continue
        if target is not None and args is not None and args.guided:
            new_item, item_meta = locator.sanitize_guided(
                item,
                target,
                max_spans,
                min_score_margin,
                args.candidate_windows,
                args.min_prob_gain,
            )
        else:
            new_item, item_meta = locator.sanitize(item, max_spans, min_score_margin)
        sanitized.append(new_item)
        meta.append(item_meta)
    return sanitized, meta


def save_jsonl(path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def mean_meta(meta, key):
    return float(np.mean([item[key] for item in meta])) if meta else 0.0


def evaluate_dataset(name, args):
    paths = DATASETS[name]
    train_items = load_jsonl(paths["train"])
    test_items = load_jsonl(paths["test"])
    adv_items = load_jsonl(paths["adv"])

    background = BackgroundStats([item["func"] for item in train_items])
    target = train_target(train_items)
    locator = LocalWindowLocator.fit(
        train_items,
        background,
        args.window,
        args.stride,
        args.calibrate_window_fpr,
    )

    clean_texts, clean_y = texts_labels(test_items)
    adv_texts, _ = texts_labels(adv_items)
    clean_pred = target.predict(clean_texts)
    adv_pred = target.predict(adv_texts)

    clean_allowed = None
    adv_allowed = None
    sample_gate_threshold = 0.0
    if args.sample_gate:
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
        if len(non_vul_scores):
            sample_gate_threshold = float(np.quantile(non_vul_scores, 1.0 - args.sample_gate_fpr))
        clean_gate_prob, _ = detector_predict(gate_detector, clean_texts, gate_background)
        adv_gate_prob, _ = detector_predict(gate_detector, adv_texts, gate_background)
        clean_allowed = clean_gate_prob >= sample_gate_threshold
        adv_allowed = adv_gate_prob >= sample_gate_threshold

    clean_sanitized, clean_meta = sanitize_items(
        test_items, locator, args.max_spans, args.min_score_margin, target, args, clean_allowed
    )
    adv_sanitized, adv_meta = sanitize_items(
        adv_items, locator, args.max_spans, args.min_score_margin, target, args, adv_allowed
    )
    clean_sanitized_texts, _ = texts_labels(clean_sanitized)
    adv_sanitized_texts, _ = texts_labels(adv_sanitized)

    clean_sanitized_pred = target.predict(clean_sanitized_texts)
    adv_sanitized_pred = target.predict(adv_sanitized_texts)

    out_prefix = f"{name}_w{args.window}_s{args.stride}_fpr{args.calibrate_window_fpr:g}"
    save_jsonl(OUT_DIR / f"{out_prefix}_adv_sanitized.json", adv_sanitized)
    save_jsonl(OUT_DIR / f"{out_prefix}_clean_sanitized.json", clean_sanitized)

    baseline_asr = float(np.mean(adv_pred == 0))
    sanitized_asr = float(np.mean(adv_sanitized_pred == 0))
    row = {
        "dataset": name,
        "window": args.window,
        "stride": args.stride,
        "window_threshold": locator.threshold,
        "sample_gate_threshold": sample_gate_threshold,
        "target_clean_acc": accuracy_score(clean_y, clean_pred),
        "target_clean_f1": f1_score(clean_y, clean_pred, zero_division=0),
        "sanitized_clean_f1": f1_score(clean_y, clean_sanitized_pred, zero_division=0),
        "baseline_asr": baseline_asr,
        "sanitized_asr": sanitized_asr,
        "asr_reduction": baseline_asr - sanitized_asr,
        "clean_modified_rate": mean_meta(clean_meta, "num_spans"),
        "adv_modified_rate": mean_meta(adv_meta, "num_spans"),
        "clean_removed_ratio": mean_meta(clean_meta, "removed_ratio"),
        "adv_removed_ratio": mean_meta(adv_meta, "removed_ratio"),
        "adv_avg_removed_tokens": mean_meta(adv_meta, "removed_tokens"),
        "adv_mean_top_window_score": mean_meta(adv_meta, "top_score"),
        "adv_mean_prob_gain": mean_meta(adv_meta, "mean_prob_gain"),
    }
    row["clean_modified_rate"] = float(np.mean([m["num_spans"] > 0 for m in clean_meta])) if clean_meta else 0.0
    row["adv_modified_rate"] = float(np.mean([m["num_spans"] > 0 for m in adv_meta])) if adv_meta else 0.0
    return row


def fmt(value):
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def print_markdown_table(rows):
    headers = [
        "dataset",
        "target_clean_f1",
        "sanitized_clean_f1",
        "baseline_asr",
        "sanitized_asr",
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

    gate_suffix = "benign_gate" if args.gate_on_benign else "all"
    sample_suffix = f"sample_gate{args.sample_gate_fpr:g}" if args.sample_gate else "no_sample_gate"
    guided_suffix = "guided" if args.guided else "unguided"
    suffix = (
        f"w{args.window}_s{args.stride}_fpr{args.calibrate_window_fpr:g}_"
        f"max{args.max_spans}_{guided_suffix}_{gate_suffix}_{sample_suffix}"
    )
    out_csv = OUT_DIR / f"localize_sanitize_{suffix}_results.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print_markdown_table(rows)
    print(f"\nSaved: {out_csv}")


def main():
    parser = argparse.ArgumentParser(
        description="Localize suspicious EaTVul inserted AST-token spans, delete them, and re-run vulnerability detection."
    )
    parser.add_argument("--datasets", nargs="*", choices=DATASETS.keys())
    parser.add_argument("--window", type=int, default=256)
    parser.add_argument("--stride", type=int, default=128)
    parser.add_argument("--max-spans", type=int, default=3)
    parser.add_argument("--candidate-windows", type=int, default=24)
    guided_group = parser.add_mutually_exclusive_group()
    guided_group.add_argument("--guided", dest="guided", action="store_true", default=True)
    guided_group.add_argument("--no-guided", dest="guided", action="store_false")
    gate_group = parser.add_mutually_exclusive_group()
    gate_group.add_argument("--gate-on-benign", dest="gate_on_benign", action="store_true", default=True)
    gate_group.add_argument("--no-gate-on-benign", dest="gate_on_benign", action="store_false")
    parser.add_argument("--sample-gate", action="store_true")
    parser.add_argument("--sample-gate-fpr", type=float, default=0.10)
    parser.add_argument(
        "--calibrate-window-fpr",
        type=float,
        default=0.02,
        help="Window score quantile on clean training windows. 0.02 keeps roughly the top 2%% clean windows removable.",
    )
    parser.add_argument(
        "--min-score-margin",
        type=float,
        default=0.0,
        help="Extra score required above the calibrated threshold before deleting a window.",
    )
    parser.add_argument(
        "--min-prob-gain",
        type=float,
        default=0.02,
        help="With guided localization, delete a window only if removal raises vulnerable probability by at least this amount.",
    )
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
