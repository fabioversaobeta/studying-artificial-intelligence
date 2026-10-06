import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.deps import CurrentUser, DbSession
from app.api.pagination import Pagination, set_total_count
from app.models.assessment import AssessmentKind
from app.models.user import Language
from app.schemas.assessment import (
    AnswerResult,
    AnswerSubmit,
    AssessmentRead,
    AttemptDetail,
    AttemptSummary,
    CompetencyAssessmentStats,
    SelfGradeSubmit,
)
from app.services import assessment_service

router = APIRouter(tags=["assessments"])

LangQuery = Annotated[
    Language | None,
    Query(description="Content language override; defaults to the user's preferred_language"),
]


@router.get("/assessments", response_model=list[AssessmentRead])
def list_assessments(
    current_user: CurrentUser,
    db: DbSession,
    page: Pagination,
    response: Response,
    competency_id: uuid.UUID | None = None,
    kind: AssessmentKind | None = None,
    lang: LangQuery = None,
) -> list[AssessmentRead]:
    items, total = assessment_service.list_assessments(
        db,
        current_user,
        competency_id=competency_id,
        kind=kind,
        lang=lang,
        limit=page.limit,
        offset=page.offset,
    )
    set_total_count(response, total)
    return items


@router.get("/competencies/{competency_id}/assessments", response_model=list[AssessmentRead])
def list_competency_assessments(
    competency_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    page: Pagination,
    response: Response,
    lang: LangQuery = None,
) -> list[AssessmentRead]:
    items, total = assessment_service.list_assessments(
        db,
        current_user,
        competency_id=competency_id,
        lang=lang,
        limit=page.limit,
        offset=page.offset,
    )
    set_total_count(response, total)
    return items


@router.get("/assessments/stats/by-competency", response_model=list[CompetencyAssessmentStats])
def competency_stats(
    current_user: CurrentUser, db: DbSession, page: Pagination, response: Response
) -> list[CompetencyAssessmentStats]:
    items, total = assessment_service.competency_stats(
        db, current_user, limit=page.limit, offset=page.offset
    )
    set_total_count(response, total)
    return items


@router.post("/assessments/{assessment_id}/attempts", response_model=AttemptDetail)
def start_attempt(
    assessment_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    response: Response,
    lang: LangQuery = None,
) -> AttemptDetail:
    """Start an attempt (201) or resume the open one for this assessment (200)."""
    detail, created = assessment_service.start_attempt(db, current_user, assessment_id, lang=lang)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return detail


@router.get("/attempts", response_model=list[AttemptSummary])
def list_attempts(
    current_user: CurrentUser,
    db: DbSession,
    page: Pagination,
    response: Response,
    assessment_id: uuid.UUID | None = None,
    lang: LangQuery = None,
) -> list[AttemptSummary]:
    items, total = assessment_service.list_attempts(
        db,
        current_user,
        assessment_id=assessment_id,
        lang=lang,
        limit=page.limit,
        offset=page.offset,
    )
    set_total_count(response, total)
    return items


@router.get("/attempts/{attempt_id}", response_model=AttemptDetail)
def get_attempt(
    attempt_id: uuid.UUID, current_user: CurrentUser, db: DbSession, lang: LangQuery = None
) -> AttemptDetail:
    return assessment_service.get_attempt(db, current_user, attempt_id, lang=lang)


@router.patch("/attempts/{attempt_id}/responses/{question_id}", response_model=AnswerResult)
def save_answer(
    attempt_id: uuid.UUID,
    question_id: uuid.UUID,
    payload: AnswerSubmit,
    current_user: CurrentUser,
    db: DbSession,
    lang: LangQuery = None,
) -> AnswerResult:
    return assessment_service.save_answer(
        db, current_user, attempt_id, question_id, payload, lang=lang
    )


@router.post(
    "/attempts/{attempt_id}/responses/{question_id}/self-grade", response_model=AnswerResult
)
def self_grade(
    attempt_id: uuid.UUID,
    question_id: uuid.UUID,
    payload: SelfGradeSubmit,
    current_user: CurrentUser,
    db: DbSession,
    lang: LangQuery = None,
) -> AnswerResult:
    return assessment_service.self_grade(
        db, current_user, attempt_id, question_id, is_correct=payload.is_correct, lang=lang
    )


@router.post("/attempts/{attempt_id}/finish", response_model=AttemptDetail)
def finish_attempt(
    attempt_id: uuid.UUID, current_user: CurrentUser, db: DbSession, lang: LangQuery = None
) -> AttemptDetail:
    return assessment_service.finish_attempt(db, current_user, attempt_id, lang=lang)
