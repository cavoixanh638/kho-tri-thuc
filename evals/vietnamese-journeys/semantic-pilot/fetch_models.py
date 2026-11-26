"""Fetch and verify the two public ONNX bundles used by this Windows experiment."""

import argparse
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests


MODELS = {
    "embedding": (
        "AITeamVN/Vietnamese_Embedding_v2", "18b44161e041bf1d3a333ab5144b5b7b93f914d2",
        ("tokenizer.json", "config.json", "modules.json", "1_Pooling/config.json", "onnx/model.onnx", "onnx/model.onnx_data"),
    ),
    "reranker": (
        "onnx-community/bge-reranker-v2-m3-ONNX", "6f5ff65298512715a1e669753bc754d2bc8f367b",
        ("tokenizer.json", "config.json", "onnx/model_quantized.onnx"),
    ),
}


def matches_file(path, info):
    if not path.exists() or path.stat().st_size != info["size"]:
        return False
    lfs = info.get("lfs")
    digest = hashlib.sha256() if lfs else hashlib.sha1(f"blob {info['size']}\0".encode())
    with path.open("rb") as source:
        for block in iter(lambda: source.read(2**20), b""):
            digest.update(block)
    return digest.hexdigest() == (lfs["sha256"] if lfs else info["blobId"])


def download(root, name):
    repo, revision, filenames = MODELS[name]
    base = "https://huggingface.co"
    with requests.Session() as session:
        response = session.get(f"{base}/api/models/{repo}/revision/{revision}", params={"blobs": "true"}, timeout=30)
        response.raise_for_status()
        metadata = response.json()
        if metadata["sha"] != revision:
            raise ValueError("Model revision mismatch")
        files = {row["rfilename"]: row for row in metadata["siblings"]}
        for filename in filenames:
            info = files[filename]
            path = root / name / filename
            if matches_file(path, info):
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            partial = path.with_suffix(path.suffix + ".part")
            url = f"{base}/{repo}/resolve/{revision}/{filename}"
            print(f"Fetching {name}/{filename} ({info['size']:,} bytes)", flush=True)
            for attempt in range(4):
                if matches_file(partial, info):
                    break
                offset = partial.stat().st_size if partial.exists() else 0
                if offset >= info["size"]:
                    offset = 0
                try:
                    headers = {"Range": f"bytes={offset}-"} if offset else {}
                    with session.get(url, headers=headers, stream=True, timeout=(20, 90)) as data:
                        data.raise_for_status()
                        append = offset > 0 and data.status_code == 206
                        if append and not data.headers.get("Content-Range", "").startswith(f"bytes {offset}-"):
                            raise ValueError("Unexpected byte range")
                        with partial.open("ab" if append else "wb") as output:
                            for block in data.iter_content(2**20):
                                output.write(block)
                except requests.RequestException as error:
                    if attempt == 3:
                        raise RuntimeError(f"Could not download {name}/{filename} ({type(error).__name__})") from None
                    time.sleep(2 ** attempt)
            if not matches_file(partial, info):
                raise ValueError(f"Checksum mismatch for {name}/{filename}")
            partial.replace(path)
    print(f"Verified {name} at {revision}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True, help="Local model cache outside the repository")
    args = parser.parse_args()
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda name: download(args.directory, name), MODELS))
