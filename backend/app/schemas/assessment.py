"""Assessment API shapes.

Two families on purpose: the *public* question shape (served while an attempt
is in progress) never carries a correct answer or explanation field at all;
the *review* part is only filled once the attempt is finished (or, for a short
answer, after the learner has saved their answer and needs the model answer to
self-grade).
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.assessment import (
    AssessmentKind,
    AttemptStatus,
    GradingStatus,
    QuestionDifficulty,
    QuestionType,
)
from app.models.user import Language


class OptionRead(BaseModel):
    id: str
    text: str


class AssessmentRead(BaseModel):
    id: uuid.UUID
    code: str
    title: str
    description: str | None
    kind: AssessmentKind
    competency_id: uuid.UUID | None
    competency_name: str | None
    pass_threshold: int
    completion_bonus_xp: int
    question_count: int
    # Per-user progress.
    attempts_completed: int
    best_score_percent: float | None
    passed: bool
    open_attempt_id: uuid.UUID | None


class SavedAnswer(BaseModel):
    option_ids: list[str] | None = None
    text: str | None = None
    grading_status: GradingStatus
    time_spent_seconds: int | None = None


class QuestionReview(BaseModel):
    """What is revealed after finishing: the verdict and the learning material."""

    correct_option_ids: list[str] | None
    explanation: str
    model_answer: str | None
    is_correct: bool | None  # null: short answer that was never self-graded
    grading_status: GradingStatus
    xp_awarded: int
    is_first_correct: bool


class AttemptQuestion(BaseModel):
    id: uuid.UUID
    position: int  # 1-based
    type: QuestionType
    difficulty: QuestionDifficulty
    xp_value: int
    tags: list[str]
    prompt: str  # markdown
    options: list[OptionRead] | None  # null for short_answer
    language: Language  # the language actually served (en when untranslated)
    answer: SavedAnswer | None = None
    review: QuestionReview | None = None  # only present on finished attempts


class AttemptSummary(BaseModel):
    id: uuid.UUID
    assessment_id: uuid.UUID
    assessment_title: str
    status: AttemptStatus
    started_at: datetime
    completed_at: datetime | None
    total_questions: int
    correct_count: int | None
    score_percent: float | None
    passed: bool | None
    xp_awarded: int


class AttemptDetail(AttemptSummary):
    pass_threshold: int
    answered_count: int
    xp_questions: int
    xp_bonus: int
    pending_review_count: int  # short answers that were not self-graded (count as wrong)
    questions: list[AttemptQuestion]


class AnswerSubmit(BaseModel):
    option_ids: list[str] | None = Field(default=None, max_length=12)
    text: str | None = Field(default=None, max_length=5000)
    time_spent_seconds: int | None = Field(default=None, ge=0, le=86_400)


class SelfGradeSubmit(BaseModel):
    is_correct: bool


class AnswerResult(BaseModel):
    question_id: uuid.UUID
    saved: bool = True
    grading_status: GradingStatus
    # Only for short answers, so the learner can self-grade against them.
    model_answer: str | None = None
    explanation: str | None = None
    is_correct: bool | None = None  # only set after a self-grade


class CompetencyAssessmentStats(BaseModel):
    competency_id: uuid.UUID
    competency_name: str
    subject_name: str
    questions_total: int  # active questions in the bank
    questions_answered: int  # distinct questions answered in finished attempts
    questions_correct: int  # distinct questions whose latest answer is correct
    coverage_percent: float  # questions_correct / questions_total (feeds mastery)
    attempts_completed: int
    responses_graded: int
    responses_correct: int
    accuracy_percent: float | None  # responses_correct / responses_graded
    xp_earned: int
