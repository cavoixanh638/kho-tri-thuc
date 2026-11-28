"""Calibrate on 51 older queries, then score the distinct frozen 120-case matrix."""

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np
import onnxruntime
import tokenizers

from fetch_models import MODELS
from judge import compare, summarize
from models import Embedding, MAX_TOKENS, Reranker
from references import app_tree, calibration, fixture_hashes, load_matrix, read, write
from scenario_matrix import in_scope


HERE = Path(__file__).resolve().parent
DENSE_K, LEXICAL_K, PAIR_K, FUSION_K = 12, 5, 8, 60


def setup():
    return {
        "models": {k: {"repo": v[0], "revision": v[1]} for k, v in MODELS.items()},
        "embedding_graph": "FP32 ONNX; CLS pooling and L2 normalization",
        "rerank_graph": "Q8 ONNX; raw pair logit",
        "max_tokens": MAX_TOKENS, "dense_k": DENSE_K, "lexical_k": LEXICAL_K,
        "rerank_k": PAIR_K, "rrf_k": FUSION_K, "backend_tree": app_tree(),
        "policy": "preserve a nonempty initial page with no expansion; otherwise offer semantic suggestions",
        "implementation": {
            name: hashlib.sha256((HERE / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            for name in ("pilot.py", "models.py", "judge.py")
        },
    }


def collect_scores(fixture, lexical, encoder, reranker):
    docs = fixture["items"]
    cases = fixture["cases"]
    positions = {d["id"]: i for i, d in enumerate(docs)}
    references = {r["id"]: r for r in lexical}
    texts = ["\n".join(d[k] for k in ("title", "description", "note") if d.get(k)) for d in docs]

    def encode(values):
        return np.vstack([encoder.encode(values[i:i+8]) for i in range(0, len(values), 8)])

    vectors = encode(texts)
    queries = encode([case["query"] for case in cases])
    results = {}
    for case, query_vector in zip(cases, queries, strict=True):
        key = case["id"]
        reference = references[key]
        baseline = reference["expanded"] if reference["offered"] else reference["initial"]
        if reference["initial"] and not reference["offered"]:
            results[key] = {"baseline": baseline, "fixed": True, "candidates": []}
            continue
        eligible = [i for i, d in enumerate(docs) if in_scope(d, case.get("filters", {}))]
        if any(positions[n] not in eligible for n in baseline):
            raise ValueError(f"Lexical scope violation for {key}")
        similarities = {i: float(score) for i, score in zip(eligible, vectors[eligible] @ query_vector)}
        dense = sorted(eligible, key=lambda i: (-similarities[i], i))[:DENSE_K]
        fused = {}
        for stream in (dense, [positions[n] for n in baseline[:LEXICAL_K]]):
            for rank, i in enumerate(stream, 1):
                fused[i] = fused.get(i, 0.0) + 1 / (FUSION_K + rank)
        order = sorted(fused, key=lambda i: (-fused[i], i))
        pairs = order[:PAIR_K]
        logits = reranker.score(case["query"], [texts[i] for i in pairs])
        pair_scores = dict(zip(pairs, map(float, logits), strict=True))
        results[key] = {
            "baseline": baseline, "fixed": False,
            "candidates": [(docs[i]["id"], similarities[i], pair_scores.get(i)) for i in order],
        }
    return results


def ranked(row, mode, threshold):
    if mode == "lexical" or row["fixed"]:
        return row["baseline"]
    candidates = row["candidates"]
    if mode == "hybrid":
        return [item for item, dense, _ in candidates if dense >= threshold][:5]
    pairs = [(item, logit) for item, _, logit in candidates if logit is not None and logit >= threshold]
    pairs.sort(key=lambda pair: -pair[1])
    return [item for item, _ in pairs[:5]]


def calibrate(cases, rows, mode):
    positives = [c for c in cases if c["accept"]]
    negatives = [c for c in cases if not c["accept"]]
    grid = [i / 100 for i in range(101)] if mode == "hybrid" else [i / 2 for i in range(-24, 25)]
    best = None
    for threshold in grid:
        top1 = sum(ranked(rows[c["id"]], mode, threshold)[:1] == c["accept"] for c in positives)
        empty = sum(not ranked(rows[c["id"]], mode, threshold) for c in negatives)
        # Integer score proportional to mean(positive top-1 rate, negative empty rate).
        objective = top1 * len(negatives) + empty * len(positives)
        candidate = (objective, empty, threshold, top1)
        if best is None or candidate > best:
            best = candidate
    _, empty, threshold, top1 = best
    return {"threshold": threshold, "positive_top1": top1, "positives": len(positives),
            "negative_empty": empty, "negatives": len(negatives)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("calibrate", "evaluate"))
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    reference = read(args.reference)
    config = setup()
    hashes = fixture_hashes()
    if config["backend_tree"] != reference["backend_tree"] or hashes != reference["fixtures"]:
        raise ValueError("Lexical reference belongs to a different fixture or backend")
    if args.phase == "evaluate":
        if not args.output:
            parser.error("Evaluation requires --output")
        fitted = read(args.calibration)
        if fitted["config"] != config or fitted["fixtures"] != hashes:
            raise ValueError("Use the pre-calibrated settings for this experiment")
    fixture = calibration() if args.phase == "calibrate" else load_matrix()
    start = time.perf_counter()
    encoder = Embedding(args.models, args.threads)
    reranker = Reranker(args.models, args.threads)
    rows = collect_scores(fixture, reference["calibration" if args.phase == "calibrate" else "matrix"], encoder, reranker)
    print(f"{args.phase}: scored {len(rows)} cases in {time.perf_counter() - start:.1f}s including model load", flush=True)
    if args.phase == "calibrate":
        fitted = {
            "config": config, "fixtures": hashes,
            "criterion": "maximize mean(positive top-1 rate, true negative rate); tie: more negatives empty, then stricter threshold",
            "hybrid": calibrate(fixture["cases"], rows, "hybrid"),
            "reranked": calibrate(fixture["cases"], rows, "reranked"),
        }
        write(args.calibration, fitted, exclusive=True)
        print(fitted["hybrid"], fitted["reranked"])
        return
    rankings = {
        name: {key: ranked(row, name, 0 if name == "lexical" else fitted[name]["threshold"]) for key, row in rows.items()}
        for name in ("lexical", "hybrid", "reranked")
    }
    report = {
        "config": config, "fixtures": hashes, "threads": args.threads,
        "python": platform.python_version(), "onnxruntime": onnxruntime.__version__,
        "tokenizers": tokenizers.__version__, "numpy": np.__version__,
        "calibration": {k: fitted[k] for k in ("criterion", "hybrid", "reranked")},
        "preserved_initial": sum(r["fixed"] for r in rows.values()), "summary": {}, "changes": {}, "cases": {},
    }
    for name, result in rankings.items():
        summary = summarize(fixture["cases"], fixture["items"], result)
        report["summary"][name] = {k: v for k, v in summary.items() if k != "cases"}
        if name != "lexical":
            report["changes"][name] = compare(fixture["cases"], fixture["items"], rankings["lexical"], result)
        for key, hits in result.items():
            report["cases"].setdefault(key, {"preserved_initial": rows[key]["fixed"]})[name] = {
                "top5": hits, "pass": summary["cases"][key]["pass"],
                "out_of_scope": summary["cases"][key]["out_of_scope"],
            }
    write(args.output, report, exclusive=True)
    print(json.dumps({key: v["all"] for key, v in report["summary"].items()}, ensure_ascii=True))


if __name__ == "__main__":
    main()
