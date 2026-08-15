"""Pure logic for computing a competency's per-user skill-tree state.

State is derived, never stored: it depends on the user's mastery scores and
activity, which already live in the `mastery_records` and `study_sessions`
tables. Storing a redundant `state` column would just invite drift.
"""

from app.models.learning import CompetencyState

MASTERY_THRESHOLD = 80.0


def compute_competency_state(
    *,
    mastery_score: float | None,
    has_activity: bool,
    prerequisites_mastered: bool,
) -> CompetencyState:
    if mastery_score is not None and mastery_score >= MASTERY_THRESHOLD:
        return CompetencyState.MASTERED
    if has_activity:
        return CompetencyState.LEARNING
    if prerequisites_mastered:
        return CompetencyState.AVAILABLE
    return CompetencyState.LOCKED
