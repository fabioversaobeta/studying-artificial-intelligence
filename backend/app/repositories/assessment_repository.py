"""Persistence for assessments: catalog reads, attempts, responses and the
per-user aggregates used for XP eligibility, mastery coverage and statistics.
No business rules here (see app.services.assessment_service).
"""

import uuid
from collections.abc import Collection
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Select, and_, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.assessment import (
    Assessment,
    AssessmentAttempt,
    AssessmentKind,
    AssessmentQuestion,
    AttemptStatus,
    Question,
    QuestionResponse,
)
from app.models.learning import Competency, Subject

# --------------------------------------------------------------------------
# Catalog
# --------------------------------------------------------------------------


def _assessments_stmt(competency_id: uuid.UUID | None, kind: AssessmentKind | None) -> Select:
    stmt = select(Assessment).where(Assessment.is_active.is_(True))
    if competency_id is not None:
        stmt = stmt.where(Assessment.competency_id == competency_id)
    if kind is not None:
        stmt = stmt.where(Assessment.kind == kind)
    return stmt


def list_assessments(
    db: Session,
    *,
    competency_id: uuid.UUID | None,
    kind: AssessmentKind | None,
    limit: int,
    offset: int,
) -> tuple[list[Assessment], int]:
    base = _assessments_stmt(competency_id, kind)
    total = int(db.execute(select(func.count()).select_from(base.subquery())).scalar_one())
    stmt = (
        base.options(selectinload(Assessment.competency))
        .order_by(Assessment.sort_order, Assessment.title, Assessment.id)
        .offset(offset)
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all()), total


def get_assessment(db: Session, assessment_id: uuid.UUID) -> Assessment | None:
    return db.get(Assessment, assessment_id)


def count_active_questions_by_assessment(
    db: Session, assessment_ids: Collection[uuid.UUID]
) -> dict[uuid.UUID, int]:
    if not assessment_ids:
        return {}
    stmt = (
        select(AssessmentQuestion.assessment_id, func.count())
        .join(Question, Question.id == AssessmentQuestion.question_id)
        .where(AssessmentQuestion.assessment_id.in_(assessment_ids), Question.is_active.is_(True))
        .group_by(AssessmentQuestion.assessment_id)
    )
    return {assessment_id: int(count) for assessment_id, count in db.execute(stmt).all()}


def list_active_assessment_questions(db: Session, assessment_id: uuid.UUID) -> list[Question]:
    stmt = (
        select(Question)
        .join(AssessmentQuestion, AssessmentQuestion.question_id == Question.id)
        .where(AssessmentQuestion.assessment_id == assessment_id, Question.is_active.is_(True))
        .options(selectinload(Question.translations))
        .order_by(AssessmentQuestion.sort_order, Question.code)
    )
    return list(db.execute(stmt).scalars().all())


def get_questions_by_ids(
    db: Session, question_ids: Collection[uuid.UUID]
) -> dict[uuid.UUID, Question]:
    if not question_ids:
        return {}
    stmt = (
        select(Question)
        .where(Question.id.in_(question_ids))
        .options(selectinload(Question.translations))
    )
    return {q.id: q for q in db.execute(stmt).scalars().all()}


# --------------------------------------------------------------------------
# Attempts and responses
# --------------------------------------------------------------------------


def get_open_attempt(
    db: Session, user_id: uuid.UUID, assessment_id: uuid.UUID
) -> AssessmentAttempt | None:
    stmt = select(AssessmentAttempt).where(
        AssessmentAttempt.user_id == user_id,
        AssessmentAttempt.assessment_id == assessment_id,
        AssessmentAttempt.status == AttemptStatus.IN_PROGRESS,
    )
    return db.execute(stmt).scalar_one_or_none()


def create_attempt(
    db: Session,
    *,
    user_id: uuid.UUID,
    assessment_id: uuid.UUID,
    question_ids: list[str],
    started_at: datetime,
) -> AssessmentAttempt:
    attempt = AssessmentAttempt(
        user_id=user_id,
        assessment_id=assessment_id,
        status=AttemptStatus.IN_PROGRESS,
        question_ids=question_ids,
        total_questions=len(question_ids),
        started_at=started_at,
    )
    db.add(attempt)
    db.flush()
    return attempt


def get_attempt(
    db: Session, attempt_id: uuid.UUID, *, for_update: bool = False
) -> AssessmentAttempt | None:
    stmt = (
        select(AssessmentAttempt)
        .where(AssessmentAttempt.id == attempt_id)
        .options(selectinload(AssessmentAttempt.assessment))
    )
    if for_update:
        stmt = stmt.with_for_update(of=AssessmentAttempt)
    return db.execute(stmt).scalar_one_or_none()


def list_attempts(
    db: Session,
    user_id: uuid.UUID,
    *,
    assessment_id: uuid.UUID | None,
    limit: int,
    offset: int,
) -> tuple[list[AssessmentAttempt], int]:
    base = select(AssessmentAttempt).where(AssessmentAttempt.user_id == user_id)
    if assessment_id is not None:
        base = base.where(AssessmentAttempt.assessment_id == assessment_id)
    total = int(db.execute(select(func.count()).select_from(base.subquery())).scalar_one())
    stmt = (
        base.options(selectinload(AssessmentAttempt.assessment))
        .order_by(AssessmentAttempt.started_at.desc(), AssessmentAttempt.id)
        .offset(offset)
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all()), total


def list_responses(db: Session, attempt_id: uuid.UUID) -> list[QuestionResponse]:
    stmt = select(QuestionResponse).where(QuestionResponse.attempt_id == attempt_id)
    return list(db.execute(stmt).scalars().all())


def get_response(
    db: Session, attempt_id: uuid.UUID, question_id: uuid.UUID
) -> QuestionResponse | None:
    stmt = select(QuestionResponse).where(
        QuestionResponse.attempt_id == attempt_id, QuestionResponse.question_id == question_id
    )
    return db.execute(stmt).scalar_one_or_none()


def add_response(db: Session, response: QuestionResponse) -> QuestionResponse:
    db.add(response)
    db.flush()
    return response


# --------------------------------------------------------------------------
# Per-user history used by the XP rule
# --------------------------------------------------------------------------


def correct_question_ids_before(
    db: Session,
    user_id: uuid.UUID,
    question_ids: Collection[uuid.UUID],
    *,
    exclude_attempt_id: uuid.UUID,
) -> set[uuid.UUID]:
    """Questions (among `question_ids`) the user already answered correctly in
    some OTHER finished attempt."""
    if not question_ids:
        return set()
    stmt = (
        select(QuestionResponse.question_id)
        .join(AssessmentAttempt, AssessmentAttempt.id == QuestionResponse.attempt_id)
        .where(
            QuestionResponse.user_id == user_id,
            QuestionResponse.question_id.in_(question_ids),
            QuestionResponse.is_correct.is_(True),
            AssessmentAttempt.status == AttemptStatus.COMPLETED,
            AssessmentAttempt.id != exclude_attempt_id,
        )
        .distinct()
    )
    return set(db.execute(stmt).scalars().all())


def paid_question_ids(
    db: Session, user_id: uuid.UUID, question_ids: Collection[uuid.UUID]
) -> set[uuid.UUID]:
    """Questions (among `question_ids`) that already earned XP for this user."""
    if not question_ids:
        return set()
    stmt = (
        select(QuestionResponse.question_id)
        .where(
            QuestionResponse.user_id == user_id,
            QuestionResponse.question_id.in_(question_ids),
            QuestionResponse.xp_awarded > 0,
        )
        .distinct()
    )
    return set(db.execute(stmt).scalars().all())


def has_passed_before(
    db: Session, user_id: uuid.UUID, assessment_id: uuid.UUID, *, exclude_attempt_id: uuid.UUID
) -> bool:
    stmt = (
        select(func.count())
        .select_from(AssessmentAttempt)
        .where(
            AssessmentAttempt.user_id == user_id,
            AssessmentAttempt.assessment_id == assessment_id,
            AssessmentAttempt.status == AttemptStatus.COMPLETED,
            AssessmentAttempt.passed.is_(True),
            AssessmentAttempt.id != exclude_attempt_id,
        )
    )
    return int(db.execute(stmt).scalar_one()) > 0


@dataclass(frozen=True)
class AssessmentUserStats:
    attempts_completed: int
    best_score_percent: float | None
    passed: bool
    open_attempt_id: uuid.UUID | None


def user_stats_by_assessment(
    db: Session, user_id: uuid.UUID, assessment_ids: Collection[uuid.UUID]
) -> dict[uuid.UUID, AssessmentUserStats]:
    if not assessment_ids:
        return {}
    completed = (
        select(
            AssessmentAttempt.assessment_id,
            func.count().label("attempts"),
            func.max(AssessmentAttempt.score_percent).label("best"),
            func.bool_or(AssessmentAttempt.passed).label("passed"),
        )
        .where(
            AssessmentAttempt.user_id == user_id,
            AssessmentAttempt.assessment_id.in_(assessment_ids),
            AssessmentAttempt.status == AttemptStatus.COMPLETED,
        )
        .group_by(AssessmentAttempt.assessment_id)
    )
    open_stmt = select(AssessmentAttempt.assessment_id, AssessmentAttempt.id).where(
        AssessmentAttempt.user_id == user_id,
        AssessmentAttempt.assessment_id.in_(assessment_ids),
        AssessmentAttempt.status == AttemptStatus.IN_PROGRESS,
    )
    open_by_assessment = {a: i for a, i in db.execute(open_stmt).all()}
    result: dict[uuid.UUID, AssessmentUserStats] = {}
    for assessment_id, attempts, best, passed in db.execute(completed).all():
        result[assessment_id] = AssessmentUserStats(
            attempts_completed=int(attempts),
            best_score_percent=float(best) if best is not None else None,
            passed=bool(passed),
            open_attempt_id=open_by_assessment.get(assessment_id),
        )
    for assessment_id, open_id in open_by_assessment.items():
        result.setdefault(assessment_id, AssessmentUserStats(0, None, False, open_id))
    return result


# --------------------------------------------------------------------------
# Mastery coverage and statistics
# --------------------------------------------------------------------------


def _latest_response_subquery(user_id: uuid.UUID):  # type: ignore[no-untyped-def]
    """Per question, the user's most recent response in a FINISHED attempt
    (rn == 1); responses of attempts still in progress never count."""
    return (
        select(
            QuestionResponse.question_id.label("question_id"),
            QuestionResponse.is_correct.label("is_correct"),
            func.row_number()
            .over(
                partition_by=QuestionResponse.question_id,
                order_by=(
                    AssessmentAttempt.completed_at.desc(),
                    QuestionResponse.answered_at.desc(),
                ),
            )
            .label("rn"),
        )
        .join(AssessmentAttempt, AssessmentAttempt.id == QuestionResponse.attempt_id)
        .where(
            QuestionResponse.user_id == user_id,
            AssessmentAttempt.status == AttemptStatus.COMPLETED,
        )
        .subquery()
    )


def count_active_questions_for_competency(db: Session, competency_id: uuid.UUID) -> int:
    stmt = (
        select(func.count())
        .select_from(Question)
        .where(Question.competency_id == competency_id, Question.is_active.is_(True))
    )
    return int(db.execute(stmt).scalar_one())


def count_correct_latest_for_competency(
    db: Session, user_id: uuid.UUID, competency_id: uuid.UUID
) -> int:
    """Distinct active questions of the competency whose latest answer is correct."""
    latest = _latest_response_subquery(user_id)
    stmt = (
        select(func.count())
        .select_from(latest)
        .join(Question, Question.id == latest.c.question_id)
        .where(
            latest.c.rn == 1,
            latest.c.is_correct.is_(True),
            Question.competency_id == competency_id,
            Question.is_active.is_(True),
        )
    )
    return int(db.execute(stmt).scalar_one())


@dataclass(frozen=True)
class CompetencyStatsRow:
    competency_id: uuid.UUID
    competency_name: str
    subject_name: str
    attempts_completed: int
    responses_graded: int
    responses_correct: int
    xp_earned: int
    questions_answered: int


def competency_stats_page(
    db: Session, user_id: uuid.UUID, *, limit: int, offset: int
) -> tuple[list[CompetencyStatsRow], int]:
    """Aggregates over the user's responses in finished attempts, per competency."""
    grouped = (
        select(
            Question.competency_id.label("competency_id"),
            func.count(func.distinct(QuestionResponse.attempt_id)).label("attempts"),
            func.count().filter(QuestionResponse.is_correct.isnot(None)).label("graded"),
            func.count().filter(QuestionResponse.is_correct.is_(True)).label("correct"),
            func.coalesce(func.sum(QuestionResponse.xp_awarded), 0).label("xp"),
            func.count(func.distinct(QuestionResponse.question_id)).label("answered"),
        )
        .select_from(QuestionResponse)
        .join(Question, Question.id == QuestionResponse.question_id)
        .join(
            AssessmentAttempt,
            and_(
                AssessmentAttempt.id == QuestionResponse.attempt_id,
                AssessmentAttempt.status == AttemptStatus.COMPLETED,
            ),
        )
        .where(QuestionResponse.user_id == user_id)
        .group_by(Question.competency_id)
        .subquery()
    )
    total = int(db.execute(select(func.count()).select_from(grouped)).scalar_one())
    stmt = (
        select(
            grouped.c.competency_id,
            Competency.name,
            Subject.name,
            grouped.c.attempts,
            grouped.c.graded,
            grouped.c.correct,
            grouped.c.xp,
            grouped.c.answered,
        )
        .join(Competency, Competency.id == grouped.c.competency_id)
        .join(Subject, Subject.id == Competency.subject_id)
        .order_by(Subject.sort_order, Competency.sort_order, Competency.id)
        .offset(offset)
        .limit(limit)
    )
    rows = [
        CompetencyStatsRow(
            competency_id=cid,
            competency_name=cname,
            subject_name=sname,
            attempts_completed=int(attempts),
            responses_graded=int(graded),
            responses_correct=int(correct),
            xp_earned=int(xp),
            questions_answered=int(answered),
        )
        for cid, cname, sname, attempts, graded, correct, xp, answered in db.execute(stmt).all()
    ]
    return rows, total


def correct_latest_by_competency(
    db: Session, user_id: uuid.UUID, competency_ids: Collection[uuid.UUID]
) -> dict[uuid.UUID, int]:
    if not competency_ids:
        return {}
    latest = _latest_response_subquery(user_id)
    stmt = (
        select(Question.competency_id, func.count())
        .select_from(latest)
        .join(Question, Question.id == latest.c.question_id)
        .where(
            latest.c.rn == 1,
            latest.c.is_correct.is_(True),
            Question.competency_id.in_(competency_ids),
            Question.is_active.is_(True),
        )
        .group_by(Question.competency_id)
    )
    return {cid: int(n) for cid, n in db.execute(stmt).all()}


def first_quiz_by_competency(db: Session) -> dict[uuid.UUID, uuid.UUID]:
    """For each competency, the id of its first active assessment that has at
    least one active question (ordered by sort_order, title, id). One query."""
    stmt = (
        select(Assessment.competency_id, Assessment.id)
        .join(AssessmentQuestion, AssessmentQuestion.assessment_id == Assessment.id)
        .join(Question, Question.id == AssessmentQuestion.question_id)
        .where(
            Assessment.is_active.is_(True),
            Assessment.competency_id.is_not(None),
            Question.is_active.is_(True),
        )
        .group_by(Assessment.id, Assessment.competency_id, Assessment.sort_order, Assessment.title)
        .order_by(Assessment.sort_order, Assessment.title, Assessment.id)
    )
    first: dict[uuid.UUID, uuid.UUID] = {}
    for competency_id, assessment_id in db.execute(stmt).all():
        first.setdefault(competency_id, assessment_id)
    return first


def active_questions_by_competency(
    db: Session, competency_ids: Collection[uuid.UUID]
) -> dict[uuid.UUID, int]:
    if not competency_ids:
        return {}
    stmt = (
        select(Question.competency_id, func.count())
        .where(Question.competency_id.in_(competency_ids), Question.is_active.is_(True))
        .group_by(Question.competency_id)
    )
    return {cid: int(n) for cid, n in db.execute(stmt).all()}
