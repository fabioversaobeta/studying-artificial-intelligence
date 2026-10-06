from app.domain.mastery import MasteryInputs, compute_mastery_score, practice_ratio


def _inputs(**overrides) -> MasteryInputs:
    base = {
        "total_study_minutes": 0,
        "challenges_total": 0,
        "challenges_passed": 0,
        "last_recall_quality": None,
        "questions_total": 0,
        "questions_correct": 0,
    }
    return MasteryInputs(**{**base, **overrides})


class TestPracticeWithQuizzes:
    def test_only_questions_exist_uses_coverage_alone(self):
        assert compute_mastery_score(_inputs(questions_total=4, questions_correct=2)) == 17.5
        assert compute_mastery_score(_inputs(questions_total=4, questions_correct=4)) == 35.0

    def test_only_challenges_exist_ignores_the_empty_question_bank(self):
        assert compute_mastery_score(_inputs(challenges_total=2, challenges_passed=1)) == 17.5

    def test_both_signals_are_averaged_with_equal_weight(self):
        inputs = _inputs(
            challenges_total=2, challenges_passed=2, questions_total=4, questions_correct=0
        )
        assert practice_ratio(inputs) == 0.5
        assert compute_mastery_score(inputs) == 17.5

    def test_both_signals_full_gives_full_practice(self):
        inputs = _inputs(
            challenges_total=3, challenges_passed=3, questions_total=8, questions_correct=8
        )
        assert compute_mastery_score(inputs) == 35.0

    def test_no_correct_answers_keeps_practice_at_zero(self):
        assert compute_mastery_score(_inputs(questions_total=10, questions_correct=0)) == 0.0

    def test_correct_count_is_clamped_to_the_bank_size(self):
        # e.g. questions deactivated after being answered: never above 100%.
        assert practice_ratio(_inputs(questions_total=3, questions_correct=9)) == 1.0
        assert practice_ratio(_inputs(questions_total=3, questions_correct=-1)) == 0.0

    def test_total_stays_within_100_with_all_signals(self):
        inputs = _inputs(
            total_study_minutes=10_000,
            challenges_total=1,
            challenges_passed=1,
            last_recall_quality=5,
            questions_total=5,
            questions_correct=5,
        )
        assert compute_mastery_score(inputs) == 100.0

    def test_other_signals_are_unchanged_by_the_bank(self):
        inputs = _inputs(total_study_minutes=60, last_recall_quality=5, questions_total=5)
        assert compute_mastery_score(inputs) == 20.0 + 25.0


class TestComputeMasteryScore:
    def test_no_activity_scores_zero(self):
        inputs = MasteryInputs(
            total_study_minutes=0, challenges_total=0, challenges_passed=0, last_recall_quality=None
        )
        assert compute_mastery_score(inputs) == 0.0

    def test_engagement_caps_at_120_minutes(self):
        at_cap = MasteryInputs(
            total_study_minutes=120,
            challenges_total=0,
            challenges_passed=0,
            last_recall_quality=None,
        )
        over_cap = MasteryInputs(
            total_study_minutes=600,
            challenges_total=0,
            challenges_passed=0,
            last_recall_quality=None,
        )
        assert compute_mastery_score(at_cap) == 40.0
        assert compute_mastery_score(over_cap) == 40.0

    def test_practice_score_zero_when_no_challenges_exist(self):
        inputs = MasteryInputs(
            total_study_minutes=0, challenges_total=0, challenges_passed=0, last_recall_quality=None
        )
        assert compute_mastery_score(inputs) == 0.0

    def test_practice_score_scales_with_pass_rate(self):
        half_passed = MasteryInputs(
            total_study_minutes=0, challenges_total=2, challenges_passed=1, last_recall_quality=None
        )
        all_passed = MasteryInputs(
            total_study_minutes=0, challenges_total=2, challenges_passed=2, last_recall_quality=None
        )
        assert compute_mastery_score(half_passed) == 17.5
        assert compute_mastery_score(all_passed) == 35.0

    def test_retention_score_scales_with_recall_quality(self):
        perfect_recall = MasteryInputs(
            total_study_minutes=0, challenges_total=0, challenges_passed=0, last_recall_quality=5
        )
        poor_recall = MasteryInputs(
            total_study_minutes=0, challenges_total=0, challenges_passed=0, last_recall_quality=1
        )
        assert compute_mastery_score(perfect_recall) == 25.0
        assert compute_mastery_score(poor_recall) == 5.0

    def test_full_mastery_requires_all_three_signals(self):
        inputs = MasteryInputs(
            total_study_minutes=120, challenges_total=1, challenges_passed=1, last_recall_quality=5
        )
        assert compute_mastery_score(inputs) == 100.0

    def test_score_never_exceeds_100(self):
        inputs = MasteryInputs(
            total_study_minutes=10_000,
            challenges_total=1,
            challenges_passed=1,
            last_recall_quality=5,
        )
        assert compute_mastery_score(inputs) == 100.0
