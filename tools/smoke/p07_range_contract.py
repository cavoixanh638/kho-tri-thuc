"""Offline P07 range contract check without starting Django or accessing Drive.

Usage: python tools/smoke/p07_range_contract.py
Run the Django/DB integration tests separately in a disposable QA PostgreSQL.
"""

import ast
import re
import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
VIEWER = REPO / "apps/backend/storage/viewer_api.py"
module = ast.parse(VIEWER.read_text(encoding="utf-8"), filename=str(VIEWER))
selected = next(
    node for node in module.body
    if isinstance(node, ast.FunctionDef) and node.name == "selected_range"
)
selected.decorator_list = []
compiled = compile(ast.Module(body=[selected], type_ignores=[]), str(VIEWER), "exec")
namespace = {"re": re, "MAX_RANGE": 4 * 1024 * 1024}
exec(compiled, namespace)
selected_range = namespace["selected_range"]
MAX_RANGE = namespace["MAX_RANGE"]


class RangeContract(unittest.TestCase):
    def test_valid(self):
        for header, size, answer in [
            ("bytes=0-0", 10, (0, 0, True)),
            ("bytes=3-8", 10, (3, 8, True)),
            ("bytes=7-", 10, (7, 9, True)),
            ("bytes=-5", 10, (5, 9, True)),
            ("bytes=-100", 10, (0, 9, True)),
            ("bytes=3-100", 10, (3, 9, True)),
            ("bytes=0-", MAX_RANGE * 25, (0, MAX_RANGE - 1, True)),
            ("bytes=100-", MAX_RANGE * 25, (100, 100 + MAX_RANGE - 1, True)),
            (None, 10, (0, 9, False)),
        ]:
            with self.subTest(header=header, size=size):
                self.assertEqual(selected_range(header, size), answer)

    def test_invalid(self):
        size = MAX_RANGE * 25
        for header, expected in [
            ("bytes=-", "viewer_range_invalid"),
            ("bytes=-0", "viewer_range_invalid"),
            ("bytes=0-1,2-3", "viewer_range_invalid"),
            ("bytes=100-99", "viewer_range_invalid"),
            ("bytes=999999999-", "viewer_range_invalid"),
            ("bytes=-6291456", "viewer_range_too_large"),
            (f"bytes=0-{MAX_RANGE}", "viewer_range_too_large"),
            (None, "viewer_range_required"),
        ]:
            with self.subTest(header=header):
                with self.assertRaisesRegex(ValueError, "^" + expected + "$"):
                    selected_range(header, size)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(RangeContract)
    )
    sys.exit(0 if result.wasSuccessful() else 1)
