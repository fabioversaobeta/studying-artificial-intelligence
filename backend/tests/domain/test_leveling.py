import pytest

from app.domain.leveling import compute_level, total_xp_required_for_level, xp_to_next_level


class TestTotalXpRequiredForLevel:
    def test_level_one_requires_zero_xp(self):
        assert total_xp_required_for_level(1) == 0

    def test_thresholds_match_documented_curve(self):
        assert total_xp_required_for_level(2) == 100
        assert total_xp_required_for_level(3) == 300
        assert total_xp_required_for_level(4) == 600
        assert total_xp_required_for_level(5) == 1000


class TestComputeLevel:
    @pytest.mark.parametrize(
        ("total_xp", "expected_level"),
        [
            (0, 1),
            (99, 1),
            (100, 2),
            (299, 2),
            (300, 3),
            (999, 4),
            (1000, 5),
        ],
    )
    def test_boundaries(self, total_xp: int, expected_level: int):
        assert compute_level(total_xp) == expected_level

    def test_negative_xp_rejected(self):
        with pytest.raises(ValueError):
            compute_level(-1)


class TestXpToNextLevel:
    def test_zero_xp_needs_full_first_threshold(self):
        assert xp_to_next_level(0) == 100

    def test_exact_threshold_needs_full_next_step(self):
        assert xp_to_next_level(100) == 200  # level 2 -> level 3 costs 300-100

    def test_partway_through_a_level(self):
        assert xp_to_next_level(150) == 150
