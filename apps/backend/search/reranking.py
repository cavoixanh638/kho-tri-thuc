"""Locally reorder the first five PostgreSQL suggestions with the BGE cross-encoder."""

import logging
import threading
import time
from pathlib import Path

from django.conf import settings


WINDOW_SIZE = 5
EXTRA_CANDIDATES = 8
MIN_NEW_LOGIT = -2.0
MIN_LEAD = 1.0
MAX_PASSAGE_CHARS = 8192
MAX_TOKENS = 512
_RETRY_SECONDS = 30
_lock = threading.Lock()
_directory = None
_model = None
_retry_after = 0.0
log = logging.getLogger(__name__)


class _BgeReranker:
    def __init__(self, directory):
        graph = directory / "onnx" / "model_quantized.onnx"
        if not graph.is_file():
            raise FileNotFoundError("Local BGE model is unavailable")
        import numpy as np
        import onnxruntime as ort
        from tokenizers import Tokenizer

        self.np = np
        self.tokenizer = Tokenizer.from_file(str(directory / "tokenizer.json"))
        if self.tokenizer.token_to_id("<pad>") != 1:
            raise ValueError("Unexpected BGE padding token")
        self.tokenizer.enable_truncation(max_length=MAX_TOKENS)
        self.tokenizer.enable_padding(direction="right", pad_id=1, pad_token="<pad>")
        options = ort.SessionOptions()
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        options.intra_op_num_threads = 4
        options.inter_op_num_threads = 1
        options.add_session_config_entry("session.intra_op.allow_spinning", "0")
        self.session = ort.InferenceSession(str(graph), sess_options=options, providers=["CPUExecutionProvider"])
        types = {"tensor(int32)": np.int32, "tensor(int64)": np.int64}
        attrs = {"input_ids": "ids", "attention_mask": "attention_mask", "token_type_ids": "type_ids"}
        self.inputs = {node.name: (attrs[node.name], types[node.type]) for node in self.session.get_inputs()}
        if not {"input_ids", "attention_mask"} <= self.inputs.keys():
            raise ValueError("Unexpected BGE model inputs")

    def scores(self, query, passages):
        pairs = self.tokenizer.encode_batch([(query, passage) for passage in passages])
        inputs = {
            name: self.np.asarray([getattr(pair, attr) for pair in pairs], dtype=dtype)
            for name, (attr, dtype) in self.inputs.items()
        }
        logits = self.np.asarray(self.session.run(["logits"], inputs)[0])
        if logits.shape not in {(len(pairs),), (len(pairs), 1)} or not self.np.isfinite(logits).all():
            raise ValueError("Invalid BGE pair scores")
        return tuple(map(float, logits.ravel()))

    def order(self, query, passages):
        logits = self.scores(query, passages)
        # Python's stable sort preserves PostgreSQL order on tied logits.
        return tuple(sorted(range(len(logits)), key=logits.__getitem__, reverse=True))


def rerank_order(query: str, passages: list[str]) -> tuple[int, ...] | None:
    """Return a permutation, or None to retain lexical order on an unavailable model."""
    if not 2 <= len(passages) <= WINDOW_SIZE:
        return None
    return _infer(query, passages, scores=False)


def best_addition(query, original, extra):
    """Admit one challenger when it clearly outscores all the existing suggestions."""
    if not (0 < len(original) < WINDOW_SIZE and 0 < len(extra) <= EXTRA_CANDIDATES):
        return None
    logits = _infer(query, original + extra, scores=True)
    if logits is None:
        return None
    boundary = len(original)
    winner = max(range(boundary, len(logits)), key=logits.__getitem__)
    if logits[winner] >= max(MIN_NEW_LOGIT, max(logits[:boundary]) + MIN_LEAD):
        return winner - boundary
    return None


def _infer(query, passages, *, scores):
    global _directory, _model, _retry_after
    configured = settings.SEARCH_BGE_MODEL_DIR
    if not configured:
        return None
    # One session per API worker. Serialize bounded CPU batches, and keep
    # lexical requests entirely outside the lock.
    with _lock:
        if _directory != configured:
            _directory, _model, _retry_after = configured, None, 0.0
        if time.monotonic() < _retry_after:
            return None
        try:
            if _model is None:
                _model = _BgeReranker(Path(configured))
            return _model.scores(query, passages) if scores else _model.order(query, passages)
        except Exception as error:
            # Optional native libraries can also fail to initialize or run.
            # Retry transient failures; never log note text or the query.
            _model = None
            _retry_after = time.monotonic() + _RETRY_SECONDS
            log.warning("search_bge_fallback error_type=%s", type(error).__name__)
            return None
