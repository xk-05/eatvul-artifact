import argparse
from pathlib import Path

import requests


DEFAULT_FILES = [
    "config.json",
    "vocab.json",
    "merges.txt",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "pytorch_model.bin",
]


def download(repo, out_dir, files):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name in files:
        url = f"https://huggingface.co/{repo}/resolve/main/{name}"
        dest = out / name
        if dest.exists() and dest.stat().st_size > 0:
            print(f"skip {dest} ({dest.stat().st_size} bytes)")
            continue
        print(f"download {url}")
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            tmp = dest.with_suffix(dest.suffix + ".part")
            with tmp.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
            tmp.replace(dest)
        print(f"saved {dest} ({dest.stat().st_size} bytes)")


def main():
    parser = argparse.ArgumentParser(description="Download selected Hugging Face model files with requests.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--files", nargs="*", default=DEFAULT_FILES)
    args = parser.parse_args()
    download(args.repo, args.out_dir, args.files)


if __name__ == "__main__":
    main()
