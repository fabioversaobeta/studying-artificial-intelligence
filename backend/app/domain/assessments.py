"""Pure rules for assessments (quizzes): XP per difficulty, deterministic
grading of choice questions, scoring and the attempt XP rule.

No I/O and no ORM imports (enums are referenced by their string values), so
everything here is unit-testable without a database. Rationale for the XP rule
is in docs/DECISIONS.md ("Assessment XP rule") and docs/DOMAIN.md.
"""

from collections.abc import Collection, Iterable
from dataclasses import dataclass

# Data table (not hardcoded in services): XP a question is worth, by difficulty.
# `Question.xp_value` is copied from here at seed time, so retuning this table
# changes future seeds without rewriting history.
XP_BY_DIFFICULTY: dict[str, int] = {"easy": 10, "medium": 20, "hard": 30}

DEFAULT_PASS_THRESHOLD = 70  # percent
DEFAULT_COMPLETION_BONUS_XP = 25

SINGLE_ANSWER_TYPES = frozenset({"multiple_choice", "code_reading"})
MULTI_ANSWER_TYPES = frozenset({"multi_select"})
CHOICE_TYPES = SINGLE_ANSWER_TYPES | MULTI_ANSWER_TYPES
OPEN_TYPES = frozenset({"short_answer"})


def xp_for_difficulty(difficulty: str) -> int:
    return XP_BY_DIFFICULTY[difficulty]


def grade_choice(correct_option_ids: Collection[str], selected_option_ids: Collection[str]) -> bool:
    """All-or-nothing: the selection must equal the correct set exactly.

    Order and duplicates in the selection are irrelevant. Used for
    multiple_choice, code_reading (single correct id) and multi_select.
    """
    return set(selected_option_ids) == set(correct_option_ids)


def score_percent(correct: int, total: int) -> float:
    """Percentage (0-100, 2 decimals) of correct answers; 0 for an empty quiz."""
    if total <= 0:
        return 0.0
    return round(correct * 100 / total, 2)


def is_passing(correct: int, total: int, pass_threshold: int) -> bool:
    """Integer-exact comparison (no float rounding): correct/total >= threshold%."""
    if total <= 0:
        return False
    return correct * 100 >= pass_threshold * total


@dataclass(frozen=True)
class AttemptXP:
    questions_xp: int
    completion_bonus_xp: int

    @property
    def total(self) -> int:
        return self.questions_xp + self.completion_bonus_xp


def compute_attempt_xp(
    *,
    passed: bool,
    unpaid_correct_xp_values: Iterable[int],
    is_first_pass: bool,
    completion_bonus_xp: int,
) -> AttemptXP:
    """The assessment XP rule (owner decision, PROPOSAL_TRACK_I.md section 3.1).

    * Nothing is paid unless the attempt passed.
    * On a pass: the sum of `xp_value` of the questions answered correctly in
      this attempt that have NEVER been paid before for this user (callers
      pass only those), plus the completion bonus on the first pass of the
      assessment.
    * Repeating pays nothing for already-paid questions and no second bonus.
    """
    if not passed:
        return AttemptXP(0, 0)
    return AttemptXP(
        questions_xp=sum(unpaid_correct_xp_values),
        completion_bonus_xp=completion_bonus_xp if is_first_pass else 0,
    )
