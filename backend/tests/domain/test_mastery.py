from app.domain.mastery import MasteryInputs, compute_mastery_score


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
