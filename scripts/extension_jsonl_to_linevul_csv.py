import argparse
import json
from pathlib import Path

import pandas as pd


def read_jsonl(path):
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def convert(in_path, out_path):
    rows = []
    for item in read_jsonl(in_path):
        rows.append(
            {
                "index": item.get("idx", len(rows)),
                "processed_func": item["func"],
                "target": int(item.get("target", 0)),
                "flaw_line": "",
                "flaw_line_index": "",
                "project": item.get("project", ""),
            }
        )
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"saved {out} rows={len(rows)}")


def main():
    parser = argparse.ArgumentParser(description="Convert extension JSONL to the CSV schema expected by LineVul.")
    parser.add_argument("--in-jsonl", required=True)
    parser.add_argument("--out-csv", required=True)
    args = parser.parse_args()
    convert(args.in_jsonl, args.out_csv)


if __name__ == "__main__":
    main()
