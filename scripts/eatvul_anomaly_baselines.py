import argparse
import csv
from pathlib import Path

import numpy as np
from scipy.sparse import hstack
from sklearn.covariance import EmpiricalCovariance
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.neighbors import LocalOutlierFactor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

from eatvul_defense import (
    BackgroundStats,
    DATASETS,
    detector_predict,
    handcrafted_features,
    load_jsonl,
    texts_labels,
    train_detector,
    train_target,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "eatvul_anomaly_baselines"


def lodo_items(name):
    clean_items = []
    adv_items = []
    for other, paths in DATASETS.items():
        if other == name:
            continue
        clean_items.extend(load_jsonl(paths["test"]))
        adv_items.extend(load_jsonl(paths["adv"]))
    return clean_items, adv_items


def fit_feature_pipeline(train_texts, max_features, n_components):
    vectorizer = TfidfVectorizer(
        tokenizer=str.split,
        preprocessor=None,
        token_pattern=None,
        ngram_range=(1, 2),
        min_df=2,
        max_features=max_features,
        sublinear_tf=True,
    )
    x_text = vectorizer.fit_transform(train_texts)
    usable_components = max(2, min(n_components, x_text.shape[0] - 1, x_text.shape[1] - 1))
    return vectorizer, TruncatedSVD(n_components=usable_components, random_state=7), StandardScaler()


def transform_features(pipeline, texts, background, fit=False):
    vectorizer, svd, scaler = pipeline
    x_text = vectorizer.transform(texts)
    x_hand = handcrafted_features(texts, background)
    x_sparse = hstack([x_text, x_hand])
    if fit:
        x = svd.fit_transform(x_sparse)
        return scaler.fit_transform(x)
    x = svd.transform(x_sparse)
    return scaler.transform(x)


class MahalanobisDetector:
    def __init__(self):
        self.model = EmpiricalCovariance(assume_centered=False)

    def fit(self, x):
        self.model.fit(x)
        return self

    def score(self, x):
        return self.model.mahalanobis(x)


def fit_baselines(x_train):
    n_neighbors = max(2, min(20, len(x_train) - 1))
    models = {
        "Isolation Forest": IsolationForest(n_estimators=200, random_state=7, n_jobs=-1),
        "One-Class SVM": OneClassSVM(kernel="rbf", gamma="scale", nu=0.10),
        "Local Outlier Factor": LocalOutlierFactor(n_neighbors=n_neighbors, novelty=True, contamination=0.10),
        "Mahalanobis": MahalanobisDetector(),
    }
    for model in models.values():
        model.fit(x_train)
    return models


def anomaly_scores(model, x):
    if isinstance(model, MahalanobisDetector):
        return model.score(x)
    if hasattr(model, "score_samples"):
        return -model.score_samples(x)
    return -model.decision_function(x)


def gate_row(name, target, clean_texts, clean_y, adv_texts, adv_pred, clean_items_lodo, adv_items_lodo, fpr):
    background = BackgroundStats([item["func"] for item in clean_items_lodo])
    detector = train_detector(clean_items_lodo, adv_items_lodo, background)
    clean_scores, _ = detector_predict(detector, clean_texts, background)
    adv_scores, _ = detector_predict(detector, adv_texts, background)
    clean_non_vul = clean_scores[clean_y == 0]
    threshold = float(np.quantile(clean_non_vul, 1.0 - fpr)) if len(clean_non_vul) else 0.5
    clean_flag = clean_scores >= threshold
    adv_flag = adv_scores >= threshold
    defended_pred = adv_pred.copy()
    defended_pred[adv_flag] = 1
    return build_row(name, "Supervised Gate", clean_y, target.predict(clean_texts), adv_pred, defended_pred, adv_flag, clean_flag, fpr)


def build_row(name, method, clean_y, clean_pred, adv_pred, defended_pred, adv_flag, clean_flag, fpr):
    base_asr = float(np.mean(adv_pred == 0))
    defended_asr = float(np.mean(defended_pred == 0))
    return {
        "dataset": name,
        "method": method,
        "target_clean_f1": f1_score(clean_y, clean_pred, zero_division=0),
        "baseline_asr": base_asr,
        "defended_asr": defended_asr,
        "asr_reduction": base_asr - defended_asr,
        "adv_recall": float(np.mean(adv_flag)),
        "clean_non_vul_fpr": float(np.mean(clean_flag[clean_y == 0])) if np.any(clean_y == 0) else 0.0,
        "calibration_fpr": fpr,
    }


def evaluate_dataset(name, args):
    paths = DATASETS[name]
    train_items = load_jsonl(paths["train"])
    test_items = load_jsonl(paths["test"])
    adv_items = load_jsonl(paths["adv"])
    clean_texts, clean_y = texts_labels(test_items)
    adv_texts, _ = texts_labels(adv_items)

    target = train_target(train_items)
    clean_pred = target.predict(clean_texts)
    adv_pred = target.predict(adv_texts)

    clean_items_lodo, adv_items_lodo = lodo_items(name)
    rows = [gate_row(name, target, clean_texts, clean_y, adv_texts, adv_pred, clean_items_lodo, adv_items_lodo, args.fpr)]

    background = BackgroundStats([item["func"] for item in clean_items_lodo])
    train_texts = [item["func"] for item in clean_items_lodo]
    pipeline = fit_feature_pipeline(train_texts, args.max_features, args.svd_components)
    x_train = transform_features(pipeline, train_texts, background, fit=True)
    x_clean = transform_features(pipeline, clean_texts, background)
    x_adv = transform_features(pipeline, adv_texts, background)
    models = fit_baselines(x_train)

    for method, model in models.items():
        clean_scores = anomaly_scores(model, x_clean)
        adv_scores = anomaly_scores(model, x_adv)
        clean_non_vul = clean_scores[clean_y == 0]
        threshold = float(np.quantile(clean_non_vul, 1.0 - args.fpr)) if len(clean_non_vul) else float(np.max(clean_scores))
        clean_flag = clean_scores >= threshold
        adv_flag = adv_scores >= threshold
        defended_pred = adv_pred.copy()
        defended_pred[adv_flag] = 1
        rows.append(build_row(name, method, clean_y, clean_pred, adv_pred, defended_pred, adv_flag, clean_flag, args.fpr))
    return rows


def run(args):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in args.datasets:
        rows.extend(evaluate_dataset(name, args))
    out_csv = OUT_DIR / "anomaly_baseline_results.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved: {out_csv}")
    for row in rows:
        print(
            row["dataset"],
            row["method"],
            f"asr={row['defended_asr']:.3f}",
            f"recall={row['adv_recall']:.3f}",
            f"fpr={row['clean_non_vul_fpr']:.3f}",
        )


def main():
    parser = argparse.ArgumentParser(description="Classic anomaly-detection baselines for EaTVul AST-token defenses.")
    parser.add_argument("--datasets", nargs="+", choices=DATASETS.keys(), default=["openssl", "asterisk"])
    parser.add_argument("--fpr", type=float, default=0.10)
    parser.add_argument("--max-features", type=int, default=12000)
    parser.add_argument("--svd-components", type=int, default=24)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
