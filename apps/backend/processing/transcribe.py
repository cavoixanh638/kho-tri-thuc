"""Offline, bounded CPU transcription in a credential-free child process."""

import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryFile
from time import monotonic, sleep

MAX_SECONDS = 600
MAX_SEGMENTS = 1000
MAX_CHARS = 100_000
PROCESSOR_VERSION = "faster-whisper-1.2.1-base-int8-v1"
MAX_RESULT_BYTES = 2_000_000


def child_environment():
    env = {
        key: value
        for key, value in os.environ.items()
        if key.upper() in {"SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "PATH"}
    }
    env.update(
        PYTHONUTF8="1",
        HF_HUB_OFFLINE="1",
        HF_HUB_DISABLE_TELEMETRY="1",
        DO_NOT_TRACK="1",
        PYTHONNOUSERSITE="1",
    )
    return env


def transcribe_file(path, model_dir):
    model = Path(model_dir)
    if not (model / "model.bin").is_file() or not (model / "kt-model.json").is_file():
        return {"state": "failed", "error": "transcript_model_missing", "segments": []}
    try:
        # Bound result storage while the child is running, not only after capture.
        with TemporaryFile() as output:
            process = subprocess.Popen(
                [sys.executable, "-m", "processing.transcribe", str(path), str(model)],
                cwd=Path(__file__).resolve().parents[1],
                env=child_environment(),
                stdout=output,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
                if sys.platform == "win32"
                else 0,
            )
            deadline = monotonic() + 420
            try:
                while process.poll() is None:
                    if (
                        monotonic() > deadline
                        or os.fstat(output.fileno()).st_size > MAX_RESULT_BYTES
                    ):
                        raise ValueError("bounded child failed")
                    sleep(0.1)
                if (
                    process.returncode
                    or os.fstat(output.fileno()).st_size > MAX_RESULT_BYTES
                ):
                    raise ValueError("bounded child failed")
                output.seek(0)
                value = json.loads(output.read(MAX_RESULT_BYTES + 1))
            finally:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=5)
        if (
            not isinstance(value, dict)
            or value.get("state") not in {"done", "not_available", "failed"}
            or not isinstance(value.get("segments"), list)
            or len(value["segments"]) > MAX_SEGMENTS
        ):
            raise ValueError("invalid transcription")
        return value
    except (OSError, ValueError, subprocess.SubprocessError):
        return {
            "state": "failed",
            "error": "transcript_processing_failed",
            "segments": [],
        }


def _media_duration(path):
    import av

    with av.open(str(path), mode="r", metadata_errors="ignore") as media:
        if media.duration is None or not media.streams.audio:
            return None
        return float(media.duration / av.time_base)


def run(path, model_dir):
    from faster_whisper import WhisperModel

    # Reject unknown/overlong input before decode_audio can allocate its PCM.
    duration = _media_duration(path)
    if (
        duration is None
        or not math.isfinite(duration)
        or not 0 < duration <= MAX_SECONDS
    ):
        return {"state": "failed", "error": "transcript_duration_limit", "segments": []}
    manifest = json.loads((model_dir / "kt-model.json").read_text(encoding="utf-8"))
    if (
        not isinstance(manifest, dict)
        or manifest.get("repository") != "Systran/faster-whisper-base"
        or not isinstance(manifest.get("revision"), str)
    ):
        raise ValueError("invalid model manifest")
    with (model_dir / "model.bin").open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != manifest.get(
            "model_sha256"
        ):
            raise ValueError("model checksum mismatch")
    model = WhisperModel(
        str(model_dir),
        device="cpu",
        compute_type="int8",
        cpu_threads=4,
        num_workers=1,
        local_files_only=True,
    )
    segments, info = model.transcribe(
        str(path), beam_size=3, vad_filter=True, condition_on_previous_text=False
    )
    if not math.isfinite(info.duration) or not 0 < info.duration <= MAX_SECONDS:
        return {"state": "failed", "error": "transcript_duration_limit", "segments": []}
    output, size = [], 0
    for part in segments:
        text = part.text.strip()
        if not text:
            continue
        if (
            not all(math.isfinite(value) for value in (part.start, part.end))
            or not 0 <= part.start <= part.end <= MAX_SECONDS + 1
        ):
            raise ValueError("invalid segment timing")
        size += len(text)
        if len(output) >= MAX_SEGMENTS or size > MAX_CHARS:
            return {
                "state": "failed",
                "error": "transcript_output_limit",
                "segments": [],
            }
        output.append(
            {"start": round(part.start, 3), "end": round(part.end, 3), "text": text}
        )
    return {
        "state": "done" if output else "not_available",
        "segments": output,
        "language": info.language,
        "language_probability": round(info.language_probability, 4),
        "duration": round(info.duration, 3),
        "model_revision": manifest["revision"],
    }


if __name__ == "__main__":
    try:
        answer = run(Path(sys.argv[1]), Path(sys.argv[2]))
    except Exception:  # noqa: BLE001 - do not emit private paths, transcript or remote exception details
        answer = {
            "state": "failed",
            "error": "transcript_processing_failed",
            "segments": [],
        }
    print(json.dumps(answer, ensure_ascii=True))
