"""Assessments (quizzes) use cases: list, start, answer, self-grade, finish,
history and statistics.

Rules worth knowing before editing (full rationale in docs/DECISIONS.md):

* Grading of choice questions is deterministic and stored when the answer is
  saved, but correctness is NOT revealed until the attempt is finished (a
  short answer reveals its model answer immediately, because self-grading needs
  it, and that carries no graded verdict).
* XP is awarded only when an attempt is finished, only if it passed, and only
  for questions never paid before + a completion bonus on the first pass. It is
  never refunded. All profile mutation goes through ``gamification_service``.
* Finishing recomputes mastery of every touched competency, flags competencies
  with wrong answers for spaced-repetition review, and counts as streak
  activity even when no XP is paid.
"""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.domain.assessments import (
    CHOICE_TYPES,
    SINGLE_ANSWER_TYPES,
    compute_attempt_xp,
    grade_choice,
    is_passing,
    score_percent,
)
from app.models.assessment import (
    Assessment,
    AssessmentAttempt,
    AssessmentKind,
    AttemptStatus,
    GradingStatus,
    Question,
    QuestionResponse,
    QuestionTranslation,
    QuestionType,
)
from app.models.gamification import XPSource
from app.models.user import DEFAULT_LANGUAGE, Language, User
from app.repositories import assessment_repository, learning_catalog_repository
from app.schemas.assessment import (
    AnswerResult,
    AnswerSubmit,
    AssessmentRead,
    AttemptDetail,
    AttemptQuestion,
    AttemptSummary,
    CompetencyAssessmentStats,
    OptionRead,
    QuestionReview,
    SavedAnswer,
)
from app.services import gamification_service, mastery_service, review_service

# --------------------------------------------------------------------------
# Short-answer judging: the extension point for roadmap item I5.
#
# A judge looks at a question and the learner's text and returns True/False
# when it can decide, or None to leave the answer `pending_review` for the
# learner's guided self-assessment (the only behaviour today; no AI is called).
# An AI judge would be plugged here (and would add its own GradingStatus), but
# per docs/PROPOSAL_TRACK_I.md it must not pay XP/mastery before it is validated
# against a golden dataset.
# --------------------------------------------------------------------------
ShortAnswerJudge = Callable[[Question, str], bool | None]


def self_assessment_judge(question: Question, text: str) -> bool | None:
    return None


short_answer_judge: ShortAnswerJudge = self_assessment_judge


# --------------------------------------------------------------------------
# Language helpers
# --------------------------------------------------------------------------


def resolve_language(user: User, override: Language | None) -> Language:
    """`?lang=` wins; otherwise the user's saved preference."""
    return override or user.preferred_language


def _translation(question: Question, language: Language) -> QuestionTranslation:
    """Translation in `language`, falling back to English (then to anything)."""
    by_language = {t.language: t for t in question.translations}
    for candidate in (language, DEFAULT_LANGUAGE):
        if candidate in by_language:
            return by_language[candidate]
    if by_language:
        return next(iter(by_language.values()))
    raise ConflictError(f"Question {question.code} has no translations")


def _localized(assessment: Assessment, language: Language) -> tuple[str, str | None]:
    override = assessment.translations.get(language.value, {})
    return override.get("title") or assessment.title, (
        override.get("description") or assessment.description
    )


def _option_ids(translation: QuestionTranslation) -> list[str]:
    return [str(option["id"]) for option in (translation.options or [])]


# --------------------------------------------------------------------------
# Catalog
# --------------------------------------------------------------------------


def list_assessments(
    db: Session,
    user: User,
    *,
    competency_id: uuid.UUID | None = None,
    kind: AssessmentKind | None = None,
    lang: Language | None = None,
    limit: int,
    offset: int,
) -> tuple[list[AssessmentRead], int]:
    if (
        competency_id is not None
        and learning_catalog_repository.get_competency(db, competency_id) is None
    ):
        raise NotFoundError("Competency not found")

    language = resolve_language(user, lang)
    assessments, total = assessment_repository.list_assessments(
        db, competency_id=competency_id, kind=kind, limit=limit, offset=offset
    )
    ids = [a.id for a in assessments]
    counts = assessment_repository.count_active_questions_by_assessment(db, ids)
    stats = assessment_repository.user_stats_by_assessment(db, user.id, ids)

    items = []
    for assessment in assessments:
        title, description = _localized(assessment, language)
        user_stats = stats.get(assessment.id)
        items.append(
            AssessmentRead(
                id=assessment.id,
                code=assessment.code,
                title=title,
                description=description,
                kind=assessment.kind,
                competency_id=assessment.competency_id,
                competency_name=assessment.competency.name if assessment.competency else None,
                pass_threshold=assessment.pass_threshold,
                completion_bonus_xp=assessment.completion_bonus_xp,
                question_count=counts.get(assessment.id, 0),
                attempts_completed=user_stats.attempts_completed if user_stats else 0,
                best_score_percent=user_stats.best_score_percent if user_stats else None,
                passed=user_stats.passed if user_stats else False,
                open_attempt_id=user_stats.open_attempt_id if user_stats else None,
            )
        )
    return items, total


# --------------------------------------------------------------------------
# Attempt views
# --------------------------------------------------------------------------


def _saved_answer(response: QuestionResponse) -> SavedAnswer:
    return SavedAnswer(
        option_ids=response.answer.get("option_ids"),
        text=response.answer.get("text"),
        grading_status=response.grading_status,
        time_spent_seconds=response.time_spent_seconds,
    )


def _build_question(
    question: Question,
    position: int,
    language: Language,
    response: QuestionResponse | None,
    *,
    reveal: bool,
) -> AttemptQuestion:
    translation = _translation(question, language)
    options = (
        [OptionRead(id=str(o["id"]), text=str(o["text"])) for o in translation.options]
        if translation.options
        else None
    )
    review = None
    if reveal:
        review = QuestionReview(
            correct_option_ids=question.correct_option_ids,
            explanation=translation.explanation,
            model_answer=translation.model_answer,
            is_correct=response.is_correct if response else False,
            grading_status=response.grading_status if response else GradingStatus.GRADED,
            xp_awarded=response.xp_awarded if response else 0,
            is_first_correct=response.is_first_correct if response else False,
        )
    return AttemptQuestion(
        id=question.id,
        position=position,
        type=question.type,
        difficulty=question.difficulty,
        xp_value=question.xp_value,
        tags=list(question.tags),
        prompt=translation.prompt,
        options=options,
        language=translation.language,
        answer=_saved_answer(response) if response else None,
        review=review,
    )


def _summary_fields(attempt: AssessmentAttempt, language: Language) -> dict[str, Any]:
    title, _ = _localized(attempt.assessment, language)
    return {
        "id": attempt.id,
        "assessment_id": attempt.assessment_id,
        "assessment_title": title,
        "status": attempt.status,
        "started_at": attempt.started_at,
        "completed_at": attempt.completed_at,
        "total_questions": attempt.total_questions,
        "correct_count": attempt.correct_count,
        "score_percent": attempt.score_percent,
        "passed": attempt.passed,
        "xp_awarded": attempt.xp_awarded,
    }


def _build_detail(db: Session, attempt: AssessmentAttempt, language: Language) -> AttemptDetail:
    questions = assessment_repository.get_questions_by_ids(
        db, [uuid.UUID(q) for q in attempt.question_ids]
    )
    responses = {r.question_id: r for r in assessment_repository.list_responses(db, attempt.id)}
    completed = attempt.status == AttemptStatus.COMPLETED

    items = []
    for position, raw_id in enumerate(attempt.question_ids, start=1):
        question = questions.get(uuid.UUID(raw_id))
        if question is None:  # deleted from the bank after the attempt started
            continue
        items.append(
            _build_question(
                question, position, language, responses.get(question.id), reveal=completed
            )
        )

    return AttemptDetail(
        **_summary_fields(attempt, language),
        pass_threshold=attempt.assessment.pass_threshold,
        answered_count=len(responses),
        xp_questions=attempt.xp_questions,
        xp_bonus=attempt.xp_bonus,
        pending_review_count=sum(
            1 for r in responses.values() if r.grading_status == GradingStatus.PENDING_REVIEW
        )
        if completed
        else 0,
        questions=items,
    )


def _own_attempt(
    db: Session, user: User, attempt_id: uuid.UUID, *, for_update: bool = False
) -> AssessmentAttempt:
    attempt = assessment_repository.get_attempt(db, attempt_id, for_update=for_update)
    if attempt is None or attempt.user_id != user.id:
        raise NotFoundError("Attempt not found")
    return attempt


# --------------------------------------------------------------------------
# Start / read
# --------------------------------------------------------------------------


def start_attempt(
    db: Session, user: User, assessment_id: uuid.UUID, *, lang: Language | None = None
) -> tuple[AttemptDetail, bool]:
    """Start an attempt, or resume the open one. Returns (detail, created)."""
    language = resolve_language(user, lang)
    assessment = assessment_repository.get_assessment(db, assessment_id)
    if assessment is None or not assessment.is_active:
        raise NotFoundError("Assessment not found")

    open_attempt = assessment_repository.get_open_attempt(db, user.id, assessment.id)
    if open_attempt is not None:
        return _build_detail(db, open_attempt, language), False

    questions = assessment_repository.list_active_assessment_questions(db, assessment.id)
    if not questions:
        raise ConflictError("This assessment has no active questions yet")

    try:
        with db.begin_nested():
            attempt = assessment_repository.create_attempt(
                db,
                user_id=user.id,
                assessment_id=assessment.id,
                question_ids=[str(q.id) for q in questions],
                started_at=datetime.now(UTC),
            )
    except IntegrityError:
        # Lost a race with a concurrent start: resume the attempt that won.
        existing = assessment_repository.get_open_attempt(db, user.id, assessment.id)
        if existing is None:
            raise
        return _build_detail(db, existing, language), False

    db.commit()
    attempt = _own_attempt(db, user, attempt.id)
    return _build_detail(db, attempt, language), True


def get_attempt(
    db: Session, user: User, attempt_id: uuid.UUID, *, lang: Language | None = None
) -> AttemptDetail:
    attempt = _own_attempt(db, user, attempt_id)
    return _build_detail(db, attempt, resolve_language(user, lang))


def list_attempts(
    db: Session,
    user: User,
    *,
    assessment_id: uuid.UUID | None,
    lang: Language | None,
    limit: int,
    offset: int,
) -> tuple[list[AttemptSummary], int]:
    language = resolve_language(user, lang)
    attempts, total = assessment_repository.list_attempts(
        db, user.id, assessment_id=assessment_id, limit=limit, offset=offset
    )
    return [AttemptSummary(**_summary_fields(a, language)) for a in attempts], total


# --------------------------------------------------------------------------
# Answering
# --------------------------------------------------------------------------


def _attempt_question(db: Session, attempt: AssessmentAttempt, question_id: uuid.UUID) -> Question:
    if str(question_id) not in attempt.question_ids:
        raise NotFoundError("Question is not part of this attempt")
    question = assessment_repository.get_questions_by_ids(db, [question_id]).get(question_id)
    if question is None:
        raise NotFoundError("Question not found")
    return question


def _require_in_progress(attempt: AssessmentAttempt) -> None:
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise ConflictError("This attempt is already finished")


def _validated_option_ids(question: Question, payload: AnswerSubmit) -> list[str]:
    selected = list(dict.fromkeys(payload.option_ids or []))  # de-duplicated, order kept
    if not selected:
        raise ValidationAppError("Select at least one option")
    if question.type in SINGLE_ANSWER_TYPES and len(selected) != 1:
        raise ValidationAppError("Select exactly one option")
    valid = _option_ids(_translation(question, DEFAULT_LANGUAGE))
    unknown = [o for o in selected if o not in valid]
    if unknown:
        raise ValidationAppError("Unknown option id")
    return selected


def save_answer(
    db: Session,
    user: User,
    attempt_id: uuid.UUID,
    question_id: uuid.UUID,
    payload: AnswerSubmit,
    *,
    lang: Language | None = None,
) -> AnswerResult:
    """Save (or replace) the answer to one question of an open attempt.

    For choice questions the verdict is stored but deliberately not returned.
    """
    attempt = _own_attempt(db, user, attempt_id)
    _require_in_progress(attempt)
    question = _attempt_question(db, attempt, question_id)

    answer: dict[str, Any]
    is_correct: bool | None
    status: GradingStatus
    if question.type in CHOICE_TYPES:
        selected = _validated_option_ids(question, payload)
        answer = {"option_ids": selected}
        is_correct = grade_choice(question.correct_option_ids or [], selected)
        status = GradingStatus.GRADED
    else:
        text = (payload.text or "").strip()
        if not text:
            raise ValidationAppError("Write an answer first")
        answer = {"text": text}
        is_correct = short_answer_judge(question, text)
        status = GradingStatus.PENDING_REVIEW if is_correct is None else GradingStatus.GRADED

    response = assessment_repository.get_response(db, attempt.id, question.id)
    if response is None:
        response = assessment_repository.add_response(
            db,
            QuestionResponse(
                attempt_id=attempt.id,
                question_id=question.id,
                user_id=user.id,
                answer=answer,
                grading_status=status,
                is_correct=is_correct,
                time_spent_seconds=payload.time_spent_seconds,
                answered_at=datetime.now(UTC),
            ),
        )
    else:
        response.answer = answer
        response.grading_status = status
        response.is_correct = is_correct
        response.time_spent_seconds = payload.time_spent_seconds
        response.answered_at = datetime.now(UTC)
    db.commit()

    result = AnswerResult(question_id=question.id, grading_status=response.grading_status)
    if question.type == QuestionType.SHORT_ANSWER:
        translation = _translation(question, resolve_language(user, lang))
        result.model_answer = translation.model_answer
        result.explanation = translation.explanation
    return result


def self_grade(
    db: Session,
    user: User,
    attempt_id: uuid.UUID,
    question_id: uuid.UUID,
    *,
    is_correct: bool,
    lang: Language | None = None,
) -> AnswerResult:
    """The learner marks their own short answer right/wrong after reading the
    model answer. Only while the attempt is open (XP is settled at finish)."""
    attempt = _own_attempt(db, user, attempt_id)
    _require_in_progress(attempt)
    question = _attempt_question(db, attempt, question_id)
    if question.type != QuestionType.SHORT_ANSWER:
        raise ValidationAppError("Only short-answer questions are self-graded")
    response = assessment_repository.get_response(db, attempt.id, question.id)
    if response is None:
        raise ValidationAppError("Save an answer before grading it")

    response.is_correct = is_correct
    response.grading_status = GradingStatus.SELF_GRADED
    db.commit()

    translation = _translation(question, resolve_language(user, lang))
    return AnswerResult(
        question_id=question.id,
        grading_status=response.grading_status,
        model_answer=translation.model_answer,
        explanation=translation.explanation,
        is_correct=is_correct,
    )


# --------------------------------------------------------------------------
# Finish
# --------------------------------------------------------------------------


def finish_attempt(
    db: Session, user: User, attempt_id: uuid.UUID, *, lang: Language | None = None
) -> AttemptDetail:
    """Score the attempt, settle XP / mastery / review flags, and reveal results.

    Idempotent: finishing a finished attempt returns the stored result and pays
    nothing again. The attempt row is locked so two concurrent finishes cannot
    both pay.
    """
    language = resolve_language(user, lang)
    attempt = _own_attempt(db, user, attempt_id, for_update=True)
    if attempt.status == AttemptStatus.COMPLETED:
        return _build_detail(db, attempt, language)

    assessment = attempt.assessment
    questions = assessment_repository.get_questions_by_ids(
        db, [uuid.UUID(q) for q in attempt.question_ids]
    )
    responses = {r.question_id: r for r in assessment_repository.list_responses(db, attempt.id)}

    correct = [r for r in responses.values() if r.is_correct is True]
    correct_ids = [r.question_id for r in correct]
    total = attempt.total_questions
    passed = is_passing(len(correct), total, assessment.pass_threshold)

    already_correct = assessment_repository.correct_question_ids_before(
        db, user.id, correct_ids, exclude_attempt_id=attempt.id
    )
    already_paid = assessment_repository.paid_question_ids(db, user.id, correct_ids)
    first_pass = passed and not assessment_repository.has_passed_before(
        db, user.id, assessment.id, exclude_attempt_id=attempt.id
    )

    for response in correct:
        response.is_first_correct = response.question_id not in already_correct

    payable = [
        r for r in correct if r.question_id not in already_paid and r.question_id in questions
    ]
    xp = compute_attempt_xp(
        passed=passed,
        unpaid_correct_xp_values=[questions[r.question_id].xp_value for r in payable],
        is_first_pass=first_pass,
        completion_bonus_xp=assessment.completion_bonus_xp,
    )
    if passed:
        for response in payable:
            response.xp_awarded = questions[response.question_id].xp_value

    attempt.status = AttemptStatus.COMPLETED
    attempt.completed_at = datetime.now(UTC)
    attempt.correct_count = len(correct)
    attempt.score_percent = score_percent(len(correct), total)
    attempt.passed = passed
    attempt.xp_questions = xp.questions_xp
    attempt.xp_bonus = xp.completion_bonus_xp
    attempt.xp_awarded = xp.total
    db.flush()

    # Mastery measures knowledge: refresh every competency this attempt touched.
    competency_ids = {q.competency_id for q in questions.values()}
    for competency_id in competency_ids:
        mastery_service.recompute_mastery(db, user_id=user.id, competency_id=competency_id)

    # A wrong (graded) answer puts its competency back in the review queue.
    missed_competencies = {
        questions[r.question_id].competency_id
        for r in responses.values()
        if r.is_correct is False and r.question_id in questions
    }
    for competency_id in missed_competencies:
        review_service.flag_for_review(db, user_id=user.id, competency_id=competency_id)

    if xp.total > 0:
        gamification_service.award_xp(
            db,
            user_id=user.id,
            amount=xp.total,
            source=XPSource.ASSESSMENT,
            reference_id=attempt.id,
            description=f"Assessment passed: {assessment.title}",
        )
    else:
        # Finished practice still counts for the streak, with or without XP.
        gamification_service.record_activity(db, user.id)

    db.commit()
    db.refresh(attempt)
    return _build_detail(db, attempt, language)


# --------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------


def competency_stats(
    db: Session, user: User, *, limit: int, offset: int
) -> tuple[list[CompetencyAssessmentStats], int]:
    rows, total = assessment_repository.competency_stats_page(
        db, user.id, limit=limit, offset=offset
    )
    ids = [row.competency_id for row in rows]
    banks = assessment_repository.active_questions_by_competency(db, ids)
    correct_latest = assessment_repository.correct_latest_by_competency(db, user.id, ids)

    items = []
    for row in rows:
        bank = banks.get(row.competency_id, 0)
        correct = min(correct_latest.get(row.competency_id, 0), bank)
        items.append(
            CompetencyAssessmentStats(
                competency_id=row.competency_id,
                competency_name=row.competency_name,
                subject_name=row.subject_name,
                questions_total=bank,
                questions_answered=row.questions_answered,
                questions_correct=correct,
                coverage_percent=score_percent(correct, bank),
                attempts_completed=row.attempts_completed,
                responses_graded=row.responses_graded,
                responses_correct=row.responses_correct,
                accuracy_percent=(
                    score_percent(row.responses_correct, row.responses_graded)
                    if row.responses_graded
                    else None
                ),
                xp_earned=row.xp_earned,
            )
        )
    return items, total
