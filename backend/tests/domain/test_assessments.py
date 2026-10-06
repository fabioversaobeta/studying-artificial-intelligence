import pytest

from app.domain.assessments import (
    XP_BY_DIFFICULTY,
    compute_attempt_xp,
    grade_choice,
    is_passing,
    score_percent,
    xp_for_difficulty,
)


def test_xp_table_is_monotonic_in_difficulty():
    assert xp_for_difficulty("easy") < xp_for_difficulty("medium") < xp_for_difficulty("hard")
    assert set(XP_BY_DIFFICULTY) == {"easy", "medium", "hard"}


class TestGradeChoice:
    def test_single_correct(self):
        assert grade_choice(["b"], ["b"]) is True
        assert grade_choice(["b"], ["a"]) is False

    def test_multi_select_is_all_or_nothing(self):
        assert grade_choice(["a", "c"], ["c", "a"]) is True
        assert grade_choice(["a", "c"], ["a"]) is False
        assert grade_choice(["a", "c"], ["a", "c", "d"]) is False

    def test_duplicates_in_the_selection_do_not_matter(self):
        assert grade_choice(["a"], ["a", "a"]) is True

    def test_empty_selection_is_wrong(self):
        assert grade_choice(["a"], []) is False


class TestScoring:
    def test_score_percent(self):
        assert score_percent(7, 10) == 70.0
        assert score_percent(1, 3) == 33.33
        assert score_percent(0, 0) == 0.0

    @pytest.mark.parametrize(
        ("correct", "total", "threshold", "expected"),
        [
            (7, 10, 70, True),  # exactly on the threshold passes
            (6, 10, 70, False),
            (2, 3, 66, True),  # 66.67% >= 66%
            (2, 3, 67, False),  # 66.67% < 67% (float rounding must not flip it)
            (0, 0, 70, False),
            (1, 1, 100, True),
        ],
    )
    def test_is_passing(self, correct, total, threshold, expected):
        assert is_passing(correct, total, threshold) is expected


class TestAttemptXp:
    def test_failed_attempt_pays_nothing(self):
        xp = compute_attempt_xp(
            passed=False,
            unpaid_correct_xp_values=[10, 20],
            is_first_pass=True,
            completion_bonus_xp=25,
        )
        assert xp.total == 0

    def test_first_pass_pays_questions_plus_bonus(self):
        xp = compute_attempt_xp(
            passed=True,
            unpaid_correct_xp_values=[10, 20],
            is_first_pass=True,
            completion_bonus_xp=25,
        )
        assert (xp.questions_xp, xp.completion_bonus_xp, xp.total) == (30, 25, 55)

    def test_repeat_pass_without_new_questions_pays_nothing(self):
        xp = compute_attempt_xp(
            passed=True, unpaid_correct_xp_values=[], is_first_pass=False, completion_bonus_xp=25
        )
        assert xp.total == 0

    def test_repeat_pass_pays_only_newly_unpaid_questions(self):
        xp = compute_attempt_xp(
            passed=True, unpaid_correct_xp_values=[30], is_first_pass=False, completion_bonus_xp=25
        )
        assert (xp.questions_xp, xp.completion_bonus_xp) == (30, 0)
