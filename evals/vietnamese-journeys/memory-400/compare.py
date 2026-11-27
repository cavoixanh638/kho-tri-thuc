"""Compare baseline and challenger without revisiting any frozen labels."""

import argparse
import math
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

from run import HERE, fingerprint, fixture, read, unique, write
from scenario_matrix import assess


def percentile(values, percent):
    return sorted(values)[math.ceil(percent * len(values)) - 1]


def aggregate(rows):
    negative = [r for r in rows if not r["accept"]]
    singleton = [r for r in rows if len(r["accept"]) == 1]
    multiple = [r for r in rows if len(r["accept"]) > 1]
    result = {
        "n": len(rows), "initial_pass": sum(r["initial_pass"] for r in rows),
        "offered": sum(r["offered"] for r in rows),
        "with_challengers_scored": sum(r["challengers"] > 0 for r in rows),
        "challengers_scored": sum(r["challengers"] for r in rows),
        "displayed_additions": sum(bool(r["added"]) for r in rows),
        "gains": sum(r["trial_pass"] and not r["control_pass"] for r in rows),
        "losses": sum(r["control_pass"] and not r["trial_pass"] for r in rows),
        "negative_n": len(negative), "singleton_n": len(singleton), "multi_n": len(multiple),
    }
    for mode in ("control", "trial"):
        result[mode] = {
            "pass": sum(r[mode + "_pass"] for r in rows),
            "singleton_top1": sum(r[mode + "_pass"] for r in singleton),
            "singleton_found_top5": sum(bool(set(r[mode]) & set(r["accept"])) for r in singleton),
            "multi_all_top5": sum(r[mode + "_pass"] for r in multiple),
            "negative_with_hits": sum(bool(r[mode]) for r in negative),
            "negative_hits": sum(len(r[mode]) for r in negative),
        }
        times = [r[mode + "_ms"] for r in rows if r["offered"]]
        if times:
            result[mode]["click_median_ms"] = round(median(times), 2)
            result[mode]["click_p95_ms"] = percentile(times, .95)
    return result


def clustered_interval(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[r["block"]].append(int(r["trial_pass"]) - int(r["control_pass"]))
    means = [mean(group) for group in groups.values()]
    assert len(means) == 100 and all(len(group) == 4 for group in groups.values())
    rng = random.Random(20261127)
    samples = [sum(rng.choices(means, k=len(means))) / len(means) for _ in range(10000)]
    return {"blocks": len(groups), "replicates": len(samples), "seed": 20261127,
            "estimate_pp": round(100 * mean(means), 4),
            "lower95_pp": round(100 * percentile(samples, .025), 4),
            "upper95_pp": round(100 * percentile(samples, .975), 4)}


def compare(control, trial):
    suite = control["suite"]
    data, files = fixture(suite)
    hashes = {f.name: fingerprint(f) for f in files}
    assert trial["suite"] == suite and (control["mode"], trial["mode"]) == ("control", "trial")
    assert hashes == control["fixtures"] == trial["fixtures"]
    assert control["runner_sha256"] == trial["runner_sha256"] == fingerprint(HERE / "run.py")
    items = {i["id"]: i for i in data["items"]}
    rows = []
    for c, a, b in zip(data["cases"], control["cases"], trial["cases"], strict=True):
        assert a["id"] == b["id"] == c["id"]
        assert (a["initial"], a["initial_sha256"], a["offered"]) == (
            b["initial"], b["initial_sha256"], b["offered"]), f"Default changed: {c['id']}"
        old = a["expanded"] if a["offered"] else a["initial"]
        new = b["expanded"] if b["offered"] else b["initial"]
        unique(old, "old ID")
        unique(new, "new ID")
        added = [i for i in new if i not in old]
        assert [i for i in new if i in old] == old, f"Original order or membership changed: {c['id']}"
        assert len(added) <= 1 and bool(added) == bool(b.get("admitted"))
        if added:
            assert a["offered"] and new[:1] == added and len(new) <= 5
        verdicts = [assess(page, c, items) for page in (a["initial"], old, new)]
        assert not any(v["out_of_scope"] for v in verdicts), c["id"]
        row = {"id": c["id"], "kind": c["kind"], "suite": c["suite"], "accept": c["accept"],
               "initial": a["initial"], "initial_sha256": a["initial_sha256"], "offered": a["offered"],
               "control": old, "trial": new, "added": added, "challengers": b.get("candidates", 0),
               **{name + "_pass": v["pass"] for name, v in zip(("initial", "control", "trial"), verdicts)}}
        if "block" in c:
            row["block"] = c["block"]
        if a["offered"]:
            row.update(control_ms=a["expanded_ms"], trial_ms=b["expanded_ms"],
                       control_ranking=a["ranking"], trial_ranking=b["ranking"])
        rows.append(row)
    groups = {"all": rows, "clicked": [r for r in rows if r["offered"]],
              "scored": [r for r in rows if r["challengers"]]}
    if suite == "400":
        groups.update({kind: [r for r in rows if r["kind"] == kind]
                       for kind in ("memory", "negative", "control", "multi")})
    for name in sorted({r["suite"] for r in rows}):
        groups[name] = [r for r in rows if r["suite"] == name]
    result = {"suite": suite, "notes": len(items), "fixtures": hashes,
              "runner_sha256": control["runner_sha256"], "comparison_sha256": fingerprint(Path(__file__)),
              "control_source": control["source"], "trial_source": trial["source"],
              "control_backend_tree": control["backend_tree"], "trial_backend_tree": trial["backend_tree"],
              "identical_default_responses": len(rows), "outside_scope": 0,
              "metrics": {key: aggregate(group) for key, group in groups.items()}}
    if suite == "400":
        result["paired_cluster_ci"] = clustered_interval(rows)
    result["cases"] = rows
    return result


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--control", type=Path, required=True)
    cli.add_argument("--trial", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    report = compare(read(args.control), read(args.trial))
    write(args.output, report, exclusive=True)
    print(report["metrics"]["all"], report.get("paired_cluster_ci", ""))
