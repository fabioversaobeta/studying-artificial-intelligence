"""gamification_service: XP, levels, streaks, achievements (service level)."""

import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.gamification import AchievementCriterion, UserAchievement, XPAward, XPSource
from app.repositories import gamification_repository
from app.services import gamification_service
from tests.factories import API, freeze_time, make_achievement, register, utc


@pytest.fixture
def user_id(client: TestClient) -> uuid.UUID:
    return register(client, "gamer@example.com")[1]


def _award(db: Session, user_id: uuid.UUID, amount: int = 10, **kwargs):
    profile = gamification_service.award_xp(
        db, user_id=user_id, amount=amount, source=XPSource.STUDY_SESSION, **kwargs
    )
    db.commit()
    return profile


class TestXpAndLevels:
    def test_rejects_non_positive_amount(self, db: Session, user_id: uuid.UUID):
        with pytest.raises(ValueError):
            gamification_service.award_xp(db, user_id=user_id, amount=0, source=XPSource.QUEST)

    def test_accumulates_xp_and_records_ledger_entries(self, db: Session, user_id: uuid.UUID):
        _award(db, user_id, 40)
        profile = _award(db, user_id, 25)
        assert profile.total_xp == 65
        amounts = db.execute(select(XPAward.amount).where(XPAward.user_id == user_id)).scalars()
        assert sorted(amounts) == [25, 40]

    def test_levels_up_at_thresholds(self, db: Session, user_id: uuid.UUID):
        assert _award(db, user_id, 99).level == 1
        assert _award(db, user_id, 1).level == 2  # 100 XP
        assert _award(db, user_id, 199).level == 2  # 299 XP
        assert _award(db, user_id, 1).level == 3  # 300 XP

    def test_big_award_can_skip_levels(self, db: Session, user_id: uuid.UUID):
        assert _award(db, user_id, 1000).level == 5

    def test_profile_endpoint_reflects_level(self, client: TestClient, db: Session):
        headers, uid = register(client, "lvl@example.com")
        _award(db, uid, 350)
        profile = client.get(f"{API}/gamification/profile", headers=headers).json()
        assert profile["total_xp"] == 350
        assert profile["level"] == 3


class TestStreak:
    def test_first_activity_starts_streak_at_one(
        self, db: Session, user_id: uuid.UUID, monkeypatch: pytest.MonkeyPatch
    ):
        freeze_time(monkeypatch, gamification_service, utc(2026, 3, 1))
        profile = _award(db, user_id)
        assert profile.current_streak_days == 1
        assert profile.longest_streak_days == 1

    def test_same_day_does_not_duplicate_streak(
        self, db: Session, user_id: uuid.UUID, monkeypatch: pytest.MonkeyPatch
    ):
        clock = freeze_time(monkeypatch, gamification_service, utc(2026, 3, 1, 8))
        _award(db, user_id)
        clock.current = utc(2026, 3, 1, 23)
        profile = _award(db, user_id)
        assert profile.current_streak_days == 1
        assert profile.total_xp == 20

    def test_consecutive_days_extend_streak(
        self, db: Session, user_id: uuid.UUID, monkeypatch: pytest.MonkeyPatch
    ):
        clock = freeze_time(monkeypatch, gamification_service, utc(2026, 3, 1))
        _award(db, user_id)
        for expected in (2, 3, 4):
            clock.current += timedelta(days=1)
            assert _award(db, user_id).current_streak_days == expected

    def test_streak_crosses_month_boundary(
        self, db: Session, user_id: uuid.UUID, monkeypatch: pytest.MonkeyPatch
    ):
        clock = freeze_time(monkeypatch, gamification_service, utc(2026, 2, 28))
        _award(db, user_id)
        clock.current = utc(2026, 3, 1)
        assert _award(db, user_id).current_streak_days == 2

    def test_gap_resets_current_but_keeps_longest(
        self, db: Session, user_id: uuid.UUID, monkeypatch: pytest.MonkeyPatch
    ):
        clock = freeze_time(monkeypatch, gamification_service, utc(2026, 3, 1))
        _award(db, user_id)
        clock.current = utc(2026, 3, 2)
        _award(db, user_id)
        clock.current = utc(2026, 3, 5)  # skipped two days
        profile = _award(db, user_id)
        assert profile.current_streak_days == 1
        assert profile.longest_streak_days == 2

    def test_non_streak_awards_leave_streak_untouched(
        self, db: Session, user_id: uuid.UUID, monkeypatch: pytest.MonkeyPatch
    ):
        clock = freeze_time(monkeypatch, gamification_service, utc(2026, 3, 1))
        _award(db, user_id)
        clock.current = utc(2026, 3, 2)
        profile = _award(db, user_id, counts_for_streak=False)
        assert profile.current_streak_days == 1
        assert profile.total_xp == 20


class TestAchievements:
    def test_xp_milestone_unlocks_once(self, db: Session, user_id: uuid.UUID):
        make_achievement(db, "xp_50", AchievementCriterion.XP_MILESTONE, 50)
        _award(db, user_id, 49)
        assert gamification_repository.get_earned_achievement_codes(db, user_id) == set()
        _award(db, user_id, 1)
        assert gamification_repository.get_earned_achievement_codes(db, user_id) == {"xp_50"}
        # A later check does not re-award it.
        assert gamification_service.check_and_award_achievements(db, user_id) == []

    def test_reward_xp_is_granted_and_marked_as_achievement_source(
        self, db: Session, user_id: uuid.UUID
    ):
        make_achievement(db, "xp_10", AchievementCriterion.XP_MILESTONE, 10, xp_reward=25)
        profile = _award(db, user_id, 10)
        assert profile.total_xp == 35
        sources = db.execute(select(XPAward.source).where(XPAward.user_id == user_id)).scalars()
        assert XPSource.ACHIEVEMENT in set(sources)

    def test_reward_xp_does_not_touch_streak(
        self, db: Session, user_id: uuid.UUID, monkeypatch: pytest.MonkeyPatch
    ):
        freeze_time(monkeypatch, gamification_service, utc(2026, 3, 1))
        make_achievement(db, "xp_10", AchievementCriterion.XP_MILESTONE, 10, xp_reward=25)
        assert _award(db, user_id, 10).current_streak_days == 1

    def test_streak_achievement_unlocks_on_third_day(
        self, db: Session, user_id: uuid.UUID, monkeypatch: pytest.MonkeyPatch
    ):
        clock = freeze_time(monkeypatch, gamification_service, utc(2026, 3, 1))
        make_achievement(db, "streak_3", AchievementCriterion.STREAK_DAYS, 3)
        for _ in range(2):
            _award(db, user_id)
            clock.current += timedelta(days=1)
        assert gamification_repository.get_earned_achievement_codes(db, user_id) == set()
        _award(db, user_id)
        assert gamification_repository.get_earned_achievement_codes(db, user_id) == {"streak_3"}

    def test_listing_marks_earned_and_locked(self, client: TestClient, db: Session):
        headers, uid = register(client, "ach@example.com")
        make_achievement(db, "low", AchievementCriterion.XP_MILESTONE, 10)
        make_achievement(db, "high", AchievementCriterion.XP_MILESTONE, 10_000)
        _award(db, uid, 20)
        items = client.get(f"{API}/gamification/achievements", headers=headers).json()
        by_code = {i["achievement"]["code"]: i for i in items}
        assert by_code["low"]["earned"] is True
        assert by_code["low"]["earned_at"] is not None
        assert by_code["high"]["earned"] is False

    def test_two_achievements_unlock_in_the_same_pass(self, db: Session, user_id: uuid.UUID):
        # The first one pays an XP reward; awarding it re-enters the achievement
        # check, which must not cause the second one to be awarded twice.
        make_achievement(db, "a_first", AchievementCriterion.XP_MILESTONE, 10, xp_reward=5)
        make_achievement(db, "b_second", AchievementCriterion.XP_MILESTONE, 10, xp_reward=0)
        _award(db, user_id, 10)
        rows = db.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        ).scalars()
        assert len(list(rows)) == 2

    def test_chain_of_three_achievements_unlocks_in_one_pass(self, db: Session, user_id: uuid.UUID):
        make_achievement(db, "a", AchievementCriterion.XP_MILESTONE, 10, xp_reward=5)
        make_achievement(db, "b", AchievementCriterion.XP_MILESTONE, 10, xp_reward=5)
        make_achievement(db, "c", AchievementCriterion.XP_MILESTONE, 10, xp_reward=5)
        profile = _award(db, user_id, 10)
        assert gamification_repository.get_earned_achievement_codes(db, user_id) == {"a", "b", "c"}
        assert profile.total_xp == 25

    def test_reward_xp_can_trigger_another_achievement(self, db: Session, user_id: uuid.UUID):
        make_achievement(db, "first", AchievementCriterion.XP_MILESTONE, 10, xp_reward=20)
        make_achievement(db, "second", AchievementCriterion.XP_MILESTONE, 30, xp_reward=0)
        profile = _award(db, user_id, 10)  # 10 -> first (+20) -> 30 -> second
        assert gamification_repository.get_earned_achievement_codes(db, user_id) == {
            "first",
            "second",
        }
        assert profile.total_xp == 30

    def test_settle_rewards_is_idempotent(self, db: Session, user_id: uuid.UUID):
        make_achievement(db, "a", AchievementCriterion.XP_MILESTONE, 10, xp_reward=5)
        profile = _award(db, user_id, 10)
        assert gamification_service.settle_rewards(db, user_id) == []
        db.commit()
        db.refresh(profile)
        assert profile.total_xp == 15

    def test_list_achievements_is_ordered_by_code(self, db: Session):
        for code in ("zeta", "alpha", "mid"):
            make_achievement(db, code, AchievementCriterion.XP_MILESTONE, 10)
        codes = [a.code for a in gamification_repository.list_achievements(db)]
        assert codes == sorted(codes)
