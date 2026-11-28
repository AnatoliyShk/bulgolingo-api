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
from sqlalchemy import BigInteger, any_, bindparam, func, or_, select
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.gemini import rag
from app.exercises.models import Exercise
from app.lexemas.models import Lexema, exercise_lexema


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


# when a word was last written; Laravel sets both columns on every save
_STAMP = func.coalesce(Lexema.updated_at, Lexema.created_at)


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
        self._fingerprint: tuple[int, int | None, datetime | None] | None = None
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
    async def _current_fingerprint(db: AsyncSession) -> tuple[int, int | None, datetime | None]:
        """Cheap staleness probe: how many lexemas there are, the newest pk, and the newest
        created/updated stamp, so in-place edits (here or in Laravel) are noticed too."""
        result = await db.execute(select(func.count(Lexema.pk), func.max(Lexema.pk), func.max(_STAMP)))
        count, max_pk, newest = result.one()
        return int(count), max_pk, newest

    async def ensure_index(self, db: AsyncSession) -> int:
        """Refresh the index only if the lexemas table changed; return its size."""
        fingerprint = await self._current_fingerprint(db)
        if self._fingerprint == fingerprint:
            return self.size
        return (await self.build_index(db, only_if_stale=True)).total

    async def build_index(
        self, db: AsyncSession, since: datetime | None = None, only_if_stale: bool = False
    ) -> IndexResult:
        """Embed the lexemas and (re)build the index.

        With `since`, only lexemas touched at or after that moment are re-embedded
        and merged into the existing index; everything else keeps the vector it
        already has. A partial refresh needs something to merge into, so it falls
        back to a full rebuild when the index has not been built yet.
        """
        async with self._lock:
            fingerprint = await self._current_fingerprint(db)
            # re-checked under the lock: a request that waited here may find the index already rebuilt
            if only_if_stale and self._fingerprint == fingerprint:
                return IndexResult(embedded=0, total=self.size, partial=False)
            if only_if_stale and self.is_built and self._fingerprint[2] is not None:
                # an automatic refresh re-embeds only what changed since the last build, not the whole table
                since = self._fingerprint[2]
            partial = since is not None and self.is_built

            query = select(Lexema).order_by(Lexema.pk)
            if partial:
                existing = set((await db.execute(select(Lexema.pk))).scalars())
                # also take words the index lacks: one inserted with an older stamp would slip past `since`
                missing = bindparam("missing", sorted(existing - self._entries.keys()), type_=ARRAY(BigInteger))
                query = query.where(or_(_STAMP >= _as_naive_utc(since), Lexema.pk == any_(missing)))
            lexemas = (await db.execute(query)).scalars().all()

            # context for each word: the sentence and explanation of its oldest linked exercise, if any
            contexts = {
                lexema_pk: (prompt, explanation)
                for lexema_pk, prompt, explanation in (
                    await db.execute(
                        select(exercise_lexema.c.lexema_id, Exercise.prompt, Exercise.explanation)
                        .join(Exercise, Exercise.pk == exercise_lexema.c.exercise_id)
                        # a subquery, not a list of pks: Postgres caps a statement at 32,767 parameters
                        .where(exercise_lexema.c.lexema_id.in_(query.with_only_columns(Lexema.pk).order_by(None)))
                        .distinct(exercise_lexema.c.lexema_id)
                        .order_by(exercise_lexema.c.lexema_id, Exercise.pk)
                    )
                ).all()
            }
            documents = [rag.lexema_document(lexema.word, *contexts.get(lexema.pk, ())) for lexema in lexemas]
            vectors = await run_in_threadpool(rag.embed_documents, documents) if documents else []

            if partial:
                # drop words deleted since the last build, or they linger once the fingerprint matches
                self._entries = {pk: entry for pk, entry in self._entries.items() if pk in existing}
            else:
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
