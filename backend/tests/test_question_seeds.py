"""The question-seed validator (the contract for bulk question generation) and
the idempotent loader in app.seeds.run."""

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assessment import (
    Assessment,
    AssessmentKind,
    AssessmentQuestion,
    Question,
    QuestionDifficulty,
    QuestionTranslation,
    QuestionType,
)
from app.models.user import Language
from app.seeds.questions.loader import load_question_sets
from app.seeds.questions.python_subject import QUESTION_SET
from app.seeds.questions.types import (
    AssessmentSeed,
    OptionSeed,
    QuestionSeed,
    QuestionText,
    SubjectQuestionSet,
)
from app.seeds.questions.validate import main as validate_main
from app.seeds.questions.validate import validate_all, validate_question_sets
from app.seeds.run import seed_questions, seed_subjects
from tests.factories import API, register

# ---------------------------------------------------------------------------
# A minimal valid question to mutate in the negative tests.
# ---------------------------------------------------------------------------


def _opts(*texts: str) -> tuple[OptionSeed, ...]:
    return tuple(OptionSeed(id=chr(ord("a") + i), text=t) for i, t in enumerate(texts))


def _valid(**overrides) -> QuestionSeed:
    base = QuestionSeed(
        code="python-type-hints-t01",
        competency_slug="type-hints",
        type=QuestionType.MULTIPLE_CHOICE,
        difficulty=QuestionDifficulty.EASY,
        correct=("b",),
        text={
            Language.EN: QuestionText(
                prompt="Pick b", options=_opts("one", "two", "three"), explanation="Because."
            ),
            Language.PT_BR: QuestionText(
                prompt="Escolha b", options=_opts("um", "dois", "tres"), explanation="Porque."
            ),
        },
        tags=("basics",),
    )
    return replace(base, **overrides)


def _errors(*questions: QuestionSeed, assessments: tuple[AssessmentSeed, ...] = ()) -> list[str]:
    return validate_question_sets(
        [SubjectQuestionSet("python", tuple(questions), assessments)],
    )


def _has(errors: list[str], fragment: str) -> bool:
    return any(fragment in e for e in errors)


class TestShippedSeeds:
    def test_the_shipped_bank_is_valid(self):
        assert validate_all() == []

    def test_cli_exits_zero_for_a_valid_bank(self, capsys: pytest.CaptureFixture[str]):
        assert validate_main() == 0
        assert "OK" in capsys.readouterr().out

    def test_pilot_covers_two_competencies_in_both_languages(self):
        questions = QUESTION_SET.questions
        assert len(questions) == 12
        assert {q.competency_slug for q in questions} == {"python-fundamentals", "type-hints"}
        assert all(set(q.text) == {Language.EN, Language.PT_BR} for q in questions)
        assert all(q.source.value == "ai_generated" for q in questions)
        assert {q.type for q in questions} >= {
            QuestionType.MULTIPLE_CHOICE,
            QuestionType.MULTI_SELECT,
            QuestionType.CODE_READING,
            QuestionType.SHORT_ANSWER,
        }

    def test_loader_discovers_the_subject_modules(self):
        assert [s.subject_slug for s in load_question_sets()] == ["python"]


class TestValidatorRejects:
    def test_a_valid_question_passes(self):
        assert _errors(_valid()) == []

    def test_duplicate_question_codes(self):
        assert _has(_errors(_valid(), _valid()), "duplicate code")

    def test_bad_code_format(self):
        assert _has(_errors(_valid(code="Bad Code")), "kebab-case")

    def test_unknown_competency(self):
        assert _has(_errors(_valid(competency_slug="nope")), "unknown competency")

    def test_missing_english(self):
        text = {Language.PT_BR: _valid().text[Language.PT_BR]}
        assert _has(_errors(_valid(text=text)), "mandatory 'en'")

    def test_portuguese_is_optional(self):
        text = {Language.EN: _valid().text[Language.EN]}
        assert _errors(_valid(text=text)) == []

    def test_correct_answer_not_among_options(self):
        assert _has(_errors(_valid(correct=("z",))), "not among the options")

    def test_no_correct_answer(self):
        assert _has(_errors(_valid(correct=())), "no correct option")

    def test_single_choice_with_two_correct(self):
        assert _has(_errors(_valid(correct=("a", "b"))), "exactly one correct")

    def test_multi_select_needs_two_correct_and_one_wrong(self):
        base = {"type": QuestionType.MULTI_SELECT}
        assert _has(_errors(_valid(correct=("a",), **base)), "at least two correct")
        assert _has(_errors(_valid(correct=("a", "b", "c"), **base)), "at least one wrong")
        assert _errors(_valid(correct=("a", "b"), **base)) == []

    def test_duplicate_option_texts_and_ids(self):
        dup_text = QuestionText(prompt="p", options=_opts("same", " SAME ", "x"), explanation="e")
        assert _has(_errors(_valid(text={Language.EN: dup_text})), "duplicate option texts")
        dup_id = QuestionText(
            prompt="p",
            options=(OptionSeed("a", "x"), OptionSeed("a", "y")),
            explanation="e",
        )
        assert _has(_errors(_valid(text={Language.EN: dup_id})), "duplicate option ids")

    def test_too_few_options(self):
        one = QuestionText(prompt="p", options=_opts("only"), explanation="e")
        assert _has(_errors(_valid(text={Language.EN: one}, correct=("a",))), "needs 2-8 options")

    def test_translation_with_different_option_ids(self):
        other = QuestionText(
            prompt="p",
            options=(OptionSeed("x", "1"), OptionSeed("y", "2"), OptionSeed("z", "3")),
            explanation="e",
        )
        text = {Language.EN: _valid().text[Language.EN], Language.PT_BR: other}
        assert _has(_errors(_valid(text=text)), "option ids differ")

    def test_empty_prompt_or_explanation(self):
        blank = QuestionText(prompt=" ", options=_opts("a", "b"), explanation="")
        errors = _errors(_valid(text={Language.EN: blank}, correct=("a",)))
        assert _has(errors, "empty prompt") and _has(errors, "empty explanation")

    def test_invalid_difficulty_and_type(self):
        assert _has(_errors(_valid(difficulty="trivial")), "invalid difficulty")
        assert _has(_errors(_valid(type="essay")), "invalid type")

    def test_bad_tags(self):
        assert _has(_errors(_valid(tags=("Not Kebab",))), "kebab-case")
        assert _has(_errors(_valid(tags=("a", "a"))), "duplicate tags")

    def test_short_answer_rules(self):
        ok = QuestionText(prompt="p", explanation="e", model_answer="m")
        base = {"type": QuestionType.SHORT_ANSWER, "correct": None}
        assert _errors(_valid(text={Language.EN: ok}, **base)) == []
        no_model = QuestionText(prompt="p", explanation="e")
        assert _has(_errors(_valid(text={Language.EN: no_model}, **base)), "needs a model_answer")
        with_options = QuestionText(
            prompt="p", explanation="e", model_answer="m", options=_opts("a", "b")
        )
        assert _has(_errors(_valid(text={Language.EN: with_options}, **base)), "must not have")
        assert _has(
            _errors(_valid(text={Language.EN: ok}, type=QuestionType.SHORT_ANSWER)),
            "must not declare correct",
        )

    def test_choice_question_must_not_carry_a_model_answer(self):
        text = QuestionText(prompt="p", options=_opts("a", "b"), explanation="e", model_answer="m")
        assert _has(_errors(_valid(text={Language.EN: text}, correct=("a",))), "only for short")

    def test_code_reading_needs_identical_code_blocks_in_every_language(self):
        code = "```python\nprint(1)\n```"
        en = QuestionText(prompt=f"What?\n{code}", options=_opts("a", "b"), explanation="e")
        no_code = QuestionText(prompt="What?", options=_opts("a", "b"), explanation="e")
        assert _has(
            _errors(
                _valid(type=QuestionType.CODE_READING, text={Language.EN: no_code}, correct=("a",))
            ),
            "fenced code block",
        )
        changed = QuestionText(
            prompt="O que?\n```python\nprint(2)\n```", options=_opts("a", "b"), explanation="e"
        )
        text = {Language.EN: en, Language.PT_BR: changed}
        assert _has(
            _errors(_valid(type=QuestionType.CODE_READING, text=text, correct=("a",))),
            "must be identical",
        )

    def test_unknown_subject(self):
        errors = validate_question_sets([SubjectQuestionSet("nonexistent", (_valid(),))])
        assert _has(errors, "unknown subject")


class TestAssessmentValidation:
    def _assessment(self, **overrides) -> AssessmentSeed:
        base = AssessmentSeed(
            code="a-quiz",
            title="Quiz",
            kind=AssessmentKind.COMPETENCY,
            competency_slug="type-hints",
        )
        return replace(base, **overrides)

    def test_valid_competency_assessment_collects_the_competency_questions(self):
        assert _errors(_valid(), assessments=(self._assessment(),)) == []

    def test_competency_assessment_without_questions(self):
        errors = _errors(
            _valid(), assessments=(self._assessment(competency_slug="python-fundamentals"),)
        )
        assert _has(errors, "has no questions")

    def test_threshold_and_bonus_ranges(self):
        errors = _errors(
            _valid(),
            assessments=(self._assessment(pass_threshold=0, completion_bonus_xp=-1),),
        )
        assert _has(errors, "pass_threshold") and _has(errors, "completion_bonus_xp")
        assert _has(
            _errors(_valid(), assessments=(self._assessment(pass_threshold=101),)), "pass_threshold"
        )

    def test_unknown_and_duplicate_question_codes(self):
        mixed = self._assessment(
            kind=AssessmentKind.MIXED,
            competency_slug=None,
            question_codes=("python-type-hints-t01", "python-type-hints-t01", "ghost"),
        )
        errors = _errors(_valid(), assessments=(mixed,))
        assert _has(errors, "unknown question 'ghost'") and _has(errors, "same question twice")

    def test_mixed_needs_explicit_codes(self):
        mixed = self._assessment(kind=AssessmentKind.MIXED, competency_slug=None)
        assert _has(_errors(_valid(), assessments=(mixed,)), "question_codes is required")

    def test_learning_path_needs_a_known_path(self):
        path = self._assessment(
            kind=AssessmentKind.LEARNING_PATH,
            competency_slug=None,
            learning_path_slug="ghost-path",
            question_codes=("python-type-hints-t01",),
        )
        assert _has(_errors(_valid(), assessments=(path,)), "unknown learning path")
        real = replace(path, learning_path_slug="senior-interview-readiness")
        assert _errors(_valid(), assessments=(real,)) == []

    def test_competency_assessment_cannot_borrow_other_competency_questions(self):
        other = _valid(code="python-fundamentals-t01", competency_slug="python-fundamentals")
        quiz = self._assessment(question_codes=("python-fundamentals-t01",))
        assert _has(_errors(_valid(), other, assessments=(quiz,)), "belongs to another competency")

    def test_duplicate_assessment_codes_and_bad_translation(self):
        errors = _errors(_valid(), assessments=(self._assessment(), self._assessment()))
        assert _has(errors, "duplicate code")
        bad = self._assessment(translations={"fr": {"title": "x"}, "pt-BR": {"title": " "}})
        errors = _errors(_valid(), assessments=(bad,))
        assert _has(errors, "invalid translation language") and _has(errors, "needs a title")


class TestSeedLoader:
    def test_seeding_is_idempotent(self, db: Session):
        competencies = seed_subjects(db)
        assert seed_questions(db, competencies) == 12
        counts = (
            db.query(Question).count(),
            db.query(QuestionTranslation).count(),
            db.query(Assessment).count(),
            db.query(AssessmentQuestion).count(),
        )
        assert seed_questions(db, competencies) == 12
        assert counts == (
            db.query(Question).count(),
            db.query(QuestionTranslation).count(),
            db.query(Assessment).count(),
            db.query(AssessmentQuestion).count(),
        )
        assert counts == (12, 24, 3, 6 + 6 + 5)

    def test_seeded_rows_follow_the_data(self, db: Session):
        seed_questions(db, seed_subjects(db))
        question = db.query(Question).filter(Question.code == "python-fundamentals-q05").one()
        assert question.difficulty == QuestionDifficulty.HARD
        assert question.xp_value == 30
        assert question.correct_option_ids == ["c"]
        assert question.competency.slug == "python-fundamentals"
        assert {t.language for t in question.translations} == {Language.EN, Language.PT_BR}

        short = db.query(Question).filter(Question.code == "python-fundamentals-q06").one()
        assert short.correct_option_ids is None
        english = next(t for t in short.translations if t.language == Language.EN)
        assert english.options is None and english.model_answer

        mixed = db.query(Assessment).filter(Assessment.code == "python-core-checkpoint").one()
        assert mixed.kind == AssessmentKind.MIXED and mixed.competency_id is None
        assert (mixed.pass_threshold, mixed.completion_bonus_xp) == (80, 40)
        assert [m.question.code for m in mixed.questions][0] == "python-fundamentals-q01"

    def test_reseeding_picks_up_edited_text(self, db: Session, monkeypatch: pytest.MonkeyPatch):
        competencies = seed_subjects(db)
        seed_questions(db, competencies)
        first = QUESTION_SET.questions[0]
        edited_text = dict(first.text)
        edited_text[Language.EN] = replace(first.text[Language.EN], explanation="REWRITTEN")
        edited = SubjectQuestionSet(
            "python",
            (replace(first, text=edited_text), *QUESTION_SET.questions[1:]),
            QUESTION_SET.assessments,
        )
        monkeypatch.setattr("app.seeds.run.load_question_sets", lambda: [edited])
        seed_questions(db, competencies)
        db.expire_all()
        translation = (
            db.query(QuestionTranslation)
            .join(Question)
            .filter(Question.code == first.code, QuestionTranslation.language == Language.EN)
            .one()
        )
        assert translation.explanation == "REWRITTEN"

    def test_an_invalid_bank_is_refused_before_touching_the_database(
        self, db: Session, monkeypatch: pytest.MonkeyPatch
    ):
        competencies = seed_subjects(db)
        broken = SubjectQuestionSet("python", (_valid(correct=("z",)),))
        monkeypatch.setattr("app.seeds.run.load_question_sets", lambda: [broken])
        with pytest.raises(ValueError, match="not among the options"):
            seed_questions(db, competencies)
        assert db.query(Question).count() == 0

    def test_seeded_quiz_can_be_played_end_to_end(self, client: TestClient, db: Session):
        seed_questions(db, seed_subjects(db))
        db.commit()
        headers, _ = register(client, "seeded@example.com")
        client.patch(f"{API}/users/me", headers=headers, json={"preferred_language": "pt-BR"})

        quizzes = client.get(f"{API}/assessments", headers=headers).json()
        quiz = next(q for q in quizzes if q["code"] == "python-type-hints-quiz")
        assert quiz["title"] == "Quiz de Type Hints"
        assert quiz["question_count"] == 6

        attempt = client.post(f"{API}/assessments/{quiz['id']}/attempts", headers=headers).json()
        assert all(q["language"] == "pt-BR" for q in attempt["questions"])
        by_id = {
            str(q.id): q
            for q in db.query(Question).filter(Question.code.like("python-type-hints-q%"))
        }
        for item in attempt["questions"]:
            question = by_id[item["id"]]
            if question.type == QuestionType.SHORT_ANSWER:
                client.put(
                    f"{API}/attempts/{attempt['id']}/responses/{item['id']}",
                    headers=headers,
                    json={"text": "my answer"},
                )
                client.post(
                    f"{API}/attempts/{attempt['id']}/responses/{item['id']}/self-grade",
                    headers=headers,
                    json={"is_correct": True},
                )
            else:
                client.put(
                    f"{API}/attempts/{attempt['id']}/responses/{item['id']}",
                    headers=headers,
                    json={"option_ids": question.correct_option_ids},
                )
        result = client.post(f"{API}/attempts/{attempt['id']}/finish", headers=headers).json()
        assert result["score_percent"] == 100.0 and result["passed"] is True
        # easy 10 + easy 10 + medium 20 + medium 20 + hard 30 + hard 30, plus the 25 bonus.
        assert result["xp_questions"] == 120
        assert result["xp_awarded"] == 145
