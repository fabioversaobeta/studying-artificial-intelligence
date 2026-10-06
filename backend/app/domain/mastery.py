"""Deterministic, transparent mastery-scoring formula.

Mastery (0-100) intentionally combines three *different* signals so that
"I opened the material" is never confused with "I can actually do this":

  engagement_score (0-40): time invested studying the competency.
      Diminishing returns after 120 minutes — grinding time alone cannot
      carry a score past this cap.

  practice_score (0-35): 35 x the weighted mean of two ratios, each only
      counted when that kind of evidence exists for the competency:
        - challenge share: challenges passed / challenges total;
        - quiz coverage: distinct active questions whose MOST RECENT answer
          (in a finished attempt) is correct / active questions total.
      Weights are 50/50 (CHALLENGE_WEIGHT / QUIZ_WEIGHT). If only one kind
      exists, it alone decides the ratio; if neither exists the score is 0.
      Zero until something is attempted, so passive reading alone cannot
      reach a "practiced" score. Coverage counts DISTINCT questions by their
      latest answer, so re-answering the same question many times cannot
      inflate it, and a later wrong answer takes the credit back.

  retention_score (0-25): most recent spaced-repetition recall quality
      (0-5 scale, see app.domain.spaced_repetition). Zero until the first
      review, so a score can't claim "retained" before it's been tested.

The weights (40/35/25) are a v1 judgment call, not derived from data.
Changing them is a one-line change here — nothing else in the codebase
encodes the formula (see docs/DECISIONS.md).
"""

from dataclasses import dataclass

ENGAGEMENT_MAX_POINTS = 40.0
ENGAGEMENT_MINUTES_FOR_MAX = 120.0

PRACTICE_MAX_POINTS = 35.0
CHALLENGE_WEIGHT = 0.5
QUIZ_WEIGHT = 0.5

RETENTION_MAX_POINTS = 25.0
RETENTION_QUALITY_SCALE = 5.0


@dataclass(frozen=True)
class MasteryInputs:
    total_study_minutes: int
    challenges_total: int
    challenges_passed: int
    last_recall_quality: int | None  # 0-5, None if never reviewed
    # Active questions of the competency, and how many of them (distinct) have a
    # correct most-recent answer. Defaults keep competencies without a question
    # bank scoring exactly as before.
    questions_total: int = 0
    questions_correct: int = 0


def practice_ratio(inputs: MasteryInputs) -> float:
    """0-1 weighted mean of the available practice signals (see module doc)."""
    weighted_sum = 0.0
    weight_sum = 0.0
    if inputs.challenges_total > 0:
        passed = max(0, min(inputs.challenges_passed, inputs.challenges_total))
        weighted_sum += CHALLENGE_WEIGHT * (passed / inputs.challenges_total)
        weight_sum += CHALLENGE_WEIGHT
    if inputs.questions_total > 0:
        correct = max(0, min(inputs.questions_correct, inputs.questions_total))
        weighted_sum += QUIZ_WEIGHT * (correct / inputs.questions_total)
        weight_sum += QUIZ_WEIGHT
    if weight_sum == 0:
        return 0.0
    return weighted_sum / weight_sum


def compute_mastery_score(inputs: MasteryInputs) -> float:
    engagement_score = min(
        ENGAGEMENT_MAX_POINTS,
        (inputs.total_study_minutes / ENGAGEMENT_MINUTES_FOR_MAX) * ENGAGEMENT_MAX_POINTS,
    )

    practice_score = PRACTICE_MAX_POINTS * practice_ratio(inputs)

    retention_score = 0.0
    if inputs.last_recall_quality is not None:
        retention_score = RETENTION_MAX_POINTS * (
            max(0, min(5, inputs.last_recall_quality)) / RETENTION_QUALITY_SCALE
        )

    total = engagement_score + practice_score + retention_score
    return round(min(100.0, max(0.0, total)), 2)
