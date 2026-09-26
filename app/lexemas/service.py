"""In-process vector index over the `lexemas` table.

The Postgres database is owned by the Laravel app and this repo has no
migrations, so there is nowhere to persist embeddings. The index is therefore
built in memory on first use and rebuilt when the lexema set changes.
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.gemini import rag
from app.lexemas.models import Lexema


@dataclass
class RetrievedLexema:
    id: uuid.UUID
    word: str
    document: str
    score: float


@dataclass
class _IndexEntry:
    id: uuid.UUID
    word: str
    document: str
    vector: list[float]


@dataclass
class IndexResult:
    """What one indexing call did: how many lexemas were embedded, and the
    resulting index size. `partial` is False when the whole table was re-embedded."""

    embedded: int
    total: int
    partial: bool


def _as_naive_utc(moment: datetime) -> datetime:
    """Laravel's `timestamps()` columns are `timestamp without time zone`, so an
    aware bound has to be flattened to UTC before it can be compared."""
    if moment.tzinfo is None:
        return moment
    return moment.astimezone(timezone.utc).replace(tzinfo=None)


class LexemaRagService:
    def __init__(self) -> None:
        """Start with an empty, unbuilt index; it is filled lazily on first use."""
        self._entries: dict[int, _IndexEntry] = {}
        self._order: list[int] = []
        self._matrix: np.ndarray = np.empty((0, rag.EMBED_DIM), dtype=np.float32)
        self._fingerprint: tuple[int, int | None] | None = None
        self._lock = asyncio.Lock()

    @property
    def size(self) -> int:
        """Number of lexemas currently in the index."""
        return len(self._order)

    @property
    def is_built(self) -> bool:
        """Whether the index has been built at least once."""
        return self._fingerprint is not None

    @staticmethod
    async def _current_fingerprint(db: AsyncSession) -> tuple[int, int | None]:
        """Cheap staleness probe: how many lexemas there are and the newest pk."""
        result = await db.execute(select(func.count(Lexema.pk), func.max(Lexema.pk)))
        count, max_pk = result.one()
        return int(count), max_pk

    async def ensure_index(self, db: AsyncSession) -> int:
        """Rebuild the index only if the lexemas table changed; return its size."""
        fingerprint = await self._current_fingerprint(db)
        if self._fingerprint == fingerprint:
            return self.size
        return (await self.build_index(db)).total

    async def build_index(self, db: AsyncSession, since: datetime | None = None) -> IndexResult:
        """Embed the lexemas and (re)build the index.

        With `since`, only lexemas touched at or after that moment are re-embedded
        and merged into the existing index; everything else keeps the vector it
        already has. A partial refresh needs something to merge into, so it falls
        back to a full rebuild when the index has not been built yet.
        """
        async with self._lock:
            partial = since is not None and self.is_built
            fingerprint = await self._current_fingerprint(db)

            query = select(Lexema).order_by(Lexema.pk)
            if partial:
                query = query.where(
                    func.coalesce(Lexema.updated_at, Lexema.created_at) >= _as_naive_utc(since)
                )
            lexemas = (await db.execute(query)).scalars().all()

            documents = [
                rag.lexema_document(
                    lexema.word,
                    lexema.exercise.clause if lexema.exercise is not None else None,
                )
                for lexema in lexemas
            ]
            vectors = await run_in_threadpool(rag.embed_documents, documents) if documents else []

            if not partial:
                self._entries = {}
            for lexema, document, vector in zip(lexemas, documents, vectors):
                self._entries[lexema.pk] = _IndexEntry(
                    id=lexema.id, word=lexema.word, document=document, vector=vector
                )

            self._rebuild_matrix()
            self._fingerprint = fingerprint
            return IndexResult(embedded=len(vectors), total=self.size, partial=partial)

    def _rebuild_matrix(self) -> None:
        """Stack the entry vectors, ordered by pk, into the matrix used for search."""
        self._order = sorted(self._entries)
        if self._order:
            self._matrix = np.asarray(
                [self._entries[pk].vector for pk in self._order], dtype=np.float32
            )
        else:
            self._matrix = np.empty((0, rag.EMBED_DIM), dtype=np.float32)

    async def retrieve(self, db: AsyncSession, query: str, k: int) -> list[RetrievedLexema]:
        """Embed `query` and return the `k` most similar lexemas, best first."""
        await self.ensure_index(db)
        if self.size == 0:
            return []

        query_vector = await run_in_threadpool(rag.embed_query, query)
        retrieved = []
        for i, score in rag.top_k(query_vector, self._matrix, k):
            entry = self._entries[self._order[i]]
            retrieved.append(
                RetrievedLexema(id=entry.id, word=entry.word, document=entry.document, score=score)
            )
        return retrieved


lexema_rag_service = LexemaRagService()
