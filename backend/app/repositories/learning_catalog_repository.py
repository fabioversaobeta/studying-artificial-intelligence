"""Read access to seeded catalog content: subjects, competencies, prerequisite
edges, learning paths, and resources. This content is authored via seeds
(app.seeds), not through user-facing write endpoints, in v1.
"""

import uuid
from collections.abc import Collection

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.learning import (
    Competency,
    CompetencyPrerequisite,
    LearningPath,
    LearningPathItem,
    LearningResource,
    Subject,
)


def list_subjects(db: Session) -> list[Subject]:
    stmt = select(Subject).order_by(Subject.sort_order, Subject.name)
    return list(db.execute(stmt).scalars().all())


def get_subject(db: Session, subject_id: uuid.UUID) -> Subject | None:
    return db.get(Subject, subject_id)


def get_subject_by_slug(db: Session, slug: str) -> Subject | None:
    stmt = select(Subject).where(Subject.slug == slug)
    return db.execute(stmt).scalar_one_or_none()


def list_competencies_by_subject(db: Session, subject_id: uuid.UUID) -> list[Competency]:
    stmt = (
        select(Competency)
        .where(Competency.subject_id == subject_id)
        .order_by(Competency.sort_order, Competency.name)
    )
    return list(db.execute(stmt).scalars().all())


def get_competency(db: Session, competency_id: uuid.UUID) -> Competency | None:
    return db.get(Competency, competency_id)


def list_all_competencies(db: Session) -> list[Competency]:
    stmt = select(Competency).options(selectinload(Competency.subject))
    return list(db.execute(stmt).scalars().all())


def get_prerequisite_ids(db: Session, competency_id: uuid.UUID) -> list[uuid.UUID]:
    stmt = select(CompetencyPrerequisite.prerequisite_id).where(
        CompetencyPrerequisite.competency_id == competency_id
    )
    return list(db.execute(stmt).scalars().all())


def list_all_prerequisite_edges(db: Session) -> list[tuple[uuid.UUID, uuid.UUID]]:
    stmt = select(CompetencyPrerequisite.competency_id, CompetencyPrerequisite.prerequisite_id)
    return [(row[0], row[1]) for row in db.execute(stmt).all()]


def list_learning_paths(db: Session) -> list[LearningPath]:
    stmt = (
        select(LearningPath)
        .options(selectinload(LearningPath.items).joinedload(LearningPathItem.competency))
        .order_by(LearningPath.sort_order, LearningPath.title)
    )
    return list(db.execute(stmt).scalars().all())


def get_learning_path_by_slug(db: Session, slug: str) -> LearningPath | None:
    stmt = (
        select(LearningPath)
        .options(selectinload(LearningPath.items).joinedload(LearningPathItem.competency))
        .where(LearningPath.slug == slug)
    )
    return db.execute(stmt).scalar_one_or_none()


def list_resources_by_competency(db: Session, competency_id: uuid.UUID) -> list[LearningResource]:
    stmt = (
        select(LearningResource)
        .where(LearningResource.competency_id == competency_id)
        .order_by(LearningResource.sort_order)
    )
    return list(db.execute(stmt).scalars().all())


def list_competencies_by_subjects(
    db: Session, subject_ids: Collection[uuid.UUID]
) -> dict[uuid.UUID, list[Competency]]:
    """Batch variant of `list_competencies_by_subject`: one query for all subjects."""
    grouped: dict[uuid.UUID, list[Competency]] = {sid: [] for sid in subject_ids}
    if not grouped:
        return grouped
    stmt = (
        select(Competency)
        .where(Competency.subject_id.in_(grouped.keys()))
        .order_by(Competency.sort_order, Competency.name)
    )
    for competency in db.execute(stmt).scalars():
        grouped[competency.subject_id].append(competency)
    return grouped


def get_prerequisite_ids_by_competency(
    db: Session, competency_ids: Collection[uuid.UUID]
) -> dict[uuid.UUID, list[uuid.UUID]]:
    """Batch variant of `get_prerequisite_ids`: one query for all competencies."""
    grouped: dict[uuid.UUID, list[uuid.UUID]] = {cid: [] for cid in competency_ids}
    if not grouped:
        return grouped
    stmt = select(
        CompetencyPrerequisite.competency_id, CompetencyPrerequisite.prerequisite_id
    ).where(CompetencyPrerequisite.competency_id.in_(grouped.keys()))
    for competency_id, prerequisite_id in db.execute(stmt).all():
        grouped[competency_id].append(prerequisite_id)
    return grouped
