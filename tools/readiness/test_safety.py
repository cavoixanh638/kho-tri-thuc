import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run


class IsolationTests(unittest.TestCase):
    def test_refuses_normal_or_injected_database_names(self):
        for name in (
            "postgres",
            "kho_tri_thuc",
            "kt_readiness_x;DROP",
            "kt_readiness_",
            "kt_readiness_" + "x" * 41,
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                run.safe_database(name)
        self.assertEqual(
            run.safe_database("kt_readiness_fixture_restore"),
            "kt_readiness_fixture_restore",
        )

    def test_refuses_serving_port_and_missing_password(self):
        for values in (
            {"KT_READINESS_PORT": "54329", "KT_READINESS_PASSWORD": "fixture"},
            {},
        ):
            with (
                self.subTest(values=values),
                patch.dict(os.environ, values, clear=True),
                self.assertRaises(ValueError),
            ):
                run.connection_args()

    def test_private_backup_must_be_new_and_outside_git(self):
        with self.assertRaises(ValueError):
            run.safe_work(run.ROOT / "private-bundle")
        with tempfile.TemporaryDirectory() as parent:
            with self.assertRaises(ValueError):
                run.safe_work(parent)
            self.assertEqual(
                run.safe_work(Path(parent) / "new"), (Path(parent) / "new").resolve()
            )


if __name__ == "__main__":
    unittest.main()
