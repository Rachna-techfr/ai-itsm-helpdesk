from __future__ import annotations

import hashlib
import math
import re
from collections import Counter

STOP = {
    "a", "an", "the", "to", "of", "for", "and", "or", "on", "in", "my", "i", "im",
    "is", "it", "this", "that", "with", "after", "from", "at", "be", "was", "were",
    "are", "am", "do", "does", "how", "what", "when", "where", "why", "please",
    "me", "we", "our", "your", "you", "can", "cant", "cannot", "not", "into",
    "about", "have", "has", "had", "if", "so", "than", "then", "just", "its",
    "since", "because", "would", "could", "should", "will", "keep", "keeps",
}


def tokenize(text: str) -> list[str]:
    cleaned = text.lower().replace("'", "").replace("'", "").replace("'", "")
    parts = re.findall(r"[a-z0-9]+", cleaned)
    kept: list[str] = []
    for part in parts:
        if part in STOP or len(part) == 1:
            continue
        if part.isdigit() and len(part) < 3:
            continue
        kept.append(part)
    bigrams = [f"{left}_{right}" for left, right in zip(kept, kept[1:])]
    return kept + bigrams


def cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    if not any(left) or not any(right):
        return 0.0
    return float(sum(a * b for a, b in zip(left, right)))


class Embedder:
    """Dense embedder. Uses all-MiniLM-L6-v2 when it loads, otherwise hashed TF-IDF."""

    def __init__(self, backend: str = "auto", dim: int = 384):
        self.dim = dim
        self.idf: dict[str, float] = {}
        self.kind = "hash-tfidf-v1"
        self.note = "Deterministic hashed TF-IDF over the seeded knowledge base. No model download."
        self._model = None
        choice = (backend or "auto").lower()
        if choice == "hash-tfidf":
            return
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            probe = self._model.encode("vpn", normalize_embeddings=True)
            self.dim = int(len(probe))
            self.kind = "all-MiniLM-L6-v2"
            self.note = "sentence-transformers all-MiniLM-L6-v2, normalized for cosine search."
        except Exception as exc:  # pragma: no cover - depends on optional install
            self._model = None
            self.kind = "hash-tfidf-v1"
            self.note = f"MiniLM unavailable ({exc.__class__.__name__}). Using hashed TF-IDF."

    def fit(self, texts: list[str]) -> None:
        if self._model is not None:
            self.idf = {}
            return
        docs = [tokenize(text) for text in texts]
        dfs: Counter[str] = Counter()
        for tokens in docs:
            dfs.update(set(tokens))
        count = max(len(docs), 1)
        self.idf = {term: math.log((1 + count) / (1 + freq)) + 1.0 for term, freq in dfs.items()}

    def embed(self, text: str) -> list[float]:
        if self._model is not None:
            vector = self._model.encode(text, normalize_embeddings=True)
            return [float(value) for value in vector]
        return self._hash_embed(text)

    def _hash_embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        counts = Counter(tokenize(text))
        for term, count in counts.items():
            if self.idf and term not in self.idf:
                continue
            weight = (1.0 + math.log(count)) * self.idf.get(term, 1.0)
            digest = hashlib.sha256(term.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "little") % self.dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign * weight
            bucket_two = int.from_bytes(digest[5:9], "little") % self.dim
            sign_two = 1.0 if digest[9] % 2 == 0 else -1.0
            vector[bucket_two] += sign_two * weight * 0.5
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        if not any(vector):
            return vector
        return [value / norm for value in vector]


def retrieval_confidence(score: float) -> float:
    if score <= 0:
        return 0.08
    scaled = 0.42 + score * 1.05
    return round(min(0.94, max(0.08, scaled)), 2)
