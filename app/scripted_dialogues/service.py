"""Builds a determined (fully scripted) Bulgarian dialogue tree with Gemini.

"Determined" means the tree is materialised up front: every node has a fixed
set of learner replies, each leading to an already-generated child node, so the
runtime never has to call the model again. Generation is grounded in lexemas
retrieved from the database (RAG) and runs at temperature 0 with a fixed seed,
so the same request over the same vocabulary yields the same tree.
"""

import json
from datetime import datetime, timezone

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.auth.models import User
from app.config import settings
from app.rag.schemas import (
    DialogueNode,
    DialogueReply,
    DialogueTreeOut,
    DialogueTreeRequest,
    RetrievedLexemaOut,
    node_count,
)
from app.scripted_dialogues.models import ScriptedDialogue
from app.scripted_lines.models import ScriptedLine
from app.lexemas.rag_service import LexemaRagService, RetrievedLexema, lexema_rag_service

SEED = 7


class TreeGenerationError(RuntimeError):
    """The model could not be coaxed into returning a usable tree."""


class _GeneratedNode(BaseModel):
    """One node as the model returns it: flat, with a parent pointer.

    Empty strings rather than nulls keep the response schema free of nullable
    fields, which the model handles far more reliably.
    """

    id: str
    parent_id: str
    option_bg: str
    option_en: str
    line_bg: str
    line_en: str
    lexemas: list[str]


class _GeneratedTree(BaseModel):
    title_bg: str
    title_en: str
    nodes: list[_GeneratedNode]


class DialogueTreeService:
    def __init__(self, rag_service: LexemaRagService = lexema_rag_service) -> None:
        self.rag_service = rag_service
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    async def generate(
        self,
        db: AsyncSession,
        request: DialogueTreeRequest,
        current_user: User,
    ) -> DialogueTreeOut:
        lexemas = await self.rag_service.retrieve(db, self._retrieval_query(request), request.lexemas)
        if not lexemas:
            raise TreeGenerationError("No lexemas in the database to ground the dialogue on")

        prompt = self._build_prompt(request, lexemas)
        generated = await self._generate_tree(prompt, request)
        root = self._assemble(generated, request)

        tree = DialogueTreeOut(
            title_bg=generated.title_bg,
            title_en=generated.title_en,
            topic=request.topic,
            level=request.level,
            depth=request.depth,
            branching=request.branching,
            lexemas=[
                RetrievedLexemaOut(id=lexema.id, word=lexema.word, score=lexema.score)
                for lexema in lexemas
            ],
            root=root,
        )

        if request.bot_id is not None:
            tree.dialogue_id = await self._persist(db, tree, generated, request, current_user)
        return tree

    @staticmethod
    def _retrieval_query(request: DialogueTreeRequest) -> str:
        return f"Тема: {request.topic}. Ниво: {request.level}. Диалог на български език."

    @staticmethod
    def _build_prompt(request: DialogueTreeRequest, lexemas: list[RetrievedLexema]) -> str:
        vocabulary = "\n".join(f"- {lexema.word} ({lexema.document})" for lexema in lexemas)
        return (
            "You are a Bulgarian language teacher writing a scripted branching dialogue "
            f"for a CEFR {request.level} learner.\n\n"
            f"Topic: {request.topic}\n\n"
            "Ground the dialogue in these lexemas from the learner's vocabulary database and "
            "reuse as many of them as sounds natural:\n"
            f"{vocabulary}\n\n"
            f"Build a COMPLETE tree exactly {request.depth} levels deep in which every node above "
            f"the deepest level has EXACTLY {request.branching} children "
            f"({node_count(request.depth, request.branching)} nodes in total).\n\n"
            "Rules for each node:\n"
            '- "id": the root is "n1"; every child appends its 1-based position to its parent id '
            '("n1.1", "n1.2", "n1.1.1", ...).\n'
            '- "parent_id": the id of the parent node, or an empty string for the root.\n'
            '- "line_bg" / "line_en": what the conversation partner says at this node, in Bulgarian '
            "and its English translation.\n"
            '- "option_bg" / "option_en": the learner\'s reply that leads TO this node, in Bulgarian '
            "and English; an empty string for the root.\n"
            '- "lexemas": the listed lexema words actually used in this node.\n\n'
            "Return every node in one flat list, parents before children. Keep the Bulgarian natural "
            f"and at {request.level}; the English must be a faithful translation, not word-for-word."
        )

    async def _generate_tree(self, prompt: str, request: DialogueTreeRequest) -> _GeneratedTree:
        """One generation, plus a second attempt that feeds the fault back to the model."""
        attempt_prompt = prompt
        last_error: Exception | None = None

        for _ in range(2):
            try:
                generated = await run_in_threadpool(self._call_gemini, attempt_prompt)
                self._validate(generated, request)
                return generated
            except (TreeGenerationError, ValidationError, json.JSONDecodeError) as exc:
                last_error = exc
                attempt_prompt = (
                    f"{prompt}\n\nYour previous answer was rejected: {exc}. "
                    "Return the corrected tree."
                )
            except errors.APIError as exc:
                raise TreeGenerationError(f"Gemini request failed: {exc}") from exc

        raise TreeGenerationError(f"Gemini returned an unusable tree: {last_error}")

    def _call_gemini(self, prompt: str) -> _GeneratedTree:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_GeneratedTree,
                temperature=0.0,
                seed=SEED,
            ),
        )
        return _GeneratedTree.model_validate_json(response.text)

    @staticmethod
    def _validate(generated: _GeneratedTree, request: DialogueTreeRequest) -> None:
        nodes = {node.id: node for node in generated.nodes}
        if len(nodes) != len(generated.nodes):
            raise TreeGenerationError("node ids are not unique")

        roots = [node for node in generated.nodes if not node.parent_id]
        if len(roots) != 1:
            raise TreeGenerationError(f"expected exactly 1 root node, got {len(roots)}")

        children: dict[str, list[_GeneratedNode]] = {node_id: [] for node_id in nodes}
        for node in generated.nodes:
            if node.parent_id and node.parent_id not in nodes:
                raise TreeGenerationError(f"node {node.id!r} points at unknown parent {node.parent_id!r}")
            if node.parent_id:
                children[node.parent_id].append(node)

        seen: set[str] = set()
        level = [roots[0]]
        for depth in range(1, request.depth + 1):
            expected = 0 if depth == request.depth else request.branching
            next_level: list[_GeneratedNode] = []
            for node in level:
                if node.id in seen:
                    raise TreeGenerationError(f"node {node.id!r} is reachable twice")
                seen.add(node.id)
                if len(children[node.id]) != expected:
                    raise TreeGenerationError(
                        f"node {node.id!r} at depth {depth} has {len(children[node.id])} children, "
                        f"expected {expected}"
                    )
                next_level += children[node.id]
            level = next_level

        if len(seen) != len(nodes):
            unreachable = sorted(set(nodes) - seen)
            raise TreeGenerationError(f"nodes not reachable from the root: {unreachable}")

    @staticmethod
    def _assemble(generated: _GeneratedTree, request: DialogueTreeRequest) -> DialogueNode:
        """Turn the validated flat list into the nested tree, children in id order."""
        children: dict[str, list[_GeneratedNode]] = {node.id: [] for node in generated.nodes}
        root = next(node for node in generated.nodes if not node.parent_id)
        for node in generated.nodes:
            if node.parent_id:
                children[node.parent_id].append(node)

        def build(node: _GeneratedNode) -> DialogueNode:
            return DialogueNode(
                id=node.id,
                line_bg=node.line_bg,
                line_en=node.line_en,
                lexemas=node.lexemas,
                replies=[
                    DialogueReply(
                        option_bg=child.option_bg,
                        option_en=child.option_en,
                        next=build(child),
                    )
                    for child in sorted(children[node.id], key=lambda c: c.id)
                ],
            )

        return build(root)

    @staticmethod
    async def _persist(
        db: AsyncSession,
        tree: DialogueTreeOut,
        generated: _GeneratedTree,
        request: DialogueTreeRequest,
        current_user: User,
    ):
        """Store the tree as a scripted dialogue, one scripted line per node.

        `scripted_lines` has no ordering column, so each line's `clause` carries
        the node id and parent id; that is what makes the tree reconstructible.
        """
        now = datetime.now(timezone.utc)
        dialogue = ScriptedDialogue(
            bot_id=request.bot_id,
            user_pk=current_user.pk,
            created_at=now,
        )
        db.add(dialogue)
        await db.flush()

        for node in sorted(generated.nodes, key=lambda n: n.id):
            db.add(
                ScriptedLine(
                    dialogue_pk=dialogue.pk,
                    clause={
                        "id": node.id,
                        "parent_id": node.parent_id or None,
                        "option_bg": node.option_bg or None,
                        "option_en": node.option_en or None,
                        "line_bg": node.line_bg,
                        "line_en": node.line_en,
                        "lexemas": node.lexemas,
                        "topic": tree.topic,
                        "level": tree.level,
                    },
                    created_at=now,
                )
            )

        await db.commit()
        await db.refresh(dialogue)
        return dialogue.id
