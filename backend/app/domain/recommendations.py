"""Pure, deterministic rules behind "what to study today" (roadmap I3).

No database, no clock, no randomness, no LLM: the service gathers a
`CompetencyFacts` per competency and these functions turn facts into scored
`Candidate`s. Every candidate carries a machine-readable reason (`reason_key`
+ `reason_params`) that `recommendation_messages` renders in the user's
language, so a suggestion is always explainable ("transparent > clever").

Scores are comparable across kinds; the weights are the constants below and
are documented in docs/DOMAIN.md. Higher score = more urgent.
"""

import re
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum

from app.domain.skill_tree import MASTERY_THRESHOLD
from app.models.learning import CompetencyState

DEFAULT_LIMIT = 5
MAX_LIMIT = 20


class RecommendationKind(StrEnum):
    REVIEW_DUE = "review_due"
    CONTINUE_LEARNING = "continue_learning"
    NEXT_IN_PATH = "next_in_path"
    TAKE_QUIZ = "take_quiz"
    GOAL_DEADLINE = "goal_deadline"
    STRENGTHEN_WEAK = "strengthen_weak"


# --- Weights (all scores are floats; see docs/DOMAIN.md) ---------------------

# review_due: always the top band. 100 + days overdue (capped), so the most
# overdue review comes first and a due review outranks every other kind
# except an overdue/imminent goal.
REVIEW_BASE_SCORE = 100.0
REVIEW_OVERDUE_DAYS_CAP = 30

# goal_deadline: a goal whose target date is within GOAL_WINDOW_DAYS (or
# already past). 85 when the window just opened, up to 85 + 25 on/after the date.
GOAL_WINDOW_DAYS = 14
GOAL_BASE_SCORE = 85.0
GOAL_URGENCY_BONUS_MAX = 25.0

# strengthen_weak: a `learning` competency with mastery below
# WEAK_MASTERY_THRESHOLD, or whose last recall quality was a lapse
# (< WEAK_RECALL_QUALITY). 70..80 by how low the mastery is, +5 on a lapse.
WEAK_MASTERY_THRESHOLD = 40.0
WEAK_RECALL_QUALITY = 3
WEAK_BASE_SCORE = 70.0
WEAK_MASTERY_BONUS_MAX = 10.0
WEAK_LAPSE_BONUS = 5.0

# next_in_path: first `available` step of a path already under way.
NEXT_IN_PATH_SCORE = 55.0
# Starting point for a user with nothing else to do (fresh account).
STARTING_POINT_SCORE = 50.0

# take_quiz: a `learning` competency with a quiz whose coverage (distinct
# questions last answered correctly / active questions) is below the
# threshold. 45..55 by how low the coverage is.
QUIZ_COVERAGE_THRESHOLD = 0.5
QUIZ_BASE_SCORE = 45.0
QUIZ_COVERAGE_BONUS_MAX = 10.0

# continue_learning: any other `learning` competency; 40..60 by how far from
# mastered it still is.
CONTINUE_BASE_SCORE = 40.0
CONTINUE_GAP_BONUS_MAX = 20.0


@dataclass(frozen=True)
class CompetencyFacts:
    """Everything the rules know about one competency for one user."""

    competency_id: uuid.UUID
    state: CompetencyState
    mastery: float  # 0-100
    last_recall_quality: int | None = None  # 0-5, None if never reviewed
    review_overdue_days: int | None = None  # None = no review is due
    goal_days_left: int | None = None  # nearest active goal; negative = overdue
    goal_title: str | None = None
    quiz_coverage: float | None = None  # 0-1, None = no quiz available
    path_next: tuple[str, str] | None = None  # (slug, title) of the path to continue


@dataclass(frozen=True)
class Candidate:
    kind: RecommendationKind
    competency_id: uuid.UUID
    score: float
    reason_key: str
    reason_params: dict[str, str | int] = field(default_factory=dict)
    path_slug: str | None = None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def candidates_for(facts: CompetencyFacts) -> list[Candidate]:
    """All the reasons to study one competency today, each with its score."""
    cid = facts.competency_id
    found: list[Candidate] = []

    if facts.review_overdue_days is not None:
        days = max(facts.review_overdue_days, 0)
        found.append(
            Candidate(
                RecommendationKind.REVIEW_DUE,
                cid,
                REVIEW_BASE_SCORE + min(days, REVIEW_OVERDUE_DAYS_CAP),
                "review_due",
                {"days": days},
            )
        )

    if (
        facts.goal_days_left is not None
        and facts.goal_days_left <= GOAL_WINDOW_DAYS
        and facts.goal_title is not None
        and facts.state not in (CompetencyState.MASTERED, CompetencyState.LOCKED)
    ):
        days_left = facts.goal_days_left
        closeness = (GOAL_WINDOW_DAYS - _clamp(days_left, 0, GOAL_WINDOW_DAYS)) / GOAL_WINDOW_DAYS
        found.append(
            Candidate(
                RecommendationKind.GOAL_DEADLINE,
                cid,
                GOAL_BASE_SCORE + GOAL_URGENCY_BONUS_MAX * closeness,
                "goal_deadline",
                {"goal": facts.goal_title, "days": days_left},
            )
        )

    if facts.state == CompetencyState.LEARNING:
        lapse = (
            facts.last_recall_quality is not None
            and facts.last_recall_quality < WEAK_RECALL_QUALITY
        )
        if facts.mastery < WEAK_MASTERY_THRESHOLD or lapse:
            shortfall = (WEAK_MASTERY_THRESHOLD - min(facts.mastery, WEAK_MASTERY_THRESHOLD)) / (
                WEAK_MASTERY_THRESHOLD
            )
            score = WEAK_BASE_SCORE + WEAK_MASTERY_BONUS_MAX * shortfall
            if lapse:
                score += WEAK_LAPSE_BONUS
            found.append(
                Candidate(
                    RecommendationKind.STRENGTHEN_WEAK,
                    cid,
                    score,
                    "strengthen_weak_lapse" if lapse else "strengthen_weak",
                    {"mastery": round(facts.mastery)},
                )
            )

        if facts.quiz_coverage is not None and facts.quiz_coverage < QUIZ_COVERAGE_THRESHOLD:
            gap = (QUIZ_COVERAGE_THRESHOLD - facts.quiz_coverage) / QUIZ_COVERAGE_THRESHOLD
            found.append(
                Candidate(
                    RecommendationKind.TAKE_QUIZ,
                    cid,
                    QUIZ_BASE_SCORE + QUIZ_COVERAGE_BONUS_MAX * gap,
                    "take_quiz",
                    {"coverage": round(facts.quiz_coverage * 100)},
                )
            )

        gap_to_mastered = (MASTERY_THRESHOLD - _clamp(facts.mastery, 0, MASTERY_THRESHOLD)) / (
            MASTERY_THRESHOLD
        )
        found.append(
            Candidate(
                RecommendationKind.CONTINUE_LEARNING,
                cid,
                CONTINUE_BASE_SCORE + CONTINUE_GAP_BONUS_MAX * gap_to_mastered,
                "continue_learning",
                {"mastery": round(facts.mastery)},
            )
        )

    if facts.state == CompetencyState.AVAILABLE and facts.path_next is not None:
        found.append(
            Candidate(
                RecommendationKind.NEXT_IN_PATH,
                cid,
                NEXT_IN_PATH_SCORE,
                "next_in_path",
                {"path": facts.path_next[1]},
                path_slug=facts.path_next[0],
            )
        )

    return found


def starting_point(competency_id: uuid.UUID, path: tuple[str, str] | None = None) -> Candidate:
    """Fallback for a user who has nothing to review, continue or reach.
    `path` is (slug, title) of the first learning path, if there is one."""
    if path is not None:
        return Candidate(
            RecommendationKind.NEXT_IN_PATH,
            competency_id,
            STARTING_POINT_SCORE,
            "starting_point_path",
            {"path": path[1]},
            path_slug=path[0],
        )
    return Candidate(
        RecommendationKind.NEXT_IN_PATH, competency_id, STARTING_POINT_SCORE, "starting_point"
    )


def select_top(candidates: Sequence[Candidate], limit: int) -> list[Candidate]:
    """One candidate per competency (the highest score wins; a tie keeps the
    first kind in enum order), ordered by score desc then competency id, so the
    result is fully deterministic."""
    kind_order = {kind: index for index, kind in enumerate(RecommendationKind)}
    best: dict[uuid.UUID, Candidate] = {}
    for candidate in candidates:
        current = best.get(candidate.competency_id)
        if current is None or (-candidate.score, kind_order[candidate.kind]) < (
            -current.score,
            kind_order[current.kind],
        ):
            best[candidate.competency_id] = candidate
    ordered = sorted(best.values(), key=lambda c: (-round(c.score, 2), str(c.competency_id)))
    return ordered[: max(limit, 0)]


def path_next_step(steps: Sequence[tuple[uuid.UUID, CompetencyState]]) -> uuid.UUID | None:
    """First `available` step (in path order) of a path that is under way: at
    least one step learning or mastered, and not every step mastered."""
    states = [state for _, state in steps]
    under_way = any(s in (CompetencyState.LEARNING, CompetencyState.MASTERED) for s in states)
    if not under_way or all(s == CompetencyState.MASTERED for s in states):
        return None
    for competency_id, state in steps:
        if state == CompetencyState.AVAILABLE:
            return competency_id
    return None


def text_mentions(text: str, phrase: str) -> bool:
    """Case-insensitive whole-phrase match of `phrase` inside `text`."""
    phrase = phrase.strip().casefold()
    if not phrase:
        return False
    pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
    return re.search(pattern, text.casefold()) is not None
