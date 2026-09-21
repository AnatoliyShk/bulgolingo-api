from uuid import UUID

from pydantic import BaseModel, Field, model_validator

MAX_NODES = 40


def node_count(depth: int, branching: int) -> int:
    """Nodes in a complete tree of `depth` levels with `branching` children each."""
    if branching == 1:
        return depth
    return (branching ** depth - 1) // (branching - 1)


class DialogueTreeRequest(BaseModel):
    topic: str = Field(min_length=1)
    level: str = Field("A1", pattern="^[ABC][12]$")
    depth: int = Field(3, ge=1, le=5)
    branching: int = Field(2, ge=1, le=4)
    lexemas: int = Field(12, ge=1, le=50, description="How many lexemas to retrieve as context")
    bot_id: int | None = Field(None, description="When set, the tree is stored as a scripted dialogue")

    @model_validator(mode="after")
    def _check_size(self) -> "DialogueTreeRequest":
        total = node_count(self.depth, self.branching)
        if total > MAX_NODES:
            raise ValueError(
                f"depth={self.depth} with branching={self.branching} needs {total} nodes, "
                f"the limit is {MAX_NODES}"
            )
        return self


class RetrievedLexemaOut(BaseModel):
    id: UUID
    word: str
    score: float


class DialogueReply(BaseModel):
    """A fixed reply the learner can pick, and the node it leads to."""

    option_bg: str
    option_en: str
    next: "DialogueNode"


class DialogueNode(BaseModel):
    id: str
    line_bg: str
    line_en: str
    lexemas: list[str]
    replies: list[DialogueReply]


class DialogueTreeOut(BaseModel):
    title_bg: str
    title_en: str
    topic: str
    level: str
    depth: int
    branching: int
    lexemas: list[RetrievedLexemaOut]
    root: DialogueNode
    dialogue_id: UUID | None = None


class LexemaIndexOut(BaseModel):
    indexed: int
