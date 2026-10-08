"""Automatic validation of the question-bank seeds (structure + consistency).

Run it before committing new questions::

    python -m app.seeds.questions.validate

It exits non-zero and prints every problem it finds. ``app.seeds.run`` runs the
same checks and refuses to seed a bank that does not pass, so a bad batch can
never reach the database. This is the contract for the bulk generation of
questions (roadmap I6): anything that passes here is structurally safe; the
*pedagogical* review (is the answer actually right?) stays a human job.
"""

import argparse
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence

from app.domain.assessments import CHOICE_TYPES, MULTI_ANSWER_TYPES, SINGLE_ANSWER_TYPES
from app.models.assessment import (
    AssessmentKind,
    QuestionDifficulty,
    QuestionSource,
    QuestionType,
)
from app.models.user import DEFAULT_LANGUAGE, Language
from app.seeds.content import LEARNING_PATHS, SUBJECTS, LearningPathSeed, SubjectSeed
from app.seeds.questions.loader import load_question_sets
from app.seeds.questions.types import (
    AssessmentSeed,
    QuestionSeed,
    QuestionText,
    SubjectQuestionSet,
)

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
OPTION_ID_RE = re.compile(r"^[a-z0-9_]{1,10}$")
FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
MIN_OPTIONS = 2
MAX_OPTIONS = 8

# --- Quality-bias warnings (never errors; ``--strict`` makes them fail) -------
# Evaluated per competency, on the English text, over single-answer choice
# questions (multiple_choice / code_reading) that have at least
# LENGTH_BIAS_MIN_OPTIONS options. multi_select and short_answer are ignored.
LENGTH_BIAS_MIN_OPTIONS = 3
# Warn when the correct option is the strictly longest one in MORE than this
# share of a competency's questions (and the competency has enough questions).
LENGTH_BIAS_MAX_SHARE = 0.5
LENGTH_BIAS_MIN_QUESTIONS = 4
# Warn when one letter holds MORE than this share of the correct answers of a
# competency that has at least POSITION_BIAS_MIN_QUESTIONS such questions.
POSITION_BIAS_MAX_SHARE = 0.4
POSITION_BIAS_MIN_QUESTIONS = 8


def _norm(text: str) -> str:
    return " ".join(text.casefold().split())


def _validate_text(
    q: QuestionSeed, language: Language, text: QuestionText, where: str
) -> list[str]:
    errors: list[str] = []
    if not text.prompt.strip():
        errors.append(f"{where}: empty prompt")
    if not text.explanation.strip():
        errors.append(f"{where}: empty explanation")

    if q.type in CHOICE_TYPES:
        if text.model_answer is not None:
            errors.append(f"{where}: model_answer is only for short_answer")
        options = text.options
        if options is None:
            return [*errors, f"{where}: choice question without options"]
        if not MIN_OPTIONS <= len(options) <= MAX_OPTIONS:
            errors.append(f"{where}: needs {MIN_OPTIONS}-{MAX_OPTIONS} options, has {len(options)}")
        ids = [o.id for o in options]
        for option_id in ids:
            if not OPTION_ID_RE.match(option_id):
                errors.append(f"{where}: invalid option id {option_id!r}")
        if len(set(ids)) != len(ids):
            errors.append(f"{where}: duplicate option ids")
        texts = [_norm(o.text) for o in options]
        if any(not t for t in texts):
            errors.append(f"{where}: empty option text")
        if len(set(texts)) != len(texts):
            errors.append(f"{where}: duplicate option texts")
    else:
        if text.options is not None:
            errors.append(f"{where}: short_answer must not have options")
        if not (text.model_answer or "").strip():
            errors.append(f"{where}: short_answer needs a model_answer")
    return errors


def _validate_question(q: QuestionSeed, valid_competencies: set[str]) -> list[str]:
    errors: list[str] = []
    where = f"question {q.code!r}"

    if not SLUG_RE.match(q.code):
        errors.append(f"{where}: code must be lowercase kebab-case")
    if q.competency_slug not in valid_competencies:
        errors.append(f"{where}: unknown competency {q.competency_slug!r}")
    if not isinstance(q.type, QuestionType):
        errors.append(f"{where}: invalid type {q.type!r}")
        return errors
    if not isinstance(q.difficulty, QuestionDifficulty):
        errors.append(f"{where}: invalid difficulty {q.difficulty!r}")
    if not isinstance(q.source, QuestionSource):
        errors.append(f"{where}: invalid source {q.source!r}")
    for tag in q.tags:
        if not SLUG_RE.match(tag):
            errors.append(f"{where}: tag {tag!r} must be lowercase kebab-case")
    if len(set(q.tags)) != len(q.tags):
        errors.append(f"{where}: duplicate tags")

    if DEFAULT_LANGUAGE not in q.text:
        errors.append(f"{where}: missing the mandatory {DEFAULT_LANGUAGE.value!r} text")
        return errors
    for language in q.text:
        if not isinstance(language, Language):
            errors.append(f"{where}: invalid language key {language!r}")
            return errors

    english = q.text[DEFAULT_LANGUAGE]
    for language, text in q.text.items():
        errors.extend(_validate_text(q, language, text, f"{where} [{language.value}]"))

    if q.type in CHOICE_TYPES and english.options:
        option_ids = {o.id for o in english.options}
        correct = q.correct or ()
        if not correct:
            errors.append(f"{where}: no correct option declared")
        if len(set(correct)) != len(correct):
            errors.append(f"{where}: duplicate correct option ids")
        for option_id in correct:
            if option_id not in option_ids:
                errors.append(f"{where}: correct option {option_id!r} is not among the options")
        if q.type in SINGLE_ANSWER_TYPES and len(correct) != 1:
            errors.append(f"{where}: {q.type.value} needs exactly one correct option")
        if q.type in MULTI_ANSWER_TYPES and len(correct) < 2:
            errors.append(f"{where}: multi_select needs at least two correct options")
        if q.type in MULTI_ANSWER_TYPES and len(correct) >= len(option_ids):
            errors.append(f"{where}: multi_select needs at least one wrong option")
        # Every translation must offer exactly the same option ids, because
        # grading is language-independent.
        for language, text in q.text.items():
            if text.options and {o.id for o in text.options} != option_ids:
                errors.append(
                    f"{where} [{language.value}]: option ids differ from the English ones"
                )
    elif q.type not in CHOICE_TYPES and q.correct is not None:
        errors.append(f"{where}: short_answer must not declare correct options")

    if q.type == QuestionType.CODE_READING:
        english_blocks = FENCE_RE.findall(english.prompt)
        if not english_blocks:
            errors.append(f"{where}: code_reading needs a fenced code block in the prompt")
        for language, text in q.text.items():
            if FENCE_RE.findall(text.prompt) != english_blocks:
                errors.append(
                    f"{where} [{language.value}]: code blocks must be identical to the English ones"
                )
    return errors


def _validate_assessment(
    a: AssessmentSeed,
    qs: SubjectQuestionSet,
    questions_by_code: dict[str, QuestionSeed],
    valid_competencies: set[str],
    path_slugs: set[str],
) -> list[str]:
    errors: list[str] = []
    where = f"assessment {a.code!r}"
    if not SLUG_RE.match(a.code):
        errors.append(f"{where}: code must be lowercase kebab-case")
    if not a.title.strip():
        errors.append(f"{where}: empty title")
    if not isinstance(a.kind, AssessmentKind):
        return [*errors, f"{where}: invalid kind {a.kind!r}"]
    if not 1 <= a.pass_threshold <= 100:
        errors.append(f"{where}: pass_threshold must be 1-100")
    if a.completion_bonus_xp < 0:
        errors.append(f"{where}: completion_bonus_xp must be >= 0")
    for language, content in a.translations.items():
        if language not in {lang.value for lang in Language} or language == DEFAULT_LANGUAGE.value:
            errors.append(f"{where}: invalid translation language {language!r}")
        if not content.get("title", "").strip():
            errors.append(f"{where} [{language}]: translation needs a title")

    codes: Sequence[str]
    if a.question_codes is None:
        if a.kind != AssessmentKind.COMPETENCY:
            return [*errors, f"{where}: question_codes is required for kind {a.kind.value}"]
        codes = [q.code for q in qs.questions if q.competency_slug == a.competency_slug]
    else:
        codes = a.question_codes
    if not codes:
        errors.append(f"{where}: has no questions")
    if len(set(codes)) != len(codes):
        errors.append(f"{where}: lists the same question twice")
    for code in codes:
        if code not in questions_by_code:
            errors.append(f"{where}: unknown question {code!r}")

    if a.kind == AssessmentKind.COMPETENCY:
        if a.competency_slug not in valid_competencies:
            errors.append(f"{where}: unknown competency {a.competency_slug!r}")
        for code in codes:
            q = questions_by_code.get(code)
            if q is not None and q.competency_slug != a.competency_slug:
                errors.append(f"{where}: question {code!r} belongs to another competency")
    elif a.competency_slug is not None:
        errors.append(f"{where}: competency_slug is only for kind competency")
    if a.kind == AssessmentKind.LEARNING_PATH:
        if a.learning_path_slug not in path_slugs:
            errors.append(f"{where}: unknown learning path {a.learning_path_slug!r}")
    elif a.learning_path_slug is not None:
        errors.append(f"{where}: learning_path_slug is only for kind learning_path")
    return errors


def validate_question_sets(
    sets: Iterable[SubjectQuestionSet],
    subjects: Sequence[SubjectSeed] = SUBJECTS,
    learning_paths: Sequence[LearningPathSeed] = LEARNING_PATHS,
) -> list[str]:
    """Return every problem found (empty list = valid)."""
    sets = list(sets)
    errors: list[str] = []
    competencies_by_subject = {s.slug: {c.slug for c in s.competencies} for s in subjects}
    path_slugs = {p.slug for p in learning_paths}

    seen_questions: dict[str, QuestionSeed] = {}
    for qs in sets:
        valid = competencies_by_subject.get(qs.subject_slug)
        if valid is None:
            errors.append(f"unknown subject {qs.subject_slug!r}")
            valid = set()
        for q in qs.questions:
            if q.code in seen_questions:
                errors.append(f"question {q.code!r}: duplicate code")
                continue
            seen_questions[q.code] = q
            errors.extend(_validate_question(q, valid))

    seen_assessments: set[str] = set()
    for qs in sets:
        valid = competencies_by_subject.get(qs.subject_slug, set())
        for a in qs.assessments:
            if a.code in seen_assessments:
                errors.append(f"assessment {a.code!r}: duplicate code")
                continue
            seen_assessments.add(a.code)
            errors.extend(_validate_assessment(a, qs, seen_questions, valid, path_slugs))
    return errors


def validate_all() -> list[str]:
    return validate_question_sets(load_question_sets())


def _single_answer_choices(sets: Iterable[SubjectQuestionSet]) -> dict[str, list[QuestionSeed]]:
    by_competency: dict[str, list[QuestionSeed]] = defaultdict(list)
    for qs in sets:
        for q in qs.questions:
            text = q.text.get(DEFAULT_LANGUAGE)
            if (
                q.type in SINGLE_ANSWER_TYPES
                and text is not None
                and text.options
                and q.correct is not None
                and len(q.correct) == 1
                and q.correct[0] in {o.id for o in text.options}
            ):
                by_competency[q.competency_slug].append(q)
    return by_competency


def _correct_is_longest(q: QuestionSeed) -> bool:
    options = q.text[DEFAULT_LANGUAGE].options or []
    lengths = {o.id: len(o.text.strip()) for o in options}
    assert q.correct is not None
    own = lengths[q.correct[0]]
    return all(own > n for oid, n in lengths.items() if oid != q.correct[0])


def quality_warnings(sets: Iterable[SubjectQuestionSet]) -> list[str]:
    """Statistical bias warnings (correct answer is a length / position tell)."""
    warnings: list[str] = []
    for competency, questions in sorted(_single_answer_choices(sets).items()):
        wide = [q for q in questions if len(q.text[DEFAULT_LANGUAGE].options or []) >= 3]
        if len(wide) >= LENGTH_BIAS_MIN_QUESTIONS:
            longest = [q for q in wide if _correct_is_longest(q)]
            if len(longest) / len(wide) > LENGTH_BIAS_MAX_SHARE:
                codes = ", ".join(q.code for q in longest)
                warnings.append(
                    f"competency {competency!r}: the correct option is the longest in "
                    f"{len(longest)}/{len(wide)} questions (> {LENGTH_BIAS_MAX_SHARE:.0%}): {codes}"
                )
        if len(questions) >= POSITION_BIAS_MIN_QUESTIONS:
            letters = Counter(q.correct[0] for q in questions if q.correct)
            letter, count = letters.most_common(1)[0]
            if count / len(questions) > POSITION_BIAS_MAX_SHARE:
                warnings.append(
                    f"competency {competency!r}: correct answer is {letter!r} in "
                    f"{count}/{len(questions)} questions (> {POSITION_BIAS_MAX_SHARE:.0%}); "
                    f"distribution {dict(sorted(letters.items()))}"
                )
    return warnings


def run(sets: Sequence[SubjectQuestionSet], strict: bool = False) -> int:
    errors = validate_question_sets(sets)
    warnings = quality_warnings(sets)
    total = sum(len(s.questions) for s in sets)
    if errors:
        print(f"{len(errors)} problem(s) in the question seeds:")
        for error in errors:
            print(f"  - {error}")
    if warnings:
        print(f"{len(warnings)} quality warning(s):")
        for warning in warnings:
            print(f"  - {warning}")
    if errors:
        return 1
    if warnings and strict:
        print("FAILED (--strict): warnings are treated as errors.")
        return 1
    print(f"OK: {total} questions in {len(sets)} subject file(s) are valid.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the question-bank seeds.")
    parser.add_argument("--strict", action="store_true", help="fail on quality warnings too")
    args = parser.parse_args(argv)
    return run(load_question_sets(), strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
