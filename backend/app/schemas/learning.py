import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.learning import (
    ChallengeSubmissionStatus,
    CompetencyState,
    DifficultyLevel,
    GoalStatus,
    ResourceType,
)


class SubjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    icon: str | None
    color: str | None
    sort_order: int


class SubjectWithProgress(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    subject: SubjectRead
    competency_count: int
    average_mastery: float


class CompetencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    difficulty: DifficultyLevel
    sort_order: int


class CompetencyWithState(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    competency: CompetencyRead
    mastery_score: float
    state: CompetencyState


class SubjectDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    subject: SubjectRead
    competencies: list[CompetencyWithState]


class LearningResourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: ResourceType
    title: str
    url: str | None
    description: str | None
    content: str | None


class LearningPathItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    competency: CompetencyRead
    sort_order: int


class LearningPathRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    description: str | None
    items: list[LearningPathItemRead]


class StudySessionCreate(BaseModel):
    competency_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    duration_minutes: int = Field(gt=0, le=600)
    notes: str | None = Field(default=None, max_length=2000)
    occurred_at: datetime | None = None


class StudySessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    competency_id: uuid.UUID | None
    subject_id: uuid.UUID | None
    duration_minutes: int
    notes: str | None
    occurred_at: datetime


class LearningGoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    target_date: date | None = None


class LearningGoalStatusUpdate(BaseModel):
    status: GoalStatus


class LearningGoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    status: GoalStatus
    target_date: date | None
    created_at: datetime


class ChallengeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    competency_id: uuid.UUID
    title: str
    description: str
    difficulty: DifficultyLevel
    xp_value: int


class ChallengeSubmissionCreate(BaseModel):
    status: ChallengeSubmissionStatus
    notes: str | None = Field(default=None, max_length=2000)


class ChallengeSubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    challenge_id: uuid.UUID
    status: ChallengeSubmissionStatus
    notes: str | None
    submitted_at: datetime
    xp_awarded: int


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    competency_id: uuid.UUID
    interval_days: int
    ease_factor: float
    repetitions: int
    due_at: datetime
    last_reviewed_at: datetime | None
    last_recall_quality: int | None


class ReviewDueRead(ReviewRead):
    """A due review enriched with the competency/subject context, so clients
    don't need extra calls to render it. Additive over ReviewRead."""

    competency_name: str
    subject_id: uuid.UUID
    subject_name: str


class ReviewRecallSubmit(BaseModel):
    quality: int = Field(ge=0, le=5)


class MasteryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    competency_id: uuid.UUID
    score: float
    updated_at: datetime
