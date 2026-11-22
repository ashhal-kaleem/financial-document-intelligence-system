"""Small CPU-only MiniLM encoder. No token, remote inference, or paid fallback."""
from functools import lru_cache
import threading
import time
from typing import List
import numpy as np
from src.infrastructure.embedding_assets import (
    ARTIFACTS, DIMENSIONS, MAX_TOKENS, MODEL_DIR, PROFILE, get_tokenizer, verify_artifact,
)

_SESSION = None
_SESSION_LOCK = threading.Lock()
# One bounded inference at a time in each warm process, including query embeddings.
_INFERENCE_LOCK = threading.Lock()


def _get_session():
    global _SESSION
    if _SESSION is None:
        with _SESSION_LOCK:
            if _SESSION is None:
                import onnxruntime as ort
                _, size, digest = ARTIFACTS["model.onnx"]
                verify_artifact(MODEL_DIR / "model.onnx", size, digest)
                opts = ort.SessionOptions()
                opts.intra_op_num_threads = 1
                opts.inter_op_num_threads = 1
                opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
                _SESSION = ort.InferenceSession(
                    str(MODEL_DIR / "model.onnx"), sess_options=opts,
                    providers=["CPUExecutionProvider"],
                )
    return _SESSION


class EmbeddingClient:
    profile = PROFILE
    batch_size = 16
    timeout_seconds = 90.0

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        tokenizer = get_tokenizer()
        encoded = tokenizer.encode_batch(texts)
        if any(not text.strip() for text in texts):
            raise ValueError("Cannot embed empty text")
        if any(len(e.ids) > MAX_TOKENS for e in encoded):
            raise ValueError("Text exceeds the embedding token limit; split it before indexing.")
        session = _get_session()
        vectors = []
        # Dynamic quantization can change activation scales when unrelated inputs share
        # a tensor. Encode each item separately so an identical doc/query text gets
        # the same vector regardless of its neighbors or upload batch boundaries.
        for enc in encoded:
            ids = np.array([enc.ids], dtype=np.int64)
            mask = np.array([enc.attention_mask], dtype=np.int64)
            types = np.array([enc.type_ids], dtype=np.int64)
            values = {"input_ids": ids, "attention_mask": mask, "token_type_ids": types}
            result = session.run(None, {i.name: values[i.name] for i in session.get_inputs()})[0]
            weights = mask[:, :, None]
            pooled = (result * weights).sum(axis=1) / np.clip(weights.sum(axis=1), 1, None)
            norms = np.linalg.norm(pooled, axis=1, keepdims=True)
            if pooled.shape != (1, DIMENSIONS) or not np.isfinite(pooled).all() or np.any(norms == 0):
                raise RuntimeError("Invalid embedding model output")
            vectors.append((pooled / norms).astype(np.float32)[0].tolist())
        return vectors

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        deadline = time.monotonic() + self.timeout_seconds
        if not _INFERENCE_LOCK.acquire(timeout=self.timeout_seconds):
            raise TimeoutError("Embedding capacity is busy. Retry later.")
        try:
            out = []
            for i in range(0, len(texts), self.batch_size):
                if time.monotonic() >= deadline:
                    raise TimeoutError("Embedding processing budget exceeded. Use a smaller document.")
                out.extend(self._embed_batch(texts[i:i + self.batch_size]))
            if time.monotonic() >= deadline:
                raise TimeoutError("Embedding processing budget exceeded. Use a smaller document.")
            return out
        finally:
            _INFERENCE_LOCK.release()

    def embed_query(self, query: str) -> List[float]:
        # A query must remain one vector. Do not silently truncate or average unrelated windows.
        return self.embed_texts([query])[0]


@lru_cache(maxsize=1)
def get_embedding_client() -> EmbeddingClient:
    return EmbeddingClient()
