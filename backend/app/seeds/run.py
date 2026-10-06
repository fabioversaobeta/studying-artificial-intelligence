"""Idempotent seed runner: populates initial catalog content, achievements,
and quests. Safe to re-run — every entity is upserted by its natural unique
key (slug/code), never duplicated.

Usage:
    python -m app.seeds.run
"""

import logging

from sqlalchemy.orm import Session

from app.domain.assessments import xp_for_difficulty
from app.infrastructure.database.session import SessionLocal
from app.models.assessment import (
    Assessment,
    AssessmentQuestion,
    Question,
    QuestionTranslation,
)
from app.models.gamification import Achievement, Quest
from app.models.learning import (
    Challenge,
    Competency,
    CompetencyPrerequisite,
    LearningPath,
    LearningPathItem,
    LearningResource,
    Subject,
)
from app.seeds.content import (
    ACHIEVEMENTS,
    LEARNING_PATHS,
    QUESTS,
    SUBJECTS,
    ChallengeSeed,
    CompetencySeed,
    ResourceSeed,
    SubjectSeed,
)
from app.seeds.questions.loader import load_question_sets
from app.seeds.questions.types import AssessmentSeed, QuestionSeed
from app.seeds.questions.validate import validate_question_sets

logger = logging.getLogger(__name__)


def _upsert_subject(db: Session, seed: SubjectSeed) -> Subject:
    subject = db.query(Subject).filter(Subject.slug == seed.slug).one_or_none()
    if subject is None:
        subject = Subject(slug=seed.slug)
        db.add(subject)
    subject.name = seed.name
    subject.description = seed.description
    subject.icon = seed.icon
    subject.color = seed.color
    subject.sort_order = SUBJECTS.index(seed)
    db.flush()
    return subject


def _upsert_competency(
    db: Session, subject: Subject, seed: CompetencySeed, order: int
) -> Competency:
    competency = (
        db.query(Competency)
        .filter(Competency.subject_id == subject.id, Competency.slug == seed.slug)
        .one_or_none()
    )
    if competency is None:
        competency = Competency(subject_id=subject.id, slug=seed.slug)
        db.add(competency)
    competency.name = seed.name
    competency.description = seed.description
    competency.difficulty = seed.difficulty
    competency.sort_order = order
    db.flush()
    return competency


def _sync_resources(
    db: Session, competency: Competency, resource_seeds: list[ResourceSeed]
) -> None:
    existing_by_title = {
        r.title: r
        for r in db.query(LearningResource).filter(LearningResource.competency_id == competency.id)
    }
    for i, rs in enumerate(resource_seeds):
        resource = existing_by_title.get(rs.title)
        if resource is None:
            resource = LearningResource(competency_id=competency.id, title=rs.title)
            db.add(resource)
        resource.type = rs.type
        resource.url = rs.url
        resource.description = rs.description
        resource.content = rs.content
        resource.sort_order = i
    db.flush()


def _sync_challenges(
    db: Session, competency: Competency, challenge_seeds: list[ChallengeSeed]
) -> None:
    existing_by_title = {
        c.title: c for c in db.query(Challenge).filter(Challenge.competency_id == competency.id)
    }
    for cs in challenge_seeds:
        challenge = existing_by_title.get(cs.title)
        if challenge is None:
            challenge = Challenge(competency_id=competency.id, title=cs.title)
            db.add(challenge)
        challenge.description = cs.description
        challenge.difficulty = cs.difficulty
        challenge.xp_value = cs.xp_value
    db.flush()


def seed_subjects(db: Session) -> dict[tuple[str, str], Competency]:
    competency_by_key: dict[tuple[str, str], Competency] = {}
    # (subject_slug, competency, prerequisite_slug) — prerequisites always live in
    # the same subject as the competency that requires them.
    prerequisite_pairs: list[tuple[str, Competency, str]] = []

    for subject_seed in SUBJECTS:
        subject = _upsert_subject(db, subject_seed)
        for order, competency_seed in enumerate(subject_seed.competencies):
            competency = _upsert_competency(db, subject, competency_seed, order)
            competency_by_key[(subject_seed.slug, competency_seed.slug)] = competency
            _sync_resources(db, competency, competency_seed.resources)
            _sync_challenges(db, competency, competency_seed.challenges)
            for prereq_slug in competency_seed.requires:
                prerequisite_pairs.append((subject_seed.slug, competency, prereq_slug))

    for subject_slug, competency, prereq_slug in prerequisite_pairs:
        prereq = competency_by_key.get((subject_slug, prereq_slug))
        if prereq is None:
            continue
        existing = (
            db.query(CompetencyPrerequisite)
            .filter(
                CompetencyPrerequisite.competency_id == competency.id,
                CompetencyPrerequisite.prerequisite_id == prereq.id,
            )
            .one_or_none()
        )
        if existing is None:
            db.add(CompetencyPrerequisite(competency_id=competency.id, prerequisite_id=prereq.id))

    db.flush()
    return competency_by_key


def seed_learning_paths(db: Session, competency_by_key: dict[tuple[str, str], Competency]) -> None:
    for order, path_seed in enumerate(LEARNING_PATHS):
        path = db.query(LearningPath).filter(LearningPath.slug == path_seed.slug).one_or_none()
        if path is None:
            path = LearningPath(slug=path_seed.slug)
            db.add(path)
        path.title = path_seed.title
        path.description = path_seed.description
        path.sort_order = order
        db.flush()

        existing_competency_ids = {
            item.competency_id
            for item in db.query(LearningPathItem).filter(
                LearningPathItem.learning_path_id == path.id
            )
        }
        for item_order, (subject_slug, competency_slug) in enumerate(path_seed.items):
            competency = competency_by_key.get((subject_slug, competency_slug))
            if competency is None or competency.id in existing_competency_ids:
                continue
            db.add(
                LearningPathItem(
                    learning_path_id=path.id, competency_id=competency.id, sort_order=item_order
                )
            )
    db.flush()


def _upsert_question(db: Session, competency: Competency, seed: QuestionSeed) -> Question:
    question = db.query(Question).filter(Question.code == seed.code).one_or_none()
    if question is None:
        question = Question(code=seed.code)
        db.add(question)
    question.competency_id = competency.id
    question.type = seed.type
    question.difficulty = seed.difficulty
    question.xp_value = xp_for_difficulty(seed.difficulty.value)
    question.correct_option_ids = list(seed.correct) if seed.correct is not None else None
    question.tags = list(seed.tags)
    question.source = seed.source
    question.is_active = True
    db.flush()

    existing = {
        t.language: t for t in db.query(QuestionTranslation).filter_by(question_id=question.id)
    }
    for language, text in seed.text.items():
        translation = existing.pop(language, None)
        if translation is None:
            translation = QuestionTranslation(question_id=question.id, language=language)
            db.add(translation)
        translation.prompt = text.prompt
        translation.options = (
            [{"id": o.id, "text": o.text} for o in text.options] if text.options else None
        )
        translation.explanation = text.explanation
        translation.model_answer = text.model_answer
    for stale in existing.values():  # a language removed from the seed
        db.delete(stale)
    db.flush()
    return question


def _upsert_assessment(
    db: Session,
    seed: AssessmentSeed,
    order: int,
    competency_by_key: dict[tuple[str, str], Competency],
    subject_slug: str,
    question_by_code: dict[str, Question],
    set_question_codes: list[str],
) -> Assessment:
    assessment = db.query(Assessment).filter(Assessment.code == seed.code).one_or_none()
    if assessment is None:
        assessment = Assessment(code=seed.code)
        db.add(assessment)
    assessment.title = seed.title
    assessment.description = seed.description
    assessment.translations = {lang: dict(content) for lang, content in seed.translations.items()}
    assessment.kind = seed.kind
    assessment.pass_threshold = seed.pass_threshold
    assessment.completion_bonus_xp = seed.completion_bonus_xp
    assessment.sort_order = order
    assessment.is_active = True
    competency = (
        competency_by_key.get((subject_slug, seed.competency_slug))
        if seed.competency_slug
        else None
    )
    assessment.competency_id = competency.id if competency else None
    path = (
        db.query(LearningPath).filter(LearningPath.slug == seed.learning_path_slug).one_or_none()
        if seed.learning_path_slug
        else None
    )
    assessment.learning_path_id = path.id if path else None
    db.flush()

    codes = (
        list(seed.question_codes)
        if seed.question_codes is not None
        else [
            code
            for code in set_question_codes
            if competency is not None and question_by_code[code].competency_id == competency.id
        ]
    )
    existing = {
        m.question_id: m
        for m in db.query(AssessmentQuestion).filter_by(assessment_id=assessment.id)
    }
    for position, code in enumerate(codes):
        question = question_by_code[code]
        membership = existing.pop(question.id, None)
        if membership is None:
            db.add(
                AssessmentQuestion(
                    assessment_id=assessment.id, question_id=question.id, sort_order=position
                )
            )
        else:
            membership.sort_order = position
    for stale in existing.values():
        db.delete(stale)
    db.flush()
    return assessment


def seed_questions(db: Session, competency_by_key: dict[tuple[str, str], Competency]) -> int:
    """Upsert the question bank and its assessments (idempotent, keyed by code).

    Refuses to seed a bank that fails the validator, so a bad batch never
    reaches the database. Returns the number of questions seeded.
    """
    sets = load_question_sets()
    errors = validate_question_sets(sets)
    if errors:
        problems = "\n".join(f"  - {e}" for e in errors)
        raise ValueError(f"Invalid question seeds:\n{problems}")

    question_by_code: dict[str, Question] = {}
    for question_set in sets:
        for seed in question_set.questions:
            competency = competency_by_key[(question_set.subject_slug, seed.competency_slug)]
            question_by_code[seed.code] = _upsert_question(db, competency, seed)

    order = 0
    for question_set in sets:
        set_codes = [q.code for q in question_set.questions]
        for assessment_seed in question_set.assessments:
            _upsert_assessment(
                db,
                assessment_seed,
                order,
                competency_by_key,
                question_set.subject_slug,
                question_by_code,
                set_codes,
            )
            order += 1
    db.flush()
    return len(question_by_code)


def seed_achievements(db: Session) -> None:
    for seed in ACHIEVEMENTS:
        achievement = db.query(Achievement).filter(Achievement.code == seed.code).one_or_none()
        if achievement is None:
            achievement = Achievement(code=seed.code)
            db.add(achievement)
        achievement.name = seed.name
        achievement.description = seed.description
        achievement.icon = seed.icon
        achievement.criteria_type = seed.criteria_type
        achievement.criteria_value = seed.criteria_value
        achievement.xp_reward = seed.xp_reward
    db.flush()


def seed_quests(db: Session) -> None:
    for seed in QUESTS:
        quest = db.query(Quest).filter(Quest.code == seed.code).one_or_none()
        if quest is None:
            quest = Quest(code=seed.code)
            db.add(quest)
        quest.title = seed.title
        quest.description = seed.description
        quest.criteria_type = seed.criteria_type
        quest.criteria_value = seed.criteria_value
        quest.period = seed.period
        quest.xp_reward = seed.xp_reward
        quest.is_active = True
    db.flush()


def run() -> None:
    db = SessionLocal()
    try:
        competency_by_key = seed_subjects(db)
        seed_learning_paths(db, competency_by_key)
        seed_achievements(db)
        seed_quests(db)
        question_count = seed_questions(db, competency_by_key)
        db.commit()
        logger.info(
            "Seed complete: %d subjects, %d competencies, %d learning paths, "
            "%d achievements, %d quests, %d questions",
            len(SUBJECTS),
            len(competency_by_key),
            len(LEARNING_PATHS),
            len(ACHIEVEMENTS),
            len(QUESTS),
            question_count,
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
