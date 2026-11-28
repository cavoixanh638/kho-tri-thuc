"""Provision the pinned CPU reranker files before starting local search."""

import argparse
import hashlib
import os
import sys
from contextlib import suppress
from http.client import HTTPException
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

MODEL_NAME = "bge-reranker-v2-m3"
MODEL_REPOSITORY = "onnx-community/bge-reranker-v2-m3-ONNX"
MODEL_REVISION = "6f5ff65298512715a1e669753bc754d2bc8f367b"
MODEL_BASE_URL = f"https://huggingface.co/{MODEL_REPOSITORY}/resolve/{MODEL_REVISION}"
MODEL_FILES = {
    "config.json": (
        848,
        "122e922dcfed6503c8721e6fe1daf090340c3d95ca7f3aa3a72730b321a51cfd",
    ),
    "tokenizer.json": (
        17_082_900,
        "8bf8afbfd11306bd872018c53bfdf2e160a56f8edbcf49933324404791c148d3",
    ),
    "onnx/model_quantized.onnx": (
        570_727_094,
        "912fc1215c2dbff6499700534bd8d31253af01573861abbfc43afd1fab6cce5d",
    ),
}
CHUNK_BYTES = 1024 * 1024


def model_directory():
    """Resolve the same leaf directory for provisioning and Django."""
    configured = os.getenv("SEARCH_BGE_MODEL_DIR")
    if configured is not None:
        return Path(configured.strip()).expanduser() if configured.strip() else None
    if os.name == "nt":
        local_app_data = os.getenv("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
        return Path(local_app_data) / "KhoTriThuc" / "models" / MODEL_NAME
    return Path("/var/lib/kho-tri-thuc/models") / MODEL_NAME


def matches_pin(path, expected_size, expected_sha):
    try:
        with path.open("rb") as model_file:
            return (
                os.fstat(model_file.fileno()).st_size == expected_size
                and hashlib.file_digest(model_file, "sha256").hexdigest() == expected_sha
            )
    except FileNotFoundError:
        return False


def provision(model_dir, source_dir=None):
    for filename, (expected_size, expected_sha) in MODEL_FILES.items():
        target = model_dir / filename
        if matches_pin(target, expected_size, expected_sha):
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with NamedTemporaryFile(
                dir=target.parent, prefix=f".{target.name}.", suffix=".tmp", delete=False
            ) as output:
                temp_path = Path(output.name)
                source = (
                    (source_dir / filename).open("rb")
                    if source_dir is not None
                    else urlopen(f"{MODEL_BASE_URL}/{filename}", timeout=30)
                )
                with source:
                    digest = hashlib.sha256()
                    received = 0
                    while chunk := source.read(CHUNK_BYTES):
                        received += len(chunk)
                        if received > expected_size:
                            raise ValueError(f"{filename} exceeds its pinned size")
                        digest.update(chunk)
                        output.write(chunk)
                    if received != expected_size or digest.hexdigest() != expected_sha:
                        raise ValueError(f"{filename} failed pinned size or SHA-256 verification")
            try:
                temp_path.replace(target)
            except PermissionError:
                # Another setup can finish first and the runtime may already have opened it.
                if not matches_pin(target, expected_size, expected_sha):
                    raise
        finally:
            if temp_path is not None:
                with suppress(FileNotFoundError):
                    temp_path.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from-dir",
        type=Path,
        help="copy and verify files from an existing model directory without network access",
    )
    args = parser.parse_args()
    model_dir = model_directory()
    if model_dir is None:
        print("SEARCH_BGE_MODEL_DIR is empty. Local BGE reranking is disabled.")
        return 0
    try:
        provision(model_dir, args.from_dir)
    except (OSError, HTTPException, ValueError) as exc:
        print(f"Local BGE model setup failed: {exc}", file=sys.stderr)
        return 1
    print(f"Verified local BGE model in {model_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
