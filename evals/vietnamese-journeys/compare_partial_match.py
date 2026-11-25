"""Try a second retrieval pass on the public fixture where SearchService returned nothing.

This is an offline comparison on one owner's authored notes. It does not change
SearchService or estimate the speed of applying this policy to a large library.
Run from any directory. JSON on stdout contains counts and fixture aliases.
"""
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def terms(text):
    folded = unicodedata.normalize("NFD", text.casefold().replace("đ", "d"))
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    return set(re.findall(r"[^\W_]+", folded))


def partial_matches(query, documents, frequency):
    # Fixed before scoring. Require two different shared terms. Among ties in
    # summed inverse document frequency, use the stable fixture ID.
    query_terms = terms(query)
    scores = []
    for key, doc_terms in documents.items():
        common = query_terms & doc_terms
        if len(common) < 2:
            continue
        score = sum(math.log((len(documents) + 1) / (frequency[word] + 1))
                    for word in sorted(common))
        scores.append((-score, key))
    return [key for _, key in sorted(scores)[:5]]


def summary(rows):
    positives = [row for row in rows if row["target"]]
    negatives = [row for row in rows if not row["target"]]
    memory = [row for row in positives if row["kind"] == "memory"]
    return {
        "positive_queries": len(positives),
        "existing_top5_hits": sum(row["target"] in row["before"] for row in positives),
        "experiment_top5_hits": sum(row["target"] in row["after"] for row in positives),
        "memory_queries": len(memory),
        "memory_top5_hits": sum(row["target"] in row["after"] for row in memory),
        "new_nonempty_missing_target": sum(not row["before"] and bool(row["after"])
                                          and row["target"] not in row["after"] for row in positives),
        "negative_queries": len(negatives),
        "negatives_with_results": sum(bool(row["after"]) for row in negatives),
    }


def main():
    corpus_bytes = (HERE / "corpus.json").read_bytes()
    gold_bytes = (HERE / "provisional.json").read_bytes()
    corpus = json.loads(corpus_bytes)
    gold = json.loads(gold_bytes)
    baseline = json.loads((HERE / "results-windows-after.json").read_bytes())
    if (hashlib.sha256(corpus_bytes).hexdigest() != baseline["corpus_sha256"]
            or hashlib.sha256(gold_bytes).hexdigest() != baseline["gold_sha256"]):
        raise ValueError("Fixture files differ from the measured PostgreSQL baseline")
    documents = {row["id"]: terms(row["title"] + " " + row["note"]) for row in corpus["items"]}
    frequency = Counter(term for doc in documents.values() for term in doc)
    labels = {row["id"]: row for row in gold["judgments"]}
    rows = []
    for entry in baseline["diagnostics"]:
        key = entry["id"]
        before = entry["top5"]
        rows.append({"target": key, "split": entry["split"], "kind": entry["kind"],
                     "before": before, "after": before or partial_matches(labels[key]["query"], documents, frequency)})
    for entry, label in zip(baseline["negative_queries"], gold["negative_queries"], strict=True):
        before = entry["top5"]
        rows.append({"target": None, "split": label["split"], "kind": "negative",
                     "before": before, "after": before or partial_matches(label["query"], documents, frequency)})
    report = {
        "scope": "offline public synthetic notes; fallback only when original top five is empty",
        "baseline_sha": baseline["code_sha"], "overall": summary(rows),
        "holdout": summary([row for row in rows if row["split"] == "holdout"]),
        "development": summary([row for row in rows if row["split"] == "development"]),
        "rows": rows,
    }
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
