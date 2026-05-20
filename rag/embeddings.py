import re


def _normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower())


def _text_to_vector(text: str, dim: int = 256) -> list[float]:
    normalized = _normalize_text(text)
    tokens = [t for t in normalized.split() if t]
    if not tokens:
        return [0.0] * dim

    vector = [0.0] * dim
    for token in tokens:
        index = abs(hash(token)) % dim
        vector[index] += 1.0

    total = sum(vector)
    if total > 0:
        return [value / total for value in vector]
    return vector


class LocalEmbeddings:
    """A small local embedding fallback to avoid quota-based cloud embedding calls."""

    def __init__(self, dim: int = 256):
        self.dim = dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [_text_to_vector(text, self.dim) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return _text_to_vector(text, self.dim)
