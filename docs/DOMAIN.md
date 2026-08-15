# Domain Model

## Entity overview

```
User ──< LearningGoal
  │
  ├──< StudySession >── Competency ──> Subject
  │                          │
  │                          ├──< LearningResource
  │                          ├──< Challenge ──< ChallengeSubmission
  │                          ├──< CompetencyPrerequisite (self-referential)
  │                          └── (member of) LearningPathItem ──> LearningPath
  │
  ├──< Mastery (per Competency)
  ├──< Review (per Competency, spaced repetition)
  │
  ├── GamificationProfile (1:1 — total_xp, level, streaks)
  ├──< XPAward (append-only ledger)
  ├──< UserAchievement >── Achievement
  └──< QuestCompletion >── Quest
```

Full table definitions live in the ORM (`backend/app/models/`) and the
Alembic migration history — this document explains *why* the shape is what
it is, not a field-by-field schema dump.

## Learning catalog (seeded content, not user-editable in v1)

**Subject** → **Competency** → (**LearningResource**, **Challenge**).
Competencies can require other competencies within the same subject
(`CompetencyPrerequisite`), forming the skill tree. **LearningPath** groups
an ordered set of competencies (possibly across subjects) into a curated
sequence.

This content is authored in `backend/app/seeds/content.py` as plain
dataclasses and upserted into the database by `backend/app/seeds/run.py`
(idempotent — safe to re-run). Application code never hardcodes a subject
or competency name; everything is read back as rows.

## Skill-tree state (computed, not stored)

A competency's state for a given user — `locked`, `available`, `learning`,
`mastered` — is derived on every read (`app.domain.skill_tree`), not stored
as a column:

- **mastered**: mastery score ≥ 80
- **learning**: score < 80 but the user has logged activity (study time > 0)
- **available**: no activity yet, but every prerequisite is mastered (or
  there are no prerequisites)
- **locked**: otherwise

Storing this as a column would require remembering to update it everywhere
mastery or activity changes; deriving it from `Mastery` + `StudySession`
rows (which already exist and are the source of truth) makes drift
impossible by construction.

## Mastery vs. XP — the most important distinction in this codebase

**XP measures activity. Mastery measures knowledge.** They are computed
independently, by different services, and must never be conflated — see
`docs/DECISIONS.md` for why this distinction exists and what breaks if it's
lost.

### Mastery formula (`app.domain.mastery`)

A transparent, deterministic score from 0-100, combining three signals so
that none of them alone can claim mastery:

| Signal | Max points | What it measures |
|---|---|---|
| Engagement | 40 | Time invested (caps at 120 minutes — grinding time alone can't carry the score past this) |
| Practice | 35 | Share of that competency's challenges passed (0 until at least one is attempted) |
| Retention | 25 | Most recent spaced-repetition recall quality (0 until the first review) |

```
score = min(40, minutes/120 * 40)
      + (35 * challenges_passed/challenges_total   if any challenges exist else 0)
      + (25 * last_recall_quality/5                if reviewed at least once else 0)
```

Recomputed after every event that could move it: a study session, a
challenge submission, a review recall (`app.services.mastery_service`).

### XP and leveling (`app.domain.leveling`)

XP is an append-only ledger (`XPAward`) with a source
(`study_session` | `challenge` | `review` | `achievement` | `quest` | ...),
summed into a cached `GamificationProfile.total_xp`. Level uses a
triangular growth curve so leveling up stays achievable early and grows
harder later, without needing an exponential curve:

```
total_xp_required_for_level(N) = 100 * N * (N-1) / 2
  L1 -> 0    L2 -> 100   L3 -> 300   L4 -> 600   L5 -> 1000 ...
```

### Streaks

`GamificationProfile.current_streak_days` increments when activity is
logged on the day after the last logged activity day, resets to 1 on a gap,
and is untouched if activity was already logged today. XP-awarding events
that shouldn't count as "showing up" for streak purposes (e.g. quest/
achievement bonus XP) pass `counts_for_streak=False`.

### Spaced repetition (`app.domain.spaced_repetition`)

A simplified SM-2 (the algorithm behind Anki/SuperMemo): a competency
enters the review queue the first time it's studied, due the next day.
Each recall submission (quality 0-5) either resets the interval (quality <
3, "forgot") or grows it (interval × ease factor, ease factor adjusted by
how easy the recall felt). Isolated in `app.domain.spaced_repetition` with
no persistence dependency, so the algorithm can be swapped later (see
`docs/PENDING.md`) without touching `Review` persistence code.

## Gamification

- **Achievements** (`Achievement` + `UserAchievement`): one-time unlocks
  evaluated against a criterion type (`first_study_session`,
  `streak_days`, `competency_mastered_count`, `challenges_passed_count`,
  `xp_milestone`) and a threshold value. Checked after every XP award
  (`app.services.gamification_service.check_and_award_achievements`).
- **Quests** (`Quest` + `QuestCompletion`): one-time or weekly goals
  (`study_sessions_count`, `challenges_passed_count`,
  `reviews_completed_count`, `xp_earned`). Progress is computed fresh from
  activity data on every read and auto-completed (XP awarded) the moment
  the target is crossed — see `app.services.quest_service` for why this
  avoids a separate "claim" endpoint.
