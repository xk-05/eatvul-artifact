import argparse
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.sparse import hstack
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Code and Dataset" / "file" / "data"
OUT_DIR = ROOT / "results" / "eatvul_defense"

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

CONTROL_TOKENS = {"if", "else", "for", "while", "switch", "case", "goto", "return", "break", "continue"}
IO_TOKENS = {"printf", "fprintf", "sprintf", "snprintf", "scanf", "fopen", "fclose", "fgets", "read", "write"}
TYPE_TOKENS = {"int", "char", "long", "short", "float", "double", "void", "struct", "enum", "const", "unsigned", "static"}
AST_STRUCT_TOKENS = {
    "FUNCTION_DEF",
    "RETURN_TYPE",
    "TYPE",
    "TYPE_NAME",
    "NAME",
    "LEAF_NODE",
    "FUNCTION_NAME",
    "PARAMETER_LIST",
    "PARAMETER_DECL",
    "STATEMENTS",
    "SIMPLE_DECL",
    "VAR_DECL",
    "EXPR_STATEMENT",
    "EXPR",
    "FUNCTION_CALL",
    "SELECTION",
    "ITERATION",
    "CONDITION",
    "JUMP_STATEMENT",
}


def load_jsonl(path):
    items = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def texts_labels(items):
    return [item["func"] for item in items], np.array([int(item["target"]) for item in items])


def vulnerable_only(items):
    return [item for item in items if int(item["target"]) == 1]


class BackgroundStats:
    def __init__(self, texts):
        self.unigram = Counter()
        self.bigram = Counter()
        self.total = 0
        for text in texts:
            tokens = text.split()
            self.unigram.update(tokens)
            self.bigram.update(zip(tokens, tokens[1:]))
            self.total += len(tokens)
        self.vocab_size = max(1, len(self.unigram))
        self.rare = {tok for tok, count in self.unigram.items() if count <= 2}

    def token_idf(self, token):
        return math.log((self.total + self.vocab_size) / (self.unigram.get(token, 0) + 1.0))

    def bigram_nll(self, tokens):
        if len(tokens) < 2:
            return 0.0
        total = 0.0
        for left, right in zip(tokens, tokens[1:]):
            prob = (self.bigram.get((left, right), 0) + 0.1) / (self.unigram.get(left, 0) + 0.1 * self.vocab_size)
            total -= math.log(prob)
        return total / (len(tokens) - 1)


def name_like(token):
    if token in AST_STRUCT_TOKENS or token in CONTROL_TOKENS or token in TYPE_TOKENS:
        return False
    if token.isdigit():
        return False
    return bool(re.search(r"[A-Za-z_]", token))


def longest_run(tokens, selected):
    best = 0
    current = 0
    for tok in tokens:
        if tok in selected:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def handcrafted_features(texts, background):
    rows = []
    for text in texts:
        tokens = text.split()
        length = max(1, len(tokens))
        counts = Counter(tokens)
        unique = len(counts)
        idfs = [background.token_idf(tok) for tok in tokens[:20000]]
        numeric = [int(tok) for tok in tokens if tok.isdigit()]
        names = [tok for tok in tokens if name_like(tok)]
        name_counter = Counter(names)
        repeated_names = sum(1 for tok, count in name_counter.items() if count >= 3)

        rare_count = sum(1 for tok in tokens if tok in background.rare or background.unigram.get(tok, 0) == 0)
        unseen_count = sum(1 for tok in tokens if background.unigram.get(tok, 0) == 0)
        control_count = sum(1 for tok in tokens if tok in CONTROL_TOKENS)
        io_count = sum(1 for tok in tokens if tok in IO_TOKENS)
        type_count = sum(1 for tok in tokens if tok in TYPE_TOKENS)
        struct_count = sum(1 for tok in tokens if tok in AST_STRUCT_TOKENS)

        row = [
            math.log1p(length),
            unique / length,
            rare_count / length,
            unseen_count / length,
            float(np.mean(idfs)) if idfs else 0.0,
            float(np.percentile(idfs, 95)) if idfs else 0.0,
            background.bigram_nll(tokens[:20000]),
            len(names) / length,
            repeated_names / max(1, len(name_counter)),
            sum("_" in tok for tok in names) / max(1, len(names)),
            sum(any(ch.isdigit() for ch in tok) for tok in names) / max(1, len(names)),
            control_count / length,
            io_count / length,
            type_count / length,
            struct_count / length,
            tokens.count("LEAF_NODE") / length,
            tokens.count("FUNCTION_DEF") / length,
            tokens.count("SELECTION") / length,
            tokens.count("ITERATION") / length,
            max(numeric) if numeric else 0,
            float(np.mean(numeric)) if numeric else 0.0,
            longest_run(tokens, AST_STRUCT_TOKENS) / length,
            longest_run(tokens, CONTROL_TOKENS) / length,
        ]
        rows.append(row)
    return np.asarray(rows, dtype=np.float32)


def train_target(train_items):
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
                    min_df=2,
                    max_features=50000,
                    sublinear_tf=True,
                ),
            ),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", n_jobs=1)),
        ]
    )
    model.fit(texts, labels)
    return model


def train_detector(train_items, adv_items, background):
    clean_neg = vulnerable_only(train_items)
    if len(clean_neg) < 20:
        clean_neg = train_items
    texts = [item["func"] for item in clean_neg] + [item["func"] for item in adv_items]
    labels = np.array([0] * len(clean_neg) + [1] * len(adv_items))

    tfidf = TfidfVectorizer(
        tokenizer=str.split,
        preprocessor=None,
        token_pattern=None,
        ngram_range=(1, 2),
        min_df=2,
        max_features=30000,
        sublinear_tf=True,
    )
    x_text = tfidf.fit_transform(texts)
    x_hand = handcrafted_features(texts, background)
    scaler = StandardScaler()
    x_hand = scaler.fit_transform(x_hand)
    x = hstack([x_text, x_hand])

    clf = RandomForestClassifier(
        n_estimators=120,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=7,
        n_jobs=-1,
    )
    clf.fit(x, labels)
    return tfidf, scaler, clf


def detector_predict(detector, texts, background):
    tfidf, scaler, clf = detector
    x_text = tfidf.transform(texts)
    x_hand = scaler.transform(handcrafted_features(texts, background))
    x = hstack([x_text, x_hand])
    probs = clf.predict_proba(x)[:, 1]
    return probs, (probs >= 0.5).astype(int)


def evaluate_dataset(name, args):
    paths = DATASETS[name]
    train_items = load_jsonl(paths["train"])
    test_items = load_jsonl(paths["test"])
    adv_items = load_jsonl(paths["adv"])

    background = BackgroundStats([item["func"] for item in train_items])
    target = train_target(train_items)

    clean_texts, clean_y = texts_labels(test_items)
    adv_texts, _ = texts_labels(adv_items)
    clean_pred = target.predict(clean_texts)
    adv_pred = target.predict(adv_texts)

    clean_vul_items = vulnerable_only(test_items)
    clean_vul_texts = [item["func"] for item in clean_vul_items]

    detector_train_items = []
    detector_adv_items = []
    if args.leave_one_dataset_out:
        for other, other_paths in DATASETS.items():
            if other == name:
                continue
            detector_train_items.extend(load_jsonl(other_paths["test"]))
            detector_adv_items.extend(load_jsonl(other_paths["adv"]))
    else:
        detector_train_items = test_items
        detector_adv_items = adv_items

    detector_background = BackgroundStats([item["func"] for item in detector_train_items])
    detector = train_detector(detector_train_items, detector_adv_items, detector_background)

    adv_det_prob, adv_detected_default = detector_predict(detector, adv_texts, detector_background)
    clean_all_det_prob, clean_all_detected_default = detector_predict(detector, clean_texts, detector_background)
    clean_det_prob, clean_detected_default = detector_predict(detector, clean_vul_texts, detector_background)

    threshold = 0.5
    if args.calibrate_clean_fpr is not None:
        clean_non_vul_scores = clean_all_det_prob[clean_y == 0]
        if len(clean_non_vul_scores):
            threshold = float(np.quantile(clean_non_vul_scores, 1.0 - args.calibrate_clean_fpr))

    adv_detected = (adv_det_prob >= threshold).astype(int)
    clean_all_detected = (clean_all_det_prob >= threshold).astype(int)
    clean_detected = (clean_det_prob >= threshold).astype(int)

    baseline_bypass = int(np.sum(adv_pred == 0))
    baseline_asr = baseline_bypass / len(adv_items)

    defended_pred = adv_pred.copy()
    defended_pred[adv_detected == 1] = 1
    defended_bypass = int(np.sum(defended_pred == 0))
    defended_asr = defended_bypass / len(adv_items)

    defended_clean_pred = clean_pred.copy()
    defended_clean_pred[clean_all_detected == 1] = 1
    defended_clean_f1 = f1_score(clean_y, defended_clean_pred, zero_division=0)
    detector_fpr_clean_non_vul = float(np.mean(clean_all_detected[clean_y == 0])) if np.any(clean_y == 0) else 0.0

    clean_acc = accuracy_score(clean_y, clean_pred)
    clean_f1 = f1_score(clean_y, clean_pred, zero_division=0)
    detector_recall = recall_score(np.ones(len(adv_detected)), adv_detected, zero_division=0)
    detector_fpr = float(np.mean(clean_detected)) if len(clean_detected) else 0.0
    detector_precision_eval_y = np.concatenate([np.zeros(len(clean_detected)), np.ones(len(adv_detected))])
    detector_precision_eval_pred = np.concatenate([clean_detected, adv_detected])
    detector_precision = precision_score(detector_precision_eval_y, detector_precision_eval_pred, zero_division=0)

    row = {
        "dataset": name,
        "target_clean_acc": clean_acc,
        "target_clean_f1": clean_f1,
        "defended_clean_f1": defended_clean_f1,
        "adv_samples": len(adv_items),
        "baseline_bypassed": baseline_bypass,
        "baseline_asr": baseline_asr,
        "threshold": threshold,
        "detector_recall_on_adv": detector_recall,
        "detector_fpr_on_clean_vul": detector_fpr,
        "detector_fpr_on_clean_non_vul": detector_fpr_clean_non_vul,
        "detector_precision_adv_vs_clean_vul": detector_precision,
        "defended_bypassed": defended_bypass,
        "defended_asr": defended_asr,
        "asr_reduction": baseline_asr - defended_asr,
        "mean_adv_detector_score": float(np.mean(adv_det_prob)),
        "mean_clean_vul_detector_score": float(np.mean(clean_det_prob)) if len(clean_det_prob) else 0.0,
    }
    return row


def fmt(value):
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def print_markdown_table(rows):
    headers = [
        "dataset",
        "target_clean_f1",
        "defended_clean_f1",
        "baseline_asr",
        "detector_recall_on_adv",
        "detector_fpr_on_clean_non_vul",
        "defended_asr",
        "asr_reduction",
    ]
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        print("| " + " | ".join(fmt(row[h]) for h in headers) + " |")


def run(args):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    names = args.datasets or list(DATASETS)
    rows = [evaluate_dataset(name, args) for name in names]

    mode = "lodo" if args.leave_one_dataset_out else "in_dataset"
    suffix = "default" if args.calibrate_clean_fpr is None else f"calib_fpr_{args.calibrate_clean_fpr:g}"
    out_csv = OUT_DIR / f"{mode}_{suffix}_results.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print_markdown_table(rows)
    print(f"\nSaved: {out_csv}")


def main():
    parser = argparse.ArgumentParser(description="Detect and defend against EaTVul-style inserted benign snippets.")
    parser.add_argument("--datasets", nargs="*", choices=DATASETS.keys())
    parser.add_argument(
        "--leave-one-dataset-out",
        action="store_true",
        help="Train the insertion detector on other datasets and test on the selected dataset.",
    )
    parser.add_argument(
        "--calibrate-clean-fpr",
        type=float,
        default=None,
        help="Set detector threshold from clean non-vulnerable validation scores, e.g. 0.10 for about 10%% clean false positives.",
    )
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
