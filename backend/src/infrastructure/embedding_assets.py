"""Pinned public model artifacts. Runtime never downloads a model or calls inference APIs."""
from functools import lru_cache
import hashlib
from pathlib import Path

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
PROFILE = "minilm-l6-v2:1110a243:quint8-avx2:single-mean-l2:256:v1"
DIMENSIONS = 384
MAX_TOKENS = 256
MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "minilm-v1"
ARTIFACTS = {
    "model.onnx": ("onnx/model_quint8_avx2.onnx", 23046789,
                   "b941bf19f1f1283680f449fa6a7336bb5600bdcd5f84d10ddc5cd72218a0fd21"),
    "tokenizer.json": ("tokenizer.json", 466247,
                       "be50c3628f2bf5bb5e3a7f17b1f74611b2561a3a27eeab05e5aa30f411572037"),
}


def verify_artifact(path: Path, size: int, digest: str) -> None:
    if not path.is_file() or path.stat().st_size != size:
        raise RuntimeError("Embedding model assets missing. Run scripts/fetch_embedding_model.py at build time.")
    with path.open("rb") as handle:
        actual = hashlib.file_digest(handle, "sha256").hexdigest() if hasattr(hashlib, "file_digest") else hashlib.sha256(handle.read()).hexdigest()
    if actual != digest:
        raise RuntimeError("Embedding model integrity check failed. Rebuild from pinned artifacts.")


@lru_cache(maxsize=1)
def get_tokenizer():
    from tokenizers import Tokenizer
    _, size, digest = ARTIFACTS["tokenizer.json"]
    verify_artifact(MODEL_DIR / "tokenizer.json", size, digest)
    tokenizer = Tokenizer.from_file(str(MODEL_DIR / "tokenizer.json"))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    return tokenizer


def split_embedding_text(text: str, overlap: int = 32) -> list[str]:
    """Use original character offsets, never drop a financial suffix by truncating tokens."""
    if not text.strip():
        return []
    tokenizer = get_tokenizer()
    encoded = tokenizer.encode(text, add_special_tokens=False)
    capacity = MAX_TOKENS - tokenizer.num_special_tokens_to_add(False)
    if not 0 <= overlap < capacity:
        raise ValueError("Invalid token overlap")
    if len(encoded.ids) <= capacity:
        return [text]
    parts = []
    start = 0
    while start < len(encoded.ids):
        stop = min(start + capacity, len(encoded.ids))
        begin_char = encoded.offsets[start][0]
        end_char = encoded.offsets[stop - 1][1]
        part = text[begin_char:end_char]
        # Offset windows can tokenize differently at a word boundary. Shrink safely if needed.
        while len(tokenizer.encode(part).ids) > MAX_TOKENS and stop > start + 1:
            stop -= 1
            end_char = encoded.offsets[stop - 1][1]
            part = text[begin_char:end_char]
        if not part or len(tokenizer.encode(part).ids) > MAX_TOKENS:
            raise ValueError("Text cannot be split into supported embedding tokens")
        parts.append(part)
        if stop == len(encoded.ids):
            break
        start = max(start + 1, stop - overlap)
    return parts
