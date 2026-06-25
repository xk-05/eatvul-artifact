from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests


BASE_URL = "https://hf-mirror.com/microsoft/codebert-base/resolve/main"
OUT_DIR = Path(__file__).resolve().parents[1] / "models" / "codebert-base"
FILES = {
    "config.json": None,
    "vocab.json": None,
    "merges.txt": None,
    "tokenizer_config.json": None,
    "special_tokens_map.json": None,
    "pytorch_model.bin": 498_627_950,
}


def session():
    sess = requests.Session()
    sess.trust_env = False
    return sess


def download_file(name):
    path = OUT_DIR / name
    expected = FILES[name]
    if expected and path.exists() and path.stat().st_size == expected:
        return
    url = f"{BASE_URL}/{name}"
    sess = session()
    with sess.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("wb") as handle:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        tmp.replace(path)


def download_range(name, idx, start, end):
    path = OUT_DIR / f"{name}.part{idx:02d}"
    expected = end - start + 1
    if path.exists() and path.stat().st_size == expected:
        return
    url = f"{BASE_URL}/{name}"
    headers = {"Range": f"bytes={start}-{end}"}
    last_error = None
    for _ in range(8):
        try:
            sess = session()
            with sess.get(url, headers=headers, stream=True, timeout=60) as resp:
                resp.raise_for_status()
                tmp = path.with_suffix(path.suffix + ".tmp")
                with tmp.open("wb") as handle:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            handle.write(chunk)
                if tmp.stat().st_size != expected:
                    raise IOError(f"{path.name}: expected {expected}, got {tmp.stat().st_size}")
                tmp.replace(path)
                return
        except Exception as exc:
            last_error = exc
    raise last_error


def download_large(name, total_size, workers=16):
    path = OUT_DIR / name
    if path.exists() and path.stat().st_size == total_size:
        return

    chunk_size = (total_size + workers - 1) // workers
    jobs = []
    for idx in range(workers):
        start = idx * chunk_size
        end = min(total_size - 1, ((idx + 1) * chunk_size) - 1)
        jobs.append((idx, start, end))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(download_range, name, idx, start, end) for idx, start, end in jobs]
        for future in as_completed(futures):
            future.result()

    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as output:
        for idx, _, _ in jobs:
            part = OUT_DIR / f"{name}.part{idx:02d}"
            with part.open("rb") as handle:
                output.write(handle.read())
    if tmp.stat().st_size != total_size:
        raise IOError(f"{name}: expected {total_size}, got {tmp.stat().st_size}")
    tmp.replace(path)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, expected in FILES.items():
        if expected:
            download_large(name, expected)
        else:
            download_file(name)
        print(f"ready: {name}")


if __name__ == "__main__":
    main()
