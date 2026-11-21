"""P17 offline media fault harness: no credential/network and no production mutation."""
import argparse
import hashlib
import importlib.util
import json
import tempfile
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "evals/parallel/p17-media"

def production(path, alias):
    file = ROOT / "apps/backend" / path
    spec = importlib.util.spec_from_file_location(alias, file)
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module

def fingerprint(data):
    return hashlib.sha256(data).hexdigest()

def proof(**changes):
    payload = b"p17-synthetic-source-bytes" * 8
    record = dict(local=payload, asset_size=len(payload), asset_sha=fingerprint(payload),
                  location="verified", file_id="fake-drive-id", owner="a", remote_owner="a",
                  item="b", remote_item="b", asset="c", remote_asset="c",
                  remote=payload, remote_size=len(payload), remote_sha=fingerprint(payload),
                  complete=True)
    record.update(changes)
    local, remote = record["local"], record["remote"]
    return bool(local and remote and record["complete"] and record["location"] == "verified"
                and record["file_id"] and record["owner"] == record["remote_owner"]
                and record["item"] == record["remote_item"] and record["asset"] == record["remote_asset"]
                and record["asset_size"] == len(local) and record["asset_sha"] == fingerprint(local)
                and record["remote_size"] == len(remote) and record["remote_sha"] == fingerprint(remote)
                and len(local) == len(remote) and fingerprint(local) == fingerprint(remote))

def readback(case):
    payload = b"p17-synthetic-source-bytes" * 8
    options = {
        "valid_full_readback": {},
        "metadata_only": {"local": None},
        "no_file_id": {"file_id": None},
        "db_pending": {"location": "pending"},
        "unverified_upload": {"location": "failed"},
        "no_readback": {"remote": None, "complete": False},
        "partial_readback": {"remote": payload[:-1], "complete": False},
        "readback_truncated_claim_complete": {"remote": payload[:-1]},
        "corrupt_readback": {"remote": payload[:-1] + b"!"},
        "local_corruption": {"local": payload + b"!"},
        "remote_sha_wrong": {"remote_sha": "0"*64},
        "remote_sha_missing": {"remote_sha": ""},
        "remote_size_wrong": {"remote_size": len(payload)+1},
        "asset_size_wrong": {"asset_size": len(payload)+1},
        "asset_sha_wrong": {"asset_sha": "0"*64},
        "owner_mismatch": {"remote_owner": "other"},
        "item_mismatch": {"remote_item": "other"},
        "asset_mismatch": {"remote_asset": "other"},
        "empty_local": {"local": b""},
        "empty_remote": {"remote": b""},
        "range_only": {"remote": payload[:3], "complete": False},
    }
    return proof(**options[case])

def manifest(parent, injection):
    with tempfile.TemporaryDirectory(prefix="p17-only-") as directory:
        root = Path(directory)
        if injection == "manifest_missing":
            pass
        elif injection == "manifest_malformed":
            (root / "result.json").write_text("not json", encoding="utf8")
        elif injection == "manifest_oversize":
            (root / "result.json").write_bytes(b"x"*(parent.MAX_RESULT_BYTES+1))
        else:
            value = {"status": "failed", "error_code": injection}
            if injection in ("valid_manifest", "invalid_header", "missing_video"):
                value = {"status": "done", "title": "", "description": "", "platform_id": "123", "duration": 1.0}
            (root / "result.json").write_text(json.dumps(value), encoding="utf8")
            if injection == "invalid_header":
                (root / "video.mp4").write_bytes(b"<html>wrong bytes</html>")
            if injection == "valid_manifest":
                (root / "video.mp4").write_bytes(bytes([0, 0, 0, 24]) + b"ftypisomdata")
        try:
            parent._result(root)
            return "ok", False
        except parent.VideoDownloadError as error:
            return error.code, error.retryable
        except (json.JSONDecodeError, UnicodeError) as error:
            return "unhandled_" + type(error).__name__.lower(), False

def evaluate():
    sources = json.loads((FIXTURES / "sources.json").read_text())
    faults = json.loads((FIXTURES / "faults.json").read_text())
    states = json.loads((FIXTURES / "states.json").read_text())
    assert len(sources) == 50 and len({x["url"] for x in sources}) == 50
    assert len(faults) >= 20 and len({x["id"] for x in faults}) == len(faults)
    required = {"captured","metadata_only","downloaded_unverified","stored_verified",
                "transcript_pending","transcript_done","transcript_unavailable","failed"}
    assert required <= {x["state"] for x in states}
    for state in states:
        if state["state"] in {"captured", "metadata_only", "failed"}:
            assert not state["media_bytes"] and not state["readback_sha_verified"]
        if state["state"] == "stored_verified":
            assert state["readback_sha_verified"]
    identity = production("ingestion/source_identity.py", "p17_identity")
    parent = production("processing/video_download.py", "p17_parent")
    child = production("processing/video_download_child.py", "p17_child")
    by_platform = Counter()
    accepted = 0
    for source in sources:
        value = identity.source_identity(source["url"])
        if source["platform"] == "youtube":
            assert value.platform == "youtube" and value.platform_id == source["video_id"]
        else:
            assert value.platform == "web"
        ok = parent.is_facebook_url(source["url"])
        assert ok == source["expected_direct_video_download"], source["id"]
        accepted += int(ok)
        by_platform[source["platform"]] += 1
    assert not child.allowed_host("facebook.com.evil.test")
    assert not child.public_ip("127.0.0.1")
    assert parent.MAX_BYTES == 128*1024*1024
    faults_failed = []
    for entry in faults:
        if entry["kind"] == "manifest":
            code, retryable = manifest(parent, entry["injection"])
        elif entry["kind"] == "readback_oracle":
            code, retryable = ("ok" if readback(entry["injection"]) else "not_verified"), False
        elif entry["kind"] == "retry_policy_mirror":
            schedule = [min(5*2**(attempt-1),60) for attempt in range(1,5)] if entry["retryable"] else []
            assert schedule == ([5,10,20,40] if entry["retryable"] else [])
            code, retryable = ("retry_then_failed" if schedule else "failed_no_retry"), bool(schedule)
        else:
            raise ValueError("unsupported fixture kind")
        if (code, retryable) != (entry["expected_code"],entry["expected_retryable"]):
            faults_failed.append({"case": entry["id"], "observed": code, "retryable": retryable})
    # 10k *metadata* records; not 10k downloaded videos or network throughput.
    start = time.monotonic()
    synthetic = {f"p17-{i:05d}": {"state": "captured", "source": i%50} for i in range(10000)}
    assert len(synthetic) == 10000
    result = {
        "scope": "offline fixture and selected real production functions; NOT live media/Drive/DB",
        "status": "PASS" if not faults_failed else "FAIL",
        "sources": {"total":len(sources), "platforms":dict(by_platform), "facebook_direct_eligible":accepted},
        "states": sorted(required), "faults":{"total":len(faults),"matched":len(faults)-len(faults_failed),"failures":faults_failed},
        "synthetic_metadata":{"items":len(synthetic),"seconds":round(time.monotonic()-start,5)},
        "not_run":["live FB/TikTok/YouTube fetch","full Drive readback real bytes",
                   "100GB and 10000 video storage","PostgreSQL worker retry",
                   "thumbnail/PDF/ASR real processing"]}
    return result

if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--output", type=Path)
    args = cli.parse_args()
    report = evaluate()
    data = json.dumps(report, indent=2, ensure_ascii=False) + chr(10)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data, encoding="utf8")
    print(data, end="")
    raise SystemExit(report["status"] != "PASS")
