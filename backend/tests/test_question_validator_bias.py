"""Quality-bias warnings of the question validator (J8): the correct option
being the longest one, and a lopsided distribution of the correct letter."""

from dataclasses import replace

import pytest

from app.models.assessment import QuestionDifficulty, QuestionType
from app.models.user import Language
from app.seeds.questions import validate
from app.seeds.questions.loader import load_question_sets
from app.seeds.questions.types import OptionSeed, QuestionSeed, QuestionText, SubjectQuestionSet

SHORT, LONG = "short", "a much longer option text that gives the answer away"


def _q(i: int, correct: str, longest: str | None) -> QuestionSeed:
    """Three options; ``longest`` is the id of the longest one (None = all equal)."""
    options = tuple(
        OptionSeed(id=oid, text=(LONG if oid == longest else f"{SHORT} {oid}"))
        for oid in ("a", "b", "c")
    )
    return QuestionSeed(
        code=f"python-type-hints-b{i:02d}",
        competency_slug="type-hints",
        type=QuestionType.MULTIPLE_CHOICE,
        difficulty=QuestionDifficulty.EASY,
        correct=(correct,),
        text={Language.EN: QuestionText(prompt="p", explanation="e", options=options)},
    )


def _sets(*questions: QuestionSeed) -> list[SubjectQuestionSet]:
    return [SubjectQuestionSet("python", tuple(questions), ())]


def _biased_length(n: int = 6) -> list[QuestionSeed]:
    return [_q(i, "abc"[i % 3], "abc"[i % 3]) for i in range(n)]


def test_balanced_questions_raise_no_warning():
    # Letters rotate a/b/c; the longest option rotates independently of the answer.
    sets = _sets(*[_q(i, "abc"[i % 3], "abc"[(i + 1) % 3]) for i in range(9)])
    assert validate.validate_question_sets(sets) == []
    assert validate.quality_warnings(sets) == []


def test_length_bias_warns_and_lists_the_questions():
    warnings = validate.quality_warnings(_sets(*_biased_length()))
    assert len(warnings) == 1
    assert "longest in 6/6" in warnings[0]
    assert "python-type-hints-b00" in warnings[0]


def test_length_bias_needs_a_minimum_number_of_questions():
    assert validate.quality_warnings(_sets(*_biased_length(3))) == []


def test_position_bias_warns():
    # 8 questions, 'b' correct in 5 (62%); the longest option is never the answer.
    questions = [_q(i, "b" if i < 5 else "ac"[i % 2], "c" if i < 5 else "b") for i in range(8)]
    warnings = validate.quality_warnings(_sets(*questions))
    assert len(warnings) == 1
    assert "'b' in 5/8" in warnings[0]


def test_position_bias_ignored_below_the_minimum():
    questions = [_q(i, "b", "c") for i in range(validate.POSITION_BIAS_MIN_QUESTIONS - 1)]
    assert validate.quality_warnings(_sets(*questions)) == []


def test_multi_select_and_short_answer_are_ignored():
    base = _q(0, "a", "a")
    multi = replace(base, type=QuestionType.MULTI_SELECT, correct=("a", "b"))
    short = replace(base, type=QuestionType.SHORT_ANSWER, correct=None)
    assert validate.quality_warnings(_sets(*[multi] * 8, *[short] * 8)) == []


def test_warnings_do_not_fail_by_default_but_strict_does(capsys: pytest.CaptureFixture[str]):
    sets = _sets(*_biased_length())
    assert validate.run(sets) == 0
    assert "quality warning" in capsys.readouterr().out
    assert validate.run(sets, strict=True) == 1
    assert "--strict" in capsys.readouterr().out


def test_errors_still_fail_without_strict(capsys: pytest.CaptureFixture[str]):
    bad = _q(0, "z", None)  # correct option id does not exist
    assert validate.run(_sets(bad)) == 1
    assert "problem(s)" in capsys.readouterr().out


def test_strict_flag_is_parsed_by_main(monkeypatch: pytest.MonkeyPatch):
    seen: list[bool] = []

    def fake_run(sets: object, strict: bool = False) -> int:
        seen.append(strict)
        return 0

    monkeypatch.setattr(validate, "run", fake_run)
    validate.main(["--strict"])
    validate.main([])
    assert seen == [True, False]


def test_shipped_banks_validate_without_strict():
    assert validate.main() == 0
    assert validate.validate_question_sets(load_question_sets()) == []
