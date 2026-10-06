"""Pure recommendation rules: scoring, de-duplication, ordering, messages."""

import uuid

import pytest

from app.domain import recommendations as rec
from app.domain.recommendation_messages import TEMPLATES, render_reason
from app.domain.recommendations import (
    CompetencyFacts,
    RecommendationKind,
    candidates_for,
    path_next_step,
    select_top,
    starting_point,
    text_mentions,
)
from app.models.learning import CompetencyState as S


def _facts(**kwargs) -> CompetencyFacts:
    defaults = {"competency_id": uuid.uuid4(), "state": S.LEARNING, "mastery": 50.0}
    return CompetencyFacts(**{**defaults, **kwargs})


def _by_kind(facts: CompetencyFacts) -> dict[RecommendationKind, rec.Candidate]:
    return {c.kind: c for c in candidates_for(facts)}


def test_review_due_scores_grow_with_overdue_days_and_are_capped():
    one = _by_kind(_facts(review_overdue_days=1))[RecommendationKind.REVIEW_DUE]
    ten = _by_kind(_facts(review_overdue_days=10))[RecommendationKind.REVIEW_DUE]
    huge = _by_kind(_facts(review_overdue_days=999))[RecommendationKind.REVIEW_DUE]
    assert one.score < ten.score < huge.score
    assert huge.score == rec.REVIEW_BASE_SCORE + rec.REVIEW_OVERDUE_DAYS_CAP


def test_review_due_applies_to_any_state():
    for state in S:
        found = _by_kind(_facts(state=state, review_overdue_days=0))
        assert RecommendationKind.REVIEW_DUE in found


def test_no_review_candidate_without_due_review():
    assert RecommendationKind.REVIEW_DUE not in _by_kind(_facts())


def test_strengthen_weak_low_mastery_and_lapse():
    weak = _by_kind(_facts(mastery=10.0))[RecommendationKind.STRENGTHEN_WEAK]
    assert weak.reason_key == "strengthen_weak"
    lapse = _by_kind(_facts(mastery=70.0, last_recall_quality=1))[
        RecommendationKind.STRENGTHEN_WEAK
    ]
    assert lapse.reason_key == "strengthen_weak_lapse"
    assert RecommendationKind.STRENGTHEN_WEAK not in _by_kind(_facts(mastery=60.0))
    assert RecommendationKind.STRENGTHEN_WEAK not in _by_kind(
        _facts(mastery=60.0, last_recall_quality=4)
    )


def test_lower_mastery_is_more_urgent():
    low = _by_kind(_facts(mastery=5.0))[RecommendationKind.STRENGTHEN_WEAK]
    mid = _by_kind(_facts(mastery=35.0))[RecommendationKind.STRENGTHEN_WEAK]
    assert low.score > mid.score


def test_take_quiz_only_when_learning_and_coverage_low():
    low = _by_kind(_facts(quiz_coverage=0.1))
    assert RecommendationKind.TAKE_QUIZ in low
    assert RecommendationKind.TAKE_QUIZ not in _by_kind(_facts(quiz_coverage=0.9))
    assert RecommendationKind.TAKE_QUIZ not in _by_kind(_facts(quiz_coverage=None))
    assert RecommendationKind.TAKE_QUIZ not in _by_kind(
        _facts(state=S.AVAILABLE, quiz_coverage=0.0)
    )


def test_continue_learning_only_for_learning_state():
    assert RecommendationKind.CONTINUE_LEARNING in _by_kind(_facts())
    for state in (S.AVAILABLE, S.LOCKED, S.MASTERED):
        assert RecommendationKind.CONTINUE_LEARNING not in _by_kind(_facts(state=state))


def test_goal_deadline_window_and_urgency():
    kw = {"goal_title": "Ship it", "state": S.LEARNING}
    outside = _by_kind(_facts(goal_days_left=rec.GOAL_WINDOW_DAYS + 1, **kw))
    assert RecommendationKind.GOAL_DEADLINE not in outside
    far = _by_kind(_facts(goal_days_left=rec.GOAL_WINDOW_DAYS, **kw))[
        RecommendationKind.GOAL_DEADLINE
    ]
    soon = _by_kind(_facts(goal_days_left=2, **kw))[RecommendationKind.GOAL_DEADLINE]
    overdue = _by_kind(_facts(goal_days_left=-5, **kw))[RecommendationKind.GOAL_DEADLINE]
    assert far.score == rec.GOAL_BASE_SCORE
    assert far.score < soon.score < overdue.score
    assert overdue.score == rec.GOAL_BASE_SCORE + rec.GOAL_URGENCY_BONUS_MAX


def test_goal_deadline_skips_mastered_and_locked():
    for state in (S.MASTERED, S.LOCKED):
        found = _by_kind(_facts(state=state, goal_days_left=1, goal_title="g"))
        assert RecommendationKind.GOAL_DEADLINE not in found


def test_next_in_path_needs_available_and_a_path():
    found = _by_kind(_facts(state=S.AVAILABLE, mastery=0.0, path_next=("p", "Path")))
    candidate = found[RecommendationKind.NEXT_IN_PATH]
    assert candidate.path_slug == "p"
    assert candidate.reason_params == {"path": "Path"}
    assert not candidate_kinds(_facts(state=S.AVAILABLE, mastery=0.0))
    assert RecommendationKind.NEXT_IN_PATH not in _by_kind(_facts(path_next=("p", "Path")))


def candidate_kinds(facts: CompetencyFacts) -> set[RecommendationKind]:
    return set(_by_kind(facts))


def test_select_top_keeps_highest_reason_per_competency():
    facts = _facts(mastery=10.0, review_overdue_days=3, quiz_coverage=0.0)
    top = select_top(candidates_for(facts), 5)
    assert len(top) == 1
    assert top[0].kind == RecommendationKind.REVIEW_DUE


def test_select_top_orders_by_score_then_id_and_applies_limit():
    ids = sorted(uuid.uuid4() for _ in range(3))
    tied = [
        rec.Candidate(RecommendationKind.CONTINUE_LEARNING, cid, 50.0, "continue_learning")
        for cid in reversed(ids)
    ]
    higher = rec.Candidate(RecommendationKind.REVIEW_DUE, uuid.uuid4(), 101.0, "review_due")
    top = select_top([*tied, higher], 3)
    assert [c.competency_id for c in top] == [higher.competency_id, ids[0], ids[1]]
    assert select_top(tied, 0) == []


def test_select_top_is_independent_of_input_order():
    a = rec.Candidate(RecommendationKind.REVIEW_DUE, uuid.uuid4(), 100.0, "review_due")
    b = rec.Candidate(RecommendationKind.TAKE_QUIZ, a.competency_id, 100.0, "take_quiz")
    assert select_top([a, b], 5) == select_top([b, a], 5)
    assert select_top([a, b], 5)[0].kind == RecommendationKind.REVIEW_DUE


def test_starting_point():
    cid = uuid.uuid4()
    with_path = starting_point(cid, ("slug", "Title"))
    assert with_path.path_slug == "slug"
    assert with_path.reason_key == "starting_point_path"
    assert starting_point(cid).reason_key == "starting_point"


def test_path_next_step():
    a, b, c = (uuid.uuid4() for _ in range(3))
    assert path_next_step([(a, S.MASTERED), (b, S.AVAILABLE), (c, S.LOCKED)]) == b
    assert path_next_step([(a, S.LEARNING), (b, S.AVAILABLE)]) == b
    # not started: the fallback handles it, not this rule
    assert path_next_step([(a, S.AVAILABLE), (b, S.LOCKED)]) is None
    assert path_next_step([(a, S.MASTERED), (b, S.MASTERED)]) is None
    assert path_next_step([(a, S.LEARNING), (b, S.LOCKED)]) is None
    assert path_next_step([]) is None


def test_text_mentions_whole_phrase_case_insensitive():
    assert text_mentions("Learn PYTHON basics", "python")
    assert text_mentions("finish type hints by May", "Type Hints")
    assert not text_mentions("javascript", "java")
    assert not text_mentions("anything", "  ")


@pytest.mark.parametrize("language", ["en", "pt-BR"])
def test_every_reason_key_renders_in_every_language(language):
    params = {"days": 3, "goal": "G", "mastery": 12, "coverage": 30, "path": "P"}
    for key in TEMPLATES["en"]:
        base = (
            key.rsplit("_", 1)[0] if key.endswith(("_one", "_other", "_today", "_overdue")) else key
        )
        assert render_reason(base, params, language)
        assert key in TEMPLATES[language]


def test_messages_pluralise_and_fall_back_to_english():
    assert "1 day overdue" in render_reason("review_due", {"days": 1}, "en")
    assert "3 days overdue" in render_reason("review_due", {"days": 3}, "en")
    assert "due today" in render_reason("review_due", {"days": 0}, "en")
    assert "3 dias" in render_reason("review_due", {"days": 3}, "pt-BR")
    assert "past its target date" in render_reason("goal_deadline", {"goal": "x", "days": -2}, "en")
    assert render_reason("starting_point", {}, "fr") == TEMPLATES["en"]["starting_point"]
