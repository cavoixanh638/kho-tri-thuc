"""Download the public CPU Whisper base model once; inference never downloads."""

import argparse
import hashlib
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    os.environ.update(HF_HUB_DISABLE_TELEMETRY="1", DO_NOT_TRACK="1")
    from huggingface_hub import snapshot_download

    repo = "Systran/faster-whisper-base"
    # Pin the public model selected and hash-verified for this implementation.
    revision = "ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66"
    args.directory.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo,
        revision=revision,
        local_dir=str(args.directory),
        token=False,
        allow_patterns=[
            "config.json",
            "model.bin",
            "tokenizer.json",
            "vocabulary.*",
            "preprocessor_config.json",
        ],
        max_workers=2,
    )
    model = args.directory / "model.bin"
    with model.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != "d01c3014881c9c6f3133c182f3d2887eb6ca1c789a7538c5c007196857a0a6a9":
        raise ValueError("Unexpected public model checksum")
    manifest = {
        "repository": repo,
        "revision": revision,
        "model_sha256": digest,
        "model_bytes": model.stat().st_size,
        "device": "cpu",
        "compute_type": "int8",
    }
    (args.directory / "kt-model.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
