"""Typed format of the question-bank seed files (the contract between the
authors of questions, the validator and the loader).

One module per subject in this package (e.g. ``python_subject.py``) exports a
single ``QUESTION_SET: SubjectQuestionSet``. Modules are discovered
automatically (see ``loader.py``), so adding a subject never touches a shared
file. The format and its rules are documented in docs/DOMAIN.md
("Question seed format"); ``validate.py`` enforces them.
"""

from dataclasses import dataclass, field

from app.models.assessment import (
    AssessmentKind,
    QuestionDifficulty,
    QuestionSource,
    QuestionType,
)
from app.models.user import Language


@dataclass(frozen=True)
class OptionSeed:
    id: str  # short, stable, language-independent: "a", "b", ...
    text: str


@dataclass(frozen=True)
class QuestionText:
    """The human-readable content of a question in ONE language."""

    prompt: str  # markdown; code_reading puts the snippet in a fenced block
    explanation: str  # why the answer is right (and common wrong ones are wrong)
    options: tuple[OptionSeed, ...] | None = None  # None for short_answer
    model_answer: str | None = None  # short_answer only: the reference answer


@dataclass(frozen=True)
class QuestionSeed:
    code: str  # globally unique and stable, e.g. "python-type-hints-q01"
    competency_slug: str  # must exist in app.seeds.content for this subject
    type: QuestionType
    difficulty: QuestionDifficulty
    # Option ids; exactly one for multiple_choice / code_reading, two or more for
    # multi_select, None for short_answer.
    correct: tuple[str, ...] | None
    # `Language.EN` is mandatory; `Language.PT_BR` is optional (falls back to en).
    text: dict[Language, QuestionText]
    tags: tuple[str, ...] = ()
    source: QuestionSource = QuestionSource.AI_GENERATED


@dataclass(frozen=True)
class AssessmentSeed:
    code: str  # globally unique and stable
    title: str  # English
    kind: AssessmentKind
    description: str | None = None
    # Required for kind=competency (the competency slug in the set's subject).
    competency_slug: str | None = None
    # Required for kind=learning_path (a slug from app.seeds.content.LEARNING_PATHS).
    learning_path_slug: str | None = None
    # Question codes, in order (may reference questions of any set, so mixed and
    # learning-path assessments can cross subjects). None on a competency
    # assessment means "every question of that competency in this set" (the
    # usual case); it is required for the other kinds.
    question_codes: tuple[str, ...] | None = None
    # {"pt-BR": {"title": "...", "description": "..."}}
    translations: dict[str, dict[str, str]] = field(default_factory=dict)
    pass_threshold: int = 70
    completion_bonus_xp: int = 25


@dataclass(frozen=True)
class SubjectQuestionSet:
    subject_slug: str
    questions: tuple[QuestionSeed, ...]
    assessments: tuple[AssessmentSeed, ...] = ()
