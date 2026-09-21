"""In-process vector index over the `lexemas` table.

The Postgres database is owned by the Laravel app and this repo has no
migrations, so there is nowhere to persist embeddings. The index is therefore
built in memory on first use and rebuilt when the lexema set changes.
"""

import asyncio
import uuid
from dataclasses import dataclass

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


class LexemaRagService:
    def __init__(self) -> None:
        self._words: list[str] = []
        self._ids: list[uuid.UUID] = []
        self._documents: list[str] = []
        self._matrix: np.ndarray = np.empty((0, rag.EMBED_DIM), dtype=np.float32)
        self._fingerprint: tuple[int, int | None] | None = None
        self._lock = asyncio.Lock()

    @property
    def size(self) -> int:
        return len(self._ids)

    @staticmethod
    async def _current_fingerprint(db: AsyncSession) -> tuple[int, int | None]:
        """Cheap staleness probe: how many lexemas there are and the newest pk."""
        result = await db.execute(select(func.count(Lexema.pk), func.max(Lexema.pk)))
        count, max_pk = result.one()
        return int(count), max_pk

    async def ensure_index(self, db: AsyncSession) -> int:
        fingerprint = await self._current_fingerprint(db)
        if self._fingerprint == fingerprint:
            return self.size
        return await self.build_index(db)

    async def build_index(self, db: AsyncSession) -> int:
        async with self._lock:
            fingerprint = await self._current_fingerprint(db)
            result = await db.execute(select(Lexema).order_by(Lexema.pk))
            lexemas = result.scalars().all()

            documents = [
                rag.lexema_document(
                    lexema.word,
                    lexema.exercise.clause if lexema.exercise is not None else None,
                )
                for lexema in lexemas
            ]

            if documents:
                vectors = await run_in_threadpool(rag.embed_documents, documents)
                matrix = np.asarray(vectors, dtype=np.float32)
            else:
                matrix = np.empty((0, rag.EMBED_DIM), dtype=np.float32)

            self._ids = [lexema.id for lexema in lexemas]
            self._words = [lexema.word for lexema in lexemas]
            self._documents = documents
            self._matrix = matrix
            self._fingerprint = fingerprint
            return self.size

    async def retrieve(self, db: AsyncSession, query: str, k: int) -> list[RetrievedLexema]:
        await self.ensure_index(db)
        if self.size == 0:
            return []

        query_vector = await run_in_threadpool(rag.embed_query, query)
        return [
            RetrievedLexema(
                id=self._ids[i],
                word=self._words[i],
                document=self._documents[i],
                score=score,
            )
            for i, score in rag.top_k(query_vector, self._matrix, k)
        ]


lexema_rag_service = LexemaRagService()
