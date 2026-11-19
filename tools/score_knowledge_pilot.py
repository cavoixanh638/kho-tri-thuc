"""Score private connector observations against the public controlled corpus.

No network calls. The report uses case aliases, never provider/user IDs or full
retrieved text. Answers are manually written by the auditor after connector
reads; this is evidence coverage, not an independent blind model benchmark.
"""

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def normalized(text):
    return unicodedata.normalize("NFC", text).casefold()


def current_note(text):
    plain = re.sub(r"(?m)^#{1,3} ", "", text)
    return plain.split("\nGhi chú người dùng\n", 1)[1].split("\nNguồn\n", 1)[0]


def score(corpus, observed):
    cases = {row["key"]: row for row in corpus["cases"]}
    before, after = observed["before"], observed["after"]
    ids = {row["id"]: key for key, row in after.items()}
    questions = []
    for question in corpus["questions"]:
        key = question["id"]
        expected = set(question["keys"])
        primary = {
            ids.get(value, "other")
            for value in observed["searches"][key]["primary_ids"]
        }
        fallback = {
            ids.get(value, "other")
            for value in observed["searches"][key].get("fallback_ids", [])
        }
        used = primary if expected <= primary else fallback
        texts = [after[case]["content"] for case in question["keys"]]
        if question.get("section") == "Ghi chú người dùng":
            texts = [current_note(text) for text in texts]
        text = normalized("\n".join(texts))
        answer = observed["answers"][key]
        evidence = all(normalized(term) in text for term in question["answer_terms"])
        excludes_old = all(
            normalized(term) not in text for term in question.get("forbidden_terms", [])
        )
        answer_has_terms = all(
            normalized(term) in normalized(answer) for term in question["answer_terms"]
        )
        passed = expected <= used and evidence and excludes_old and answer_has_terms
        questions.append(
            {
                "id": key,
                "question": question["question"],
                "primary_query": question["semantic_query"],
                "primary_found_expected": expected <= primary,
                "primary_result_count": len(observed["searches"][key]["primary_ids"]),
                "keyword_fallback_used": not expected <= primary,
                "fallback_query": question["fallback_query"]
                if not expected <= primary
                else None,
                "retrieved_expected_sources": expected <= used,
                "evidence_terms_present": evidence,
                "superseded_terms_excluded": excludes_old,
                "answer": answer,
                "source_cases": question["keys"],
                "result": "PASS" if passed else "FAIL",
            }
        )
    unchanged = ["scope", "unicode", "page", "missing"]
    changed = ["commit", "backup", "note", "subtitle"]
    checks = {
        "eight_files_readable_before_and_after": len(before)
        == len(after)
        == len(cases)
        == 8
        and all(row["content"] for row in before.values())
        and all(row["content"] for row in after.values()),
        "same_file_ids_before_and_after": all(
            before[key]["id"] == after[key]["id"] for key in cases
        ),
        "changed_fields_read_as_current": all(
            before[key]["content"] != after[key]["content"] for key in changed
        ),
        "unchanged_content_exact": all(
            before[key]["content"] == after[key]["content"] for key in unchanged
        ),
        "current_note_has_new_deadline": "30/11"
        in current_note(after["note"]["content"])
        and "27/11" not in current_note(after["note"]["content"]),
        "original_capture_note_still_present": "27/11"
        in after["note"]["content"].split("## Chú thích từng lượt tiếp nhận", 1)[1],
        "subtitle_current_version_only": "cờ cam" in after["subtitle"]["content"]
        and "cờ tím" not in after["subtitle"]["content"],
        "missing_video_transcript_explicit": "CHƯA CÓ TRANSCRIPT VIDEO"
        in after["missing"]["content"],
        "provided_subtitle_not_marked_missing": "CHƯA CÓ TRANSCRIPT VIDEO"
        not in after["subtitle"]["content"],
    }
    primary_pass = sum(row["primary_found_expected"] for row in questions)
    passed = sum(row["result"] == "PASS" for row in questions)
    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "status": "PASS_CONTROLLED_WITH_SEARCH_LIMITATION"
        if all(checks.values()) and passed == len(questions)
        else "FAIL",
        "scope": "Codex Google Drive connector, 8 controlled Items, 9 predeclared questions; folder-scoped keyword retrieval and auditor-written grounded answers",
        "method": "Initial query uses several question terms; a predeclared shorter keyword is allowed after a miss. Full file text is fetched before and after changes. This does not measure general semantic search or independent ChatGPT UI behavior.",
        "checks": checks,
        "summary": {
            "primary_query_successes": primary_pass,
            "questions": len(questions),
            "answers_with_retrieved_evidence": passed,
            "keyword_fallbacks": len(questions) - primary_pass,
            "formats": dict(Counter(row["mime_type"] for row in after.values())),
        },
        "questions": questions,
        "limitations": [
            "Controlled public paraphrases and authored fixtures; not personal-corpus quality",
            "Question terms and folder were supplied by the auditor; not blind ranking or unrestricted discovery",
            "One primary query missed; shorter keyword found the expected note",
            "No independent ChatGPT consumer UI session or indexing-latency SLA",
            "No native Google Docs, PDF parser or ASR acceptance",
        ],
        "data_handling": "Only case aliases, public/fixture answers and outcomes retained; provider IDs and retrieved export text stay outside Git",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument(
        "--corpus", type=Path, default=ROOT / "evals/knowledge/pilot-cases.json"
    )
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = score(
        json.loads(args.corpus.read_text(encoding="utf-8")),
        json.loads(args.observations.read_text(encoding="utf-8")),
    )
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": report["status"], **report["summary"]}))
    return int(report["status"] == "FAIL")


if __name__ == "__main__":
    sys.exit(main())
