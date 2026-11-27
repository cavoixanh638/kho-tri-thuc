"""Offline diagnostic of wider semantic retrieval on already offered prose searches."""

import argparse
import sys
from pathlib import Path

from run import HERE, fingerprint, fixture, read, write
from scenario_matrix import assess

PILOT = HERE.parent / "semantic-pilot"
sys.path.insert(0, str(PILOT))
sys.path.insert(0, str(HERE.parents[2] / "apps/backend"))
from models import Embedding, Reranker
from pilot import collect_scores, ranked, setup
from search.claims import claim_params
from search.quantities import quantity_params
from search.recall import recall_params
from search.structured import lookup, normalize_query


def prose(text):
    q = normalize_query(text)
    terms = (recall_params(q) or {}).get("terms", [])
    claims = claim_params(q)
    return (len(terms) >= 4 and not any(ch.isdigit() for ch in q) and not lookup(q)[0]
            and not claims["claim_patterns"] and not claims["claim_opposite"]
            and not quantity_params(q)["quantity_required"])


def summarize(rows):
    result = {"n": len(rows), "tested_clicks": sum(r["active"] for r in rows),
              "tested_full_pages": sum(r["active"] and len(r["original"]) == 5 for r in rows)}
    for mode in ("original", "filtered", "semantic"):
        result[mode] = {
            "pass": sum(r[mode + "_pass"] for r in rows),
            "gains": sum(r[mode + "_pass"] and not r["original_pass"] for r in rows),
            "losses": sum(not r[mode + "_pass"] and r["original_pass"] for r in rows),
            "negative_with_hits": sum(not r["expected"] and bool(r[mode]) for r in rows),
            "negative_hits": sum(len(r[mode]) for r in rows if not r["expected"]),
            "positive_now_empty": sum(bool(r["expected"] and r["original"]) and not r[mode] for r in rows),
            "positive_in_top5": sum(bool(set(r[mode]).intersection(r["expected"])) for r in rows),
        }
    return result


def measure(suite, encoder, reranker, calibration):
    data, files = fixture(suite)
    ref_path = HERE / f"results-{suite}-windows.json"
    ref = read(ref_path)
    assert ref["fixtures"] == {f.name: fingerprint(f) for f in files}
    items = {i["id"]: i for i in data["items"]}
    cases = data["cases"]
    controls = {r["id"]: r for r in ref["cases"]}
    selected = [c for c in cases if controls[c["id"]]["offered"] and prose(c["query"])]
    refs = [{"id": c["id"], "offered": True, "initial": controls[c["id"]]["initial"],
             "expanded": controls[c["id"]]["control"]} for c in selected]
    # The previous pilot ranks only by document text, query and already known
    # search filters. Remove answer keys even from its input.
    plain = [{k: c[k] for k in ("id", "query", "filters") if k in c} for c in selected]
    scored = collect_scores({"items": data["items"], "cases": plain}, refs, encoder, reranker)
    floor = calibration["reranked"]["threshold"]
    rows = []
    for c in cases:
        ref_row = controls[c["id"]]
        old = ref_row["control"]
        filtered = semantic = old
        if s := scored.get(c["id"]):
            semantic = ranked(s, "reranked", floor)
            scores = {k: p for k, _, p in s["candidates"] if p is not None}
            missing = [k for k in old if k not in scores]
            texts = ["\n".join(items[k][f] for f in ("title", "description", "note") if items[k].get(f))
                     for k in missing]
            scores.update(zip(missing, reranker.score(c["query"], texts), strict=True))
            filtered = sorted((k for k in old if scores[k] >= floor), key=scores.__getitem__, reverse=True)
        row = {"id": c["id"], "kind": c["kind"], "active": c["id"] in scored, "expected": c["accept"]}
        for label, hits in (("original", old), ("filtered", filtered), ("semantic", semantic)):
            verdict = assess(hits, c, items)
            assert not verdict["out_of_scope"] and len(set(hits)) == len(hits) <= 5
            row[label] = hits
            row[label + "_pass"] = verdict["pass"]
        assert ref_row["control_pass"] == row["original_pass"]
        rows.append(row)
    groups = {"all": rows, "active": [r for r in rows if r["active"]]}
    if suite == "400":
        groups.update({kind: [r for r in rows if r["kind"] == kind]
                       for kind in ("memory", "multi", "negative", "control")})
    return {"reference_sha256": fingerprint(ref_path), "metrics": {k: summarize(g) for k, g in groups.items()},
            "cases": rows}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--models", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    cal_path = PILOT / "calibration-windows.json"
    calibration = read(cal_path)
    config = setup()
    for k in ("models", "dense_k", "lexical_k", "rerank_k", "rrf_k", "implementation"):
        assert config[k] == calibration["config"][k], k
    encoder, reranker = Embedding(args.models), Reranker(args.models)
    report = {"status": "exploratory_offline_after_primary", "calibration_sha256": fingerprint(cal_path),
              "script_sha256": fingerprint(Path(__file__)), "models": config["models"],
              "minimum_logit": calibration["reranked"]["threshold"]}
    for suite in ("120", "400"):
        report[suite] = measure(suite, encoder, reranker, calibration)
        print(suite, report[suite]["metrics"]["all"], flush=True)
    write(args.output, report, exclusive=True)
