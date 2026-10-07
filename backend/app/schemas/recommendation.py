import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.domain.recommendations import RecommendationKind


class RecommendationCompetency(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    subject_id: uuid.UUID
    subject_name: str


class RecommendationAction(BaseModel):
    """Where the UI should send the learner. `review`: the reviews screen
    (`id` = competency); `competency`: its subject page (`id` = competency);
    `assessment`: the quizzes screen (`id` = assessment); `path`: the learning
    path detail (`slug`)."""

    type: Literal["review", "competency", "assessment", "path"]
    id: uuid.UUID | None = None
    slug: str | None = None


class RecommendationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kind: RecommendationKind
    competency: RecommendationCompetency
    reason: str
    score: float
    action: RecommendationAction


class TodayRecommendationsRead(BaseModel):
    items: list[RecommendationRead]
