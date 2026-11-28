"""Tests for the offline and download paths of model provisioning."""

import hashlib
import io
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from search import prepare_bge


class PrepareBgeTests(TestCase):
    filename = "onnx/model_quantized.onnx"
    content = b"pinned model fixture"

    def setUp(self):
        pin = (len(self.content), hashlib.sha256(self.content).hexdigest())
        patched_pins = patch.dict(prepare_bge.MODEL_FILES, {self.filename: pin}, clear=True)
        patched_pins.start()
        self.addCleanup(patched_pins.stop)
        self.directory = Path(self.enterContext(TemporaryDirectory()))
        self.model_dir = self.directory / "models"
        self.target = self.model_dir / self.filename

    def test_download_and_reuse_verified_file(self):
        with patch.object(prepare_bge, "urlopen", return_value=io.BytesIO(self.content)) as download:
            prepare_bge.provision(self.model_dir)
            prepare_bge.provision(self.model_dir)

        download.assert_called_once_with(f"{prepare_bge.MODEL_BASE_URL}/{self.filename}", timeout=30)
        self.assertEqual(self.target.read_bytes(), self.content)
        self.assertEqual(list(self.target.parent.iterdir()), [self.target])

    def test_rejects_bad_hash_and_preserves_existing_file(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b"existing model")
        corrupted = b"!" + self.content[1:]
        with patch.object(prepare_bge, "urlopen", return_value=io.BytesIO(corrupted)):
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                prepare_bge.provision(self.model_dir)

        self.assertEqual(self.target.read_bytes(), b"existing model")
        self.assertEqual(list(self.target.parent.iterdir()), [self.target])

    def test_offline_provisioning_repairs_invalid_file_without_network(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b"bad")
        source_dir = self.directory / "source"
        source = source_dir / self.filename
        source.parent.mkdir(parents=True)
        source.write_bytes(self.content)

        with patch.object(prepare_bge, "urlopen") as download:
            prepare_bge.provision(self.model_dir, source_dir)

        download.assert_not_called()
        self.assertEqual(self.target.read_bytes(), self.content)

    def test_explicit_empty_directory_disables_download(self):
        with patch.dict(os.environ, {"SEARCH_BGE_MODEL_DIR": ""}):
            self.assertIsNone(prepare_bge.model_directory())
