#!/usr/bin/env python3
"""Run the frozen catalog parser without installing Django or touching a DB.

Extracts the *actual function AST* from catalog/groups_api.py, not a reimplementation.
Audit findings are machine-readable; --strict exits 1 if any criterion fails.
Usage: python evals/parallel/p10-parser-audit.py [--strict]
"""

import argparse
import ast
import json
import re
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "apps/backend/catalog/groups_api.py"


def load_parser():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    matches = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_inline_item_links"]
    if len(matches) != 1:
        raise RuntimeError("exactly one production parser function required")
    module = ast.fix_missing_locations(ast.Module(body=matches, type_ignores=[]))
    namespace = {"UUID": UUID, "re": re}
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace["_inline_item_links"]


def evaluate():
    parser = load_parser()
    a = uuid5(NAMESPACE_URL, "p10-frozen-a")
    b = uuid5(NAMESPACE_URL, "p10-frozen-b")
    link_a, link_b = f"[Tiếng Việt](#/muc/{a})", f"[Trùng tên](#/muc/{b})"
    ticks = "\x60" * 3
    cases = [
        ("uuid_normal", link_a, {a}),
        ("two_links", link_a + " " + link_b, {a, b}),
        ("unicode_label", "Xem thêm " + link_a + "\r\n", {a}),
        ("duplicate_target_deduplicated", link_a + "\n" + link_a, {a}),
        ("fenced_backtick", ticks + "md\n" + link_a + "\n" + ticks, set()),
        ("fenced_tilde", "~~~~\n" + link_a + "\n~~~~", set()),
        ("inline_code", "\x60" + link_a + "\x60", set()),
        ("escaped_open_bracket", "\\" + link_a, set()),
        ("indented_code", "    " + link_a, set()),
        ("html_script", "<script>" + link_a + "</script>", set()),
        ("html_comment", "<!-- " + link_a + " -->", set()),
        ("image_not_link", "![img](#/muc/" + str(a) + ")", set()),
        ("unsafe_scheme", "[x](javascript:alert(1))", set()),
        ("malformed_uuid", "[x](#/muc/not-a-valid-uuid)", set()),
        ("punctuation_adjacent_valid_markdown", "Xem:" + link_a, {a}),
        ("two_adjacent_valid_markdown_links", link_a + link_b, {a, b}),
    ]
    results = []
    for name, markdown, expected in cases:
        observed = parser(markdown)
        results.append({
            "case": name,
            "status": "PASS" if observed == expected else "FAIL",
            "expected_ids": sorted(str(value) for value in expected),
            "observed_ids": sorted(str(value) for value in observed),
        })
    return {
        "suite": "P10 isolated production function AST / no DB",
        "source": "apps/backend/catalog/groups_api.py::_inline_item_links",
        "passed": sum(row["status"] == "PASS" for row in results),
        "failed": sum(row["status"] == "FAIL" for row in results),
        "cases": results,
    }


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--strict", action="store_true", help="nonzero on a discovered regression")
    parsed = args.parse_args()
    result = evaluate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if parsed.strict and result["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
