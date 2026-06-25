import argparse
import csv
import random
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score

from eatvul_defense import BackgroundStats, DATASETS, detector_predict, load_jsonl, texts_labels, train_detector


ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models" / "codebert-base"
OUT_DIR = ROOT / "results" / "neural_target_gate"


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)


def balanced_subset(items, max_per_class, seed):
    rng = random.Random(seed)
    by_label = {0: [], 1: []}
    for item in items:
        by_label[int(item["target"])].append(item)
    chosen = []
    for label in [0, 1]:
        values = list(by_label[label])
        rng.shuffle(values)
        chosen.extend(values[:max_per_class])
    rng.shuffle(chosen)
    return chosen


def lodo_gate(name, clean_texts, clean_y, adv_texts, fpr):
    train_items = []
    adv_items = []
    for other, paths in DATASETS.items():
        if other == name:
            continue
        train_items.extend(load_jsonl(paths["test"]))
        adv_items.extend(load_jsonl(paths["adv"]))
    background = BackgroundStats([item["func"] for item in train_items])
    detector = train_detector(train_items, adv_items, background)
    clean_scores, _ = detector_predict(detector, clean_texts, background)
    adv_scores, _ = detector_predict(detector, adv_texts, background)
    clean_non_vul = clean_scores[clean_y == 0]
    threshold = float(np.quantile(clean_non_vul, 1.0 - fpr)) if len(clean_non_vul) else 0.5
    return clean_scores >= threshold, adv_scores >= threshold, threshold, clean_scores, adv_scores


def row_for_predictions(name, victim, train_n, clean_y, clean_pred, adv_pred, clean_flag, adv_flag, threshold):
    bypass_mask = adv_pred == 0
    bypassed = int(np.sum(bypass_mask))
    recall_on_bypass = float(np.mean(adv_flag[bypass_mask])) if bypassed else 0.0
    clean_non_vul_mask = clean_y == 0
    return {
        "dataset": name,
        "victim": victim,
        "train_n": train_n,
        "clean_test_n": len(clean_y),
        "adv_n": len(adv_pred),
        "clean_acc": accuracy_score(clean_y, clean_pred),
        "clean_f1": f1_score(clean_y, clean_pred, zero_division=0),
        "adv_bypassed": bypassed,
        "adv_asr": float(np.mean(bypass_mask)),
        "gate_threshold": threshold,
        "gate_recall_all_adv": float(np.mean(adv_flag)),
        "gate_recall_on_neural_bypassed": recall_on_bypass,
        "clean_non_vul_fpr": float(np.mean(clean_flag[clean_non_vul_mask])) if np.any(clean_non_vul_mask) else 0.0,
    }


def run_bilstm(name, train_items, clean_items, adv_items, args):
    import tensorflow as tf
    from tensorflow.keras import layers, models
    from tensorflow.keras.preprocessing.sequence import pad_sequences
    from tensorflow.keras.preprocessing.text import Tokenizer

    tf.keras.utils.set_random_seed(args.seed)
    train_texts, train_y = texts_labels(train_items)
    clean_texts, clean_y = texts_labels(clean_items)
    adv_texts, _ = texts_labels(adv_items)

    tokenizer = Tokenizer(num_words=args.vocab_size, filters="", lower=False, split=" ", oov_token="<UNK>")
    tokenizer.fit_on_texts(train_texts)
    x_train = pad_sequences(tokenizer.texts_to_sequences(train_texts), maxlen=args.max_len, padding="post", truncating="post")
    x_clean = pad_sequences(tokenizer.texts_to_sequences(clean_texts), maxlen=args.max_len, padding="post", truncating="post")
    x_adv = pad_sequences(tokenizer.texts_to_sequences(adv_texts), maxlen=args.max_len, padding="post", truncating="post")
    vocab = min(args.vocab_size, len(tokenizer.word_index) + 1)

    inputs = layers.Input(shape=(args.max_len,))
    x = layers.Embedding(vocab, args.embedding_dim, mask_zero=True)(inputs)
    x = layers.Bidirectional(layers.LSTM(args.lstm_units, return_sequences=True))(x)
    score = layers.Dense(1, activation="tanh")(x)
    score = layers.Flatten()(score)
    weight = layers.Activation("softmax", name="attention_vec")(score)
    context = layers.Dot(axes=1)([x, weight])
    x = layers.Dense(32, activation="relu")(context)
    x = layers.Dropout(0.20)(x)
    outputs = layers.Dense(1, activation="sigmoid")(x)
    model = models.Model(inputs, outputs, name="jsonl_bilstm_attention")
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    model.fit(x_train, train_y, epochs=args.bilstm_epochs, batch_size=args.batch_size, validation_split=0.10, verbose=0)

    clean_prob = model.predict(x_clean, batch_size=args.batch_size, verbose=0).reshape(-1)
    adv_prob = model.predict(x_adv, batch_size=args.batch_size, verbose=0).reshape(-1)
    return (clean_prob >= 0.5).astype(int), (adv_prob >= 0.5).astype(int)


def run_codebert(name, train_items, clean_items, adv_items, args):
    import torch
    from torch.utils.data import DataLoader, Dataset
    from transformers import RobertaForSequenceClassification, RobertaTokenizer

    torch.manual_seed(args.seed)
    tokenizer = RobertaTokenizer.from_pretrained(str(MODEL_DIR), local_files_only=True)
    model = RobertaForSequenceClassification.from_pretrained(str(MODEL_DIR), num_labels=2, local_files_only=True)
    model.train()
    device = torch.device("cpu")
    model.to(device)

    class JsonlDataset(Dataset):
        def __init__(self, items):
            self.items = items

        def __len__(self):
            return len(self.items)

        def __getitem__(self, idx):
            item = self.items[idx]
            enc = tokenizer(
                " ".join(item["func"].split()),
                max_length=args.codebert_len,
                truncation=True,
                padding="max_length",
                return_tensors="pt",
            )
            return {
                "input_ids": enc["input_ids"].squeeze(0),
                "attention_mask": enc["attention_mask"].squeeze(0),
                "labels": torch.tensor(int(item["target"]), dtype=torch.long),
            }

    train_loader = DataLoader(JsonlDataset(train_items), batch_size=args.codebert_batch, shuffle=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.codebert_lr)
    for _epoch in range(args.codebert_epochs):
        for batch in train_loader:
            optimizer.zero_grad()
            batch = {key: value.to(device) for key, value in batch.items()}
            loss = model(**batch).loss
            loss.backward()
            optimizer.step()

    def predict(items):
        loader = DataLoader(JsonlDataset(items), batch_size=args.codebert_batch, shuffle=False)
        preds = []
        model.eval()
        with torch.no_grad():
            for batch in loader:
                labels = batch.pop("labels")
                batch = {key: value.to(device) for key, value in batch.items()}
                logits = model(**batch).logits
                preds.extend(torch.argmax(logits, dim=1).cpu().numpy().tolist())
        return np.asarray(preds, dtype=int)

    return predict(clean_items), predict(adv_items)


def evaluate_dataset(name, args):
    paths = DATASETS[name]
    train_all = load_jsonl(paths["train"])
    clean_items = load_jsonl(paths["test"])
    adv_items = load_jsonl(paths["adv"])
    train_items = balanced_subset(train_all, args.max_train_per_class, args.seed)
    clean_texts, clean_y = texts_labels(clean_items)
    adv_texts, _ = texts_labels(adv_items)
    clean_flag, adv_flag, threshold, _clean_scores, _adv_scores = lodo_gate(name, clean_texts, clean_y, adv_texts, args.gate_fpr)

    rows = []
    if "bilstm" in args.victims:
        clean_pred, adv_pred = run_bilstm(name, train_items, clean_items, adv_items, args)
        rows.append(row_for_predictions(name, "BiLSTM-attention", len(train_items), clean_y, clean_pred, adv_pred, clean_flag, adv_flag, threshold))
    if "codebert" in args.victims:
        clean_pred, adv_pred = run_codebert(name, train_items, clean_items, adv_items, args)
        rows.append(row_for_predictions(name, "CodeBERT-base", len(train_items), clean_y, clean_pred, adv_pred, clean_flag, adv_flag, threshold))
    return rows


def run(args):
    set_seed(args.seed)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUT_DIR / "neural_target_gate_results.csv"
    rows = []
    if args.append_existing and out_csv.exists():
        with out_csv.open(newline="", encoding="utf-8") as handle:
            rows.extend(csv.DictReader(handle))
    for name in args.datasets:
        new_rows = evaluate_dataset(name, args)
        keys = {(row["dataset"], row["victim"]) for row in new_rows}
        rows = [row for row in rows if (row["dataset"], row["victim"]) not in keys]
        rows.extend(new_rows)
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved: {out_csv}")
    for row in rows:
        print(
            row["dataset"],
            row["victim"],
            f"clean_f1={float(row['clean_f1']):.3f}",
            f"asr={float(row['adv_asr']):.3f}",
            f"gate_bypass_recall={float(row['gate_recall_on_neural_bypassed']):.3f}",
        )


def main():
    parser = argparse.ArgumentParser(description="Neural target model check for the EaTVul sample-level gate.")
    parser.add_argument("--datasets", nargs="+", choices=DATASETS.keys(), default=["openssl", "asterisk"])
    parser.add_argument("--victims", nargs="+", choices=["bilstm", "codebert"], default=["bilstm", "codebert"])
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--gate-fpr", type=float, default=0.10)
    parser.add_argument("--max-train-per-class", type=int, default=80)
    parser.add_argument("--max-len", type=int, default=256)
    parser.add_argument("--vocab-size", type=int, default=20000)
    parser.add_argument("--embedding-dim", type=int, default=64)
    parser.add_argument("--lstm-units", type=int, default=32)
    parser.add_argument("--bilstm-epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--codebert-len", type=int, default=256)
    parser.add_argument("--codebert-batch", type=int, default=4)
    parser.add_argument("--codebert-epochs", type=int, default=1)
    parser.add_argument("--codebert-lr", type=float, default=2e-5)
    parser.add_argument("--append-existing", action="store_true")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
