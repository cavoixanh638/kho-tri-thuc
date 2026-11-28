"""Local ONNX models for the Vietnamese search pilot."""

import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer


MAX_TOKENS = 512  # Includes special tokens and both sides of a reranker pair.
EMBEDDING_DIMENSION = 1024
PAD_TOKEN_ID = 1


class _OnnxModel:
    def __init__(self, directory: Path, graph_path: Path, threads: int):
        if threads < 1:
            raise ValueError("CPU thread count must be at least 1")

        self.tokenizer = Tokenizer.from_file(str(directory / "tokenizer.json"))
        if self.tokenizer.token_to_id("<pad>") != PAD_TOKEN_ID:
            raise ValueError(f"Expected XLM-R pad token ID {PAD_TOKEN_ID} in {directory}")
        self.tokenizer.enable_truncation(max_length=MAX_TOKENS)
        self.tokenizer.enable_padding(direction="right", pad_id=PAD_TOKEN_ID, pad_token="<pad>")

        options = ort.SessionOptions()
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        options.inter_op_num_threads = 1
        options.intra_op_num_threads = threads
        options.add_session_config_entry("session.intra_op.allow_spinning", "0")
        self.session = ort.InferenceSession(
            str(graph_path), sess_options=options, providers=["CPUExecutionProvider"]
        )
        self.inputs = {}
        for node in self.session.get_inputs():
            if node.name not in {"input_ids", "attention_mask", "token_type_ids"}:
                raise ValueError(f"Unsupported ONNX input {node.name!r} in {graph_path}")
            if node.type not in {"tensor(int32)", "tensor(int64)"}:
                raise ValueError(f"Unsupported ONNX input type {node.type!r} in {graph_path}")
            self.inputs[node.name] = np.int32 if node.type == "tensor(int32)" else np.int64
        if not {"input_ids", "attention_mask"} <= self.inputs.keys():
            raise ValueError(f"Expected input_ids and attention_mask in {graph_path}")
        self.outputs = {node.name for node in self.session.get_outputs()}

    def _run(self, batch: list, output: str) -> np.ndarray:
        encoded = self.tokenizer.encode_batch(batch)
        attributes = {
            "input_ids": "ids",
            "attention_mask": "attention_mask",
            "token_type_ids": "type_ids",
        }
        inputs = {
            name: np.asarray([getattr(entry, attributes[name]) for entry in encoded], dtype=dtype)
            for name, dtype in self.inputs.items()
        }
        values = np.asarray(self.session.run([output], inputs)[0], dtype=np.float32)
        if not np.isfinite(values).all():
            raise ValueError(f"ONNX output {output!r} contains non-finite values")
        return values


class Embedding(_OnnxModel):
    def __init__(self, model_directory: str | Path, threads: int = 4):
        directory = Path(model_directory) / "embedding"
        pooling_path = directory / "1_Pooling" / "config.json"
        pooling = json.loads(pooling_path.read_text(encoding="utf-8"))
        if (
            pooling.get("word_embedding_dimension") != EMBEDDING_DIMENSION
            or pooling.get("pooling_mode_cls_token") is not True
            or any(
                enabled
                for key, enabled in pooling.items()
                if key.startswith("pooling_mode_") and key != "pooling_mode_cls_token"
            )
        ):
            raise ValueError(f"Expected 1024-dimensional CLS-only pooling in {pooling_path}")
        modules_path = directory / "modules.json"
        modules = json.loads(modules_path.read_text(encoding="utf-8"))
        if not any(module.get("type") == "sentence_transformers.models.Normalize" for module in modules):
            raise ValueError(f"Expected a Normalize module in {modules_path}")

        graph_path = directory / "onnx" / "model.onnx"
        weights_path = graph_path.with_suffix(".onnx_data")
        if not weights_path.is_file():
            raise FileNotFoundError(f"Missing external ONNX weights: {weights_path}")
        super().__init__(directory, graph_path, threads)
        if "sentence_embedding" in self.outputs:
            self.output = "sentence_embedding"
        elif "last_hidden_state" in self.outputs:
            self.output = "last_hidden_state"
        else:
            raise ValueError(f"Expected sentence_embedding or last_hidden_state in {graph_path}")

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, EMBEDDING_DIMENSION), dtype=np.float32)
        vectors = self._run(texts, self.output)
        if self.output == "last_hidden_state":
            if vectors.ndim != 3 or vectors.shape[1] == 0:
                raise ValueError(f"Unexpected last_hidden_state shape: {vectors.shape}")
            vectors = vectors[:, 0, :]
        if vectors.shape != (len(texts), EMBEDDING_DIMENSION):
            raise ValueError(f"Unexpected embedding shape: {vectors.shape}")
        norms = np.linalg.norm(vectors.astype(np.float64), axis=1, keepdims=True)
        if np.any(norms == 0):
            raise ValueError("ONNX embedding contains a zero vector")
        return (vectors / norms).astype(np.float32)


class Reranker(_OnnxModel):
    def __init__(self, model_directory: str | Path, threads: int = 4):
        directory = Path(model_directory) / "reranker"
        config_path = directory / "config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config.get("model_type") != "xlm-roberta" or config.get("pad_token_id") != PAD_TOKEN_ID:
            raise ValueError(f"Expected an XLM-R sequence classifier in {config_path}")
        graph_path = directory / "onnx" / "model_quantized.onnx"
        super().__init__(directory, graph_path, threads)
        if "logits" not in self.outputs:
            raise ValueError(f"Expected logits in {graph_path}")

    def score(self, query: str, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty(0, dtype=np.float32)
        logits = self._run([(query, passage) for passage in texts], "logits")
        if logits.shape == (len(texts), 1):
            return logits[:, 0]
        if logits.shape == (len(texts),):
            return logits
        raise ValueError(f"Unexpected reranker logits shape: {logits.shape}")
