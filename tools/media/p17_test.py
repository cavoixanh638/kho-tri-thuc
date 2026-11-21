"""Independent P17 regression tests. Run: python -m unittest discover -s tools/media -p 'p17_test.py' -v"""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

FILE = Path(__file__).with_name("p17_media_eval.py")
SPEC = importlib.util.spec_from_file_location("p17_media_eval", FILE)
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


class FixtureAndOracleTests(unittest.TestCase):
    def test_sources_50_distinct_three_platforms(self):
        rows = json.loads((module.FIXTURES/"sources.json").read_text())
        self.assertEqual(len(rows), 50)
        self.assertEqual(len({r["url"] for r in rows}), 50)
        self.assertEqual(set(r["platform"] for r in rows), {"facebook","youtube","tiktok"})

    def test_faults_20_or_more_distinct(self):
        rows = json.loads((module.FIXTURES/"faults.json").read_text())
        self.assertGreaterEqual(len(rows), 20)
        self.assertEqual(len({r["id"] for r in rows}), len(rows))
        self.assertEqual(set(r["kind"] for r in rows),
                         {"manifest","readback_oracle","retry_policy_mirror"})

    def test_no_metadata_or_db_flag_substitutes_full_drive_readback(self):
        fixtures = json.loads((module.FIXTURES/"faults.json").read_text())
        cases = [r for r in fixtures if r["kind"] == "readback_oracle"]
        self.assertGreaterEqual(len(cases), 20)
        for case in cases:
            with self.subTest(case=case["injection"]):
                self.assertEqual(module.readback(case["injection"]),
                                 case["injection"] == "valid_full_readback")

    def test_states(self):
        rows = json.loads((module.FIXTURES/"states.json").read_text())
        self.assertGreaterEqual(len({r["state"] for r in rows}), 6)
        for r in rows:
            if r["state"] == "metadata_only":
                self.assertFalse(r["media_bytes"])
                self.assertFalse(r["readback_sha_verified"])

    def test_no_live_readback_claim(self):
        self.assertTrue(module.proof())
        self.assertFalse(module.proof(remote=None))
        self.assertFalse(module.proof(remote_sha=""))
        self.assertFalse(module.proof(remote_owner="another"))
        self.assertFalse(module.proof(complete=False))

    @unittest.skipUnless((module.ROOT/"apps/backend/processing/video_download.py").exists(),
                         "Repository production source unavailable; source-bound checks NOT_RUN")
    def test_production_source_bound(self):
        result = module.evaluate()
        self.assertEqual(result["status"], "PASS", result["faults"]["failures"])
        self.assertEqual(result["sources"]["total"], 50)
        self.assertEqual(result["faults"]["total"], 47)
        self.assertEqual(result["synthetic_metadata"]["items"], 10000)


if __name__ == "__main__":
    unittest.main()
