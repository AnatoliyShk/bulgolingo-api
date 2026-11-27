"""Rules that break silently: the dialogue-tree validator, dialogue ownership, and the exercise clause shape."""

import pytest
from sqlalchemy.dialects import postgresql

from app.auth.models import ADMIN_ROLE_ID, User
from app.exercises.models import Exercise, ExerciseOption, ExerciseWordPair
from app.rag.schemas import DialogueTreeRequest
from app.scripted_dialogues.models import ScriptedDialogue
from app.scripted_dialogues.service import DialogueTreeService, TreeGenerationError, _GeneratedNode, _GeneratedTree


def _node(node_id: str, parent_id: str = "") -> _GeneratedNode:
    return _GeneratedNode(
        id=node_id, parent_id=parent_id, option_bg="", option_en="", line_bg="Здравей", line_en="Hi", lexemas=[]
    )


def _full_tree() -> list[_GeneratedNode]:
    """depth 3, branching 2: n1 -> n1.1, n1.2 -> four leaves."""
    nodes = [_node("n1")]
    for child in ("n1.1", "n1.2"):
        nodes.append(_node(child, "n1"))
        nodes += [_node(f"{child}.{i}", child) for i in (1, 2)]
    return nodes


REQUEST = DialogueTreeRequest(topic="кафе", depth=3, branching=2)


def test_validate_accepts_a_complete_tree():
    DialogueTreeService._validate(_GeneratedTree(title_bg="", title_en="", nodes=_full_tree()), REQUEST)


@pytest.mark.parametrize(
    "nodes, fault",
    [
        ([n for n in _full_tree() if n.id != "n1.2.2"], "has 1 children, expected 2"),
        (_full_tree() + [_node("n2")], "expected exactly 1 root"),
        (_full_tree() + [_node("n1.1.1.1", "n1.1.1")], "has 1 children, expected 0"),
        (_full_tree() + [_node("n9", "nope")], "unknown parent"),
    ],
    ids=["missing child", "two roots", "too deep", "orphan"],
)
def test_validate_rejects_a_broken_tree(nodes, fault):
    with pytest.raises(TreeGenerationError, match=fault):
        DialogueTreeService._validate(_GeneratedTree(title_bg="", title_en="", nodes=nodes), REQUEST)


def _where(user: User) -> str:
    clause = ScriptedDialogue.visible_to(user)
    return str(clause.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


def test_students_only_see_their_own_dialogues():
    assert _where(User(pk=5, role_id=1)) == "scripted_dialogues.user_id = 5"


def test_admins_see_every_dialogue():
    assert _where(User(pk=5, role_id=ADMIN_ROLE_ID)) == "true"


def _options(texts: list[str], correct: int) -> list[ExerciseOption]:
    return [ExerciseOption(position=i, text=t, is_correct=i == correct) for i, t in enumerate(texts)]


# Expected shapes are copied from rows of Laravel's legacy `clause` column, which match its storedClause().
@pytest.mark.parametrize(
    "exercise, expected",
    [
        (
            Exercise(
                decision_type="fill_in_the_blank",
                prompt="Цената __ ДДС.",
                explanation="The price includes VAT.",
                options=_options(["включена", "включи", "включва"], 2),
            ),
            {
                "sentence": "Цената __ ДДС.",
                "options": ["включена", "включи", "включва"],
                "correct_option": 2,
                "explanation": "The price includes VAT.",
            },
        ),
        (
            Exercise(
                decision_type="image_matching",
                prompt=None,
                explanation="Зелен is green.",
                options=_options(["Розовото прасе.", "Зеленият огър."], 1),
            ),
            {"options": ["Розовото прасе.", "Зеленият огър."], "correct_option": 1, "explanation": "Зелен is green."},
        ),
        (
            Exercise(
                decision_type="true_false",
                prompt="Vitosha is next to Sofia.",
                statement_is_true=True,
                explanation="Correct.",
            ),
            {"sentence": "Vitosha is next to Sofia.", "correct_option": True, "explanation": "Correct."},
        ),
        (
            Exercise(
                decision_type="multiple_choice",
                explanation="Match the adjectives.",
                word_pairs=[
                    ExerciseWordPair(position=0, term="тих", translation="Quiet"),
                    ExerciseWordPair(position=1, term="скъп", translation="Expensive"),
                ],
            ),
            {"pairs": [["Quiet", "тих"], ["Expensive", "скъп"]], "explanation": "Match the adjectives."},
        ),
        (
            Exercise(
                decision_type="multiple_choice",
                explanation="",
                word_pairs=[
                    ExerciseWordPair(position=0, term="тих", translation="Quiet", left_position=1, right_position=0),
                    ExerciseWordPair(position=1, term="скъп", translation="Expensive", left_position=0, right_position=1),
                ],
            ),
            {
                "pairs": [["Quiet", "тих"], ["Expensive", "скъп"]],
                "order": {"left": [1, 0], "right": [0, 1]},
                "explanation": "",
            },
        ),
    ],
    ids=["fill_in_the_blank", "image_matching", "true_false", "multiple_choice", "multiple_choice with board order"],
)
def test_exercise_clause_matches_laravel(exercise, expected):
    assert exercise.clause == expected
