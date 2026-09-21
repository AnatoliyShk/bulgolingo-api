"""Embedding layer for lexema-grounded retrieval.

Gemini's embedding endpoint is synchronous, so everything here is sync and is
expected to be called from a worker thread (`run_in_threadpool`) when used
inside an async route. Vectors are L2-normalised on the way in, which makes
cosine similarity a plain dot product.
"""

import numpy as np
from google import genai
from google.genai import types

from app.config import settings

client = genai.Client(api_key=settings.gemini_api_key)

EMBED_MODEL = settings.gemini_embed_model
EMBED_DIM = settings.gemini_embed_dim
BATCH_SIZE = 100


def _normalize(v) -> list[float]:
    a = np.asarray(v, dtype=np.float32)
    norm = np.linalg.norm(a)
    if norm == 0:
        return a.tolist()
    return (a / norm).tolist()  # required when output_dimensionality < native size


def embed(texts: list[str], task_type: str) -> list[list[float]]:
    out: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        resp = client.models.embed_content(
            model=EMBED_MODEL,
            contents=texts[i:i + BATCH_SIZE],
            config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=EMBED_DIM),
        )
        out += [_normalize(e.values) for e in resp.embeddings]
    return out


def embed_documents(texts: list[str]) -> list[list[float]]:
    return embed(texts, "RETRIEVAL_DOCUMENT")


def embed_query(text: str) -> list[float]:
    return embed([text], "RETRIEVAL_QUERY")[0]


def lexema_document(word: str, exercise_clause: dict | None = None) -> str:
    """The text indexed for one lexema.

    The `lexemas` table only carries the word itself, so the linked exercise's
    clause (when there is one) is folded in to give the vector some context to
    work with.
    """
    document = f"Лексема: {word}"
    if exercise_clause:
        sentence = exercise_clause.get("sentence")
        explanation = exercise_clause.get("explanation")
        context = " ".join(str(part) for part in (sentence, explanation) if part)
        if context:
            document = f"{document}. Контекст: {context}"
    return document


def top_k(query_vector: list[float], matrix: np.ndarray, k: int) -> list[tuple[int, float]]:
    """Indices and cosine scores of the `k` rows closest to `query_vector`.

    Both sides are already normalised, so the dot product is the cosine.
    """
    if matrix.size == 0 or k <= 0:
        return []
    scores = matrix @ np.asarray(query_vector, dtype=np.float32)
    k = min(k, scores.shape[0])
    best = np.argpartition(-scores, k - 1)[:k]
    best = best[np.argsort(-scores[best])]
    return [(int(i), float(scores[i])) for i in best]
