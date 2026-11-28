"""Collect real lexical rankings for calibration and verify the frozen Windows baseline."""

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
JOURNEYS = HERE.parent
REPO = JOURNEYS.parents[1]
sys.path.insert(0, str(JOURNEYS))
from evaluate import fingerprint, read, write
from scenario_matrix import MATRIX_FILES, load_matrix


def calibration():
    corpus = read(JOURNEYS / "corpus.json")
    labels = read(JOURNEYS / "recall-check.json")
    cases = [
        {"id": row["id"], "query": row["query"], "accept": [row["id"]], "kind": "memory", "suite": "calibration"}
        for row in labels["judgments"]
    ] + [
        {"id": f"N{i:02}", "query": row["query"], "accept": [], "kind": "absent", "suite": "calibration"}
        for i, row in enumerate(labels["negative_queries"], 1)
    ]
    return {"items": corpus["items"], "cases": cases}


def app_tree():
    def git(*args):
        return subprocess.check_output(["git", "-C", str(REPO), *args], text=True).strip()
    tree = git("rev-parse", "HEAD:apps/backend")
    if git("status", "--porcelain", "--", "apps/backend"):
        raise RuntimeError("Benchmark a clean backend checkout")
    return tree


def fixture_hashes():
    paths = [*MATRIX_FILES, JOURNEYS / "corpus.json", JOURNEYS / "recall-check.json"]
    return {p.relative_to(JOURNEYS).as_posix(): fingerprint(p) for p in paths}


def collect():
    spec = importlib.util.spec_from_file_location("confusable_runner", JOURNEYS / "confusable-cases/run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    stored = read(JOURNEYS / "scenario-matrix/results-windows.json")
    tree = app_tree()
    if tree != stored["backend_tree"]:
        raise RuntimeError("A new backend requires a new lexical baseline")
    rows = runner.measure(REPO, load_matrix())
    reference = {r["id"]: r for r in stored["cases"]}
    for row in rows:
        if any(row[k] != reference[row["id"]][k] for k in ("accept", "initial", "expanded", "offered")):
            raise RuntimeError(f"Frozen search order differs at {row['id']}")
    return {
        "backend_tree": tree, "fixtures": fixture_hashes(), "matrix": rows,
        "calibration": runner.measure(REPO, calibration()),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    path = parser.parse_args().output
    output = collect()
    write(path, output, exclusive=True)
    print(f"Verified {len(output['matrix'])} frozen rankings in both modes and measured {len(output['calibration'])} calibration queries.")
