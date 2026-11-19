"""Safety gates for the live pilot; these tests perform no network or DB writes."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from knowledge_pilot import ROOT, PilotError, validate_cases, validate_target


class PilotSafetyTests(unittest.TestCase):
    def test_rejects_production_cluster_even_with_new_database_and_loopback_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            for host in ("127.0.0.1", "localhost", "::1"):
                with (
                    self.subTest(host=host),
                    self.assertRaisesRegex(PilotError, "separate_postgres_cluster"),
                ):
                    validate_target(
                        {"host": "127.0.0.1", "port": "54329"},
                        {"host": host, "port": 54329, "dbname": "kt_pilot_fresh"},
                        Path(directory),
                    )

    def test_requires_fresh_pilot_namespace_and_loopback(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, host in (
                ("kho_tri_thuc", "127.0.0.1"),
                ("kt_pilot_x;DROP DATABASE x", "127.0.0.1"),
                ("kt_pilot_ok", "db.example.org"),
            ):
                with self.subTest(name=name, host=host), self.assertRaises(PilotError):
                    validate_target(
                        {"host": "127.0.0.1", "port": 54329},
                        {"host": host, "port": 62224, "dbname": name},
                        Path(directory),
                    )

    def test_private_receipts_cannot_be_written_inside_repo(self):
        with self.assertRaisesRegex(PilotError, "outside_git"):
            validate_target(
                {"host": "127.0.0.1", "port": 54329},
                {"host": "127.0.0.1", "port": 62224, "dbname": "kt_pilot_ok"},
                ROOT / "evals/private",
            )

    def test_accepts_separate_cluster_and_external_private_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            validate_target(
                {"host": "127.0.0.1", "port": 54329},
                {"host": "127.0.0.1", "port": 62224, "dbname": "kt_pilot_ok"},
                Path(directory),
            )

    def test_corpus_labels_and_source_allowlist(self):
        data = json.loads(
            (ROOT / "evals/knowledge/pilot-cases.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(validate_cases(data)), 8)
        for change in ("url", "note", "duplicate"):
            modified = copy.deepcopy(data)
            if change == "url":
                modified["cases"][0]["url"] = "http://127.0.0.1/private"
            elif change == "note":
                modified["cases"][4]["note"] = "unlabelled personal-looking note"
            else:
                modified["cases"][1]["key"] = modified["cases"][0]["key"]
            with self.subTest(change=change), self.assertRaises(PilotError):
                validate_cases(modified)


if __name__ == "__main__":
    unittest.main()
