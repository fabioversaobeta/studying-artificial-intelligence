import pytest

from app.domain.spaced_repetition import DEFAULT_EASE_FACTOR, ReviewState, next_review_state


class TestNextReviewState:
    def test_first_successful_review_sets_interval_to_one_day(self):
        current = ReviewState(interval_days=1, ease_factor=DEFAULT_EASE_FACTOR, repetitions=0)
        result = next_review_state(current, quality=4)
        assert result.interval_days == 1
        assert result.repetitions == 1

    def test_second_successful_review_sets_interval_to_six_days(self):
        current = ReviewState(interval_days=1, ease_factor=DEFAULT_EASE_FACTOR, repetitions=1)
        result = next_review_state(current, quality=4)
        assert result.interval_days == 6
        assert result.repetitions == 2

    def test_third_successful_review_multiplies_by_ease_factor(self):
        current = ReviewState(interval_days=6, ease_factor=2.5, repetitions=2)
        result = next_review_state(current, quality=4)
        assert result.interval_days == round(6 * 2.5)
        assert result.repetitions == 3

    def test_failed_recall_resets_repetitions_and_interval(self):
        current = ReviewState(interval_days=30, ease_factor=2.8, repetitions=5)
        result = next_review_state(current, quality=1)
        assert result.interval_days == 1
        assert result.repetitions == 0
        # ease factor is preserved on failure, not reset
        assert result.ease_factor == 2.8

    def test_ease_factor_never_drops_below_minimum(self):
        current = ReviewState(interval_days=1, ease_factor=1.3, repetitions=2)
        result = next_review_state(current, quality=3)
        assert result.ease_factor >= 1.3

    def test_perfect_recall_increases_ease_factor_more_than_mediocre(self):
        current = ReviewState(interval_days=6, ease_factor=2.5, repetitions=2)
        perfect = next_review_state(current, quality=5)
        mediocre = next_review_state(current, quality=3)
        assert perfect.ease_factor > mediocre.ease_factor

    def test_quality_out_of_range_rejected(self):
        current = ReviewState(interval_days=1, ease_factor=DEFAULT_EASE_FACTOR, repetitions=0)
        with pytest.raises(ValueError):
            next_review_state(current, quality=6)
        with pytest.raises(ValueError):
            next_review_state(current, quality=-1)
