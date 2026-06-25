from pathlib import Path

import requests


BASE_URL = "https://hf-mirror.com/microsoft/codebert-base/resolve/main/pytorch_model.bin"
OUT_DIR = Path(__file__).resolve().parents[1] / "models" / "codebert-base"
RANGES = [
    ("pytorch_model.bin.part13.0.tail", 409251691, 412926272),
    ("pytorch_model.bin.part13.1.tail", 417493313, 420717334),
    ("pytorch_model.bin.part13.2.tail", 426537751, 428508396),
    ("pytorch_model.bin.part13.3.tail", 432002285, 436299457),
]


def get_session():
    session = requests.Session()
    session.trust_env = False
    return session


def download(name, start, end):
    path = OUT_DIR / name
    expected = end - start + 1
    if path.exists() and path.stat().st_size == expected:
        print(f"ready: {name}")
        return
    headers = {"Range": f"bytes={start}-{end}"}
    last_error = None
    for _ in range(20):
        try:
            session = get_session()
            with session.get(BASE_URL, headers=headers, stream=True, timeout=(15, 30)) as response:
                response.raise_for_status()
                tmp = path.with_suffix(path.suffix + ".tmp")
                with tmp.open("wb") as output:
                    for chunk in response.iter_content(chunk_size=256 * 1024):
                        if chunk:
                            output.write(chunk)
                if tmp.stat().st_size != expected:
                    raise IOError(f"{name}: expected {expected}, got {tmp.stat().st_size}")
                tmp.replace(path)
                print(f"ready: {name}")
                return
        except Exception as exc:
            last_error = exc
    raise last_error


def main():
    for item in RANGES:
        download(*item)


if __name__ == "__main__":
    main()
