import argparse
import json
import random
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "data" / "linevul_bigvul" / "test.csv"
DEFAULT_OUT = ROOT / "data" / "extension_projects"
DEFAULT_PROJECTS = ["chrome", "linux", "android", "tcpdump", "php-src", "imagemagick", "ffmpeg"]
PROJECT_ALIASES = {
    "chrome": ["chrome", "chromium"],
    "linux": ["linux"],
    "android": ["android"],
    "tcpdump": ["tcpdump"],
    "php-src": ["php-src", "php_src"],
    "imagemagick": ["imagemagick", "image-magick"],
    "ffmpeg": ["ffmpeg"],
}


def project_key(value, projects):
    text = str(value).lower()
    for project in projects:
        aliases = PROJECT_ALIASES.get(project, [project])
        if any(alias in text for alias in aliases):
            return project
    return None


def iter_project_rows(csv_path, projects, chunksize):
    usecols = [
        "index",
        "project",
        "processed_func",
        "target",
        "file_name",
        "commit_id",
        "CVE ID",
    ]
    wanted = set(projects)
    for chunk in pd.read_csv(csv_path, usecols=usecols, chunksize=chunksize):
        chunk = chunk.dropna(subset=["processed_func", "target", "project"])
        for row in chunk.to_dict("records"):
            key = project_key(row["project"], wanted)
            if key not in wanted:
                continue
            func = str(row["processed_func"]).strip()
            if not func:
                continue
            yield {
                "idx": int(row.get("index", 0)),
                "project": key,
                "func": func,
                "target": int(row["target"]),
                "source_path": "" if pd.isna(row.get("file_name")) else str(row.get("file_name")),
                "commit": "" if pd.isna(row.get("commit_id")) else str(row.get("commit_id")),
                "cve": "" if pd.isna(row.get("CVE ID")) else str(row.get("CVE ID")),
                "data_source": "linevul_bigvul_test_csv",
            }


def stratified_split(rows, train_frac, seed, max_per_project=None):
    rng = random.Random(seed)
    by_label = {0: [], 1: []}
    for row in rows:
        by_label[int(row["target"])].append(row)
    chosen = []
    for label, values in by_label.items():
        values = list(values)
        rng.shuffle(values)
        if max_per_project is not None:
            values = values[:max_per_project]
        chosen.extend(values)
    rng.shuffle(chosen)

    train = []
    test = []
    for label in [0, 1]:
        values = [row for row in chosen if int(row["target"]) == label]
        cut = max(1, int(len(values) * train_frac)) if len(values) > 1 else len(values)
        train.extend(values[:cut])
        test.extend(values[cut:])
    rng.shuffle(train)
    rng.shuffle(test)
    return train, test


def write_jsonl(path, rows, split):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for pos, row in enumerate(rows):
            out = dict(row)
            out["idx"] = int(out.get("idx", pos))
            out["split"] = split
            handle.write(json.dumps(out, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Prepare multi-project extension JSONL from LineVul Big-Vul CSV.")
    parser.add_argument("--csv", default=str(DEFAULT_CSV))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--projects", nargs="+", default=DEFAULT_PROJECTS)
    parser.add_argument("--train-frac", type=float, default=0.70)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--chunksize", type=int, default=50000)
    parser.add_argument("--max-per-label", type=int)
    args = parser.parse_args()

    rows_by_project = {project: [] for project in args.projects}
    for row in iter_project_rows(Path(args.csv), args.projects, args.chunksize):
        rows_by_project[row["project"]].append(row)

    summary = []
    for project, rows in rows_by_project.items():
        train, test = stratified_split(rows, args.train_frac, args.seed, args.max_per_label)
        out_base = Path(args.out_dir) / project
        write_jsonl(out_base / "train.jsonl", train, "train")
        write_jsonl(out_base / "test.jsonl", test, "test")
        # adv.jsonl is intentionally seeded with vulnerable test functions; the
        # extension harness can also generate adaptive attacks from the clean test set.
        adv = [row for row in test if int(row["target"]) == 1]
        write_jsonl(out_base / "adv.jsonl", adv, "adv")
        evidence_role = "small_case" if project == "ffmpeg" or len(adv) < 10 else "generalization"
        summary.append(
            {
                "project": project,
                "total": len(rows),
                "train": len(train),
                "test": len(test),
                "adv_seed": len(adv),
                "train_vul": sum(1 for row in train if int(row["target"]) == 1),
                "test_vul": len(adv),
                "evidence_role": evidence_role,
            }
        )

    summary_path = Path(args.out_dir) / "linevul_bigvul_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
