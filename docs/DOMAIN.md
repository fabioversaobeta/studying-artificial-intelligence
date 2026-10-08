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
  ├──< AssessmentAttempt >── Assessment ──< Question ──< QuestionTranslation
  │         └──< QuestionResponse >── Question (Question belongs to a Competency)
  ├──< AssessmentAttempt >── Assessment ──< Question ──< QuestionTranslation
  │         └──< QuestionResponse >── Question (Question belongs to a Competency)
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

`LearningResource` covers two distinct shapes sharing one table: external
references (`url` set — articles, docs, videos) and in-platform lessons
(`type == LESSON`, `content` holds a full markdown body). Lesson content
is authored as ordered modules per competency in `backend/app/seeds/
lessons/` (one Python file per subject) — module count scales with the
topic's real complexity rather than being fixed, e.g. SOLID gets 6 modules
(one per principle plus synthesis), narrower topics get 1-2. See
docs/DECISIONS.md for why this is split out from `content.py` and a
raw-string gotcha worth knowing before editing lesson bodies.

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
| Practice | 35 | Weighted mean of the challenge pass share and the quiz coverage (0 until at least one is attempted) — see below |
| Retention | 25 | Most recent spaced-repetition recall quality (0 until the first review) |

```
challenge_share = challenges_passed / challenges_total      (only if challenges exist)
quiz_coverage   = questions_correct / questions_total       (only if active questions exist)
practice_ratio  = (0.5*challenge_share + 0.5*quiz_coverage) / (sum of the weights present)
                  (0 if neither exists)

score = min(40, minutes/120 * 40)
      + 35 * practice_ratio
      + (25 * last_recall_quality/5                if reviewed at least once else 0)
```

`questions_correct` counts **distinct active questions of the competency whose
most recent answer, in a finished attempt, is correct**; `questions_total` is
the number of active questions of the competency. Because it is per distinct
question and by latest answer, answering the same question many times cannot
inflate it, a later wrong answer takes the credit back, and answers in an
attempt that is still open never count. The 50/50 weights live in
`app.domain.mastery` (`CHALLENGE_WEIGHT`, `QUIZ_WEIGHT`); a signal that does
not exist for a competency is ignored, so competencies without a question bank
score exactly as before. The total stays <= 100.

Recomputed after every event that could move it: a study session, a
challenge submission, a finished quiz attempt, a review recall (`app.services.mastery_service`).

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

A study session too short to earn XP (under 10 minutes) still counts for the
streak: `gamification_service.record_activity` updates the streak without
awarding XP, so the streak measures consistency while XP measures effort.

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
  `assessments_passed_count`, `xp_milestone`) and a threshold value. Checked after every XP award
  (`app.services.gamification_service.check_and_award_achievements`).
- **Quests** (`Quest` + `QuestCompletion`): one-time or weekly goals
  (`study_sessions_count`, `challenges_passed_count`,
  `reviews_completed_count`, `assessments_passed_count`, `xp_earned`). Progress is computed fresh from
  activity data on every read and auto-completed (XP awarded) the moment
  the target is crossed — see `app.services.quest_service` for why this
  avoids a separate "claim" endpoint.

## Assessments (question bank and quizzes)

Distinct from challenges (self-assessed activities): a **Question** has a
deterministic or self-graded answer, and quizzes feed the Practice signal of
mastery. No AI is called at runtime; the questions are seed data (written by
Claude, reviewed by the owner — `source=ai_generated`).

- **Question**: `code` (stable key), competency, `type` (`multiple_choice`,
  `multi_select`, `short_answer`, `code_reading` — the last is multiple choice
  over a code snippet), `difficulty` (`easy|medium|hard`), `xp_value` (copied
  from `app.domain.assessments.XP_BY_DIFFICULTY`: 10/20/30), `correct_option_ids`
  (language-independent), `tags`, `source`, `is_active`.
- **QuestionTranslation**: prompt (markdown), options `[{id, text}]`,
  explanation, model answer (short answers), per language. `en` is mandatory,
  `pt-BR` optional with per-question fallback to `en`.
- **Assessment**: ordered question set (`kind`: competency, learning_path or
  mixed), `pass_threshold` (default 70 %), `completion_bonus_xp`.
- **AssessmentAttempt** (snapshot of the question ids served, status, score,
  `passed`, XP breakdown) and **QuestionResponse** (answer, `is_correct`,
  grading status, time, `is_first_correct`, `xp_awarded`).

Grading: choice questions are all-or-nothing and graded when the answer is
saved, but the verdict is only revealed when the attempt is finished.
Short answers stay `pending_review` until the learner marks them right/wrong
after reading the model answer (`self_graded`); an ungraded one counts as wrong.
The extension point for an AI judge (roadmap I5) is
`assessment_service.short_answer_judge`.

**XP rule** (owner decision): XP only when finishing an attempt with
`score >= pass_threshold`; it is the sum of `xp_value` of questions answered
correctly that have never paid XP for that user, plus the completion bonus on
the first pass of that assessment. Repeating pays nothing for paid questions
and no second bonus, but still updates mastery, the streak and quests.
Never refunded. Finishing also flags the competency of every wrongly answered
question for spaced-repetition review (due now; SM-2 state untouched).

### Question seed format

One module per subject in `backend/app/seeds/questions/` (e.g.
`python_subject.py`) exporting `QUESTION_SET = SubjectQuestionSet(subject_slug,
questions, assessments)`; the types are in `questions/types.py`. Modules are
auto-discovered (`loader.py`), so subjects can be added in parallel without
touching a shared file. Each `QuestionSeed` has: `code` (globally unique,
kebab-case, e.g. `python-type-hints-q01`), `competency_slug`, `type`,
`difficulty`, `correct` (option ids; `None` for short answers), `tags`,
`source` and `text: {Language: QuestionText}` where `QuestionText` holds
`prompt`, `explanation`, `options` (ids `a`, `b`, ...) and `model_answer`.

Rules enforced by `python -m app.seeds.questions.validate` (also run by
`app.seeds.run`, which refuses an invalid bank and is idempotent by `code`):
codes and assessment codes are unique; the competency exists; `en` is present;
difficulty/type/source are valid; 2-8 options with unique ids and unique texts;
every correct id is among the options (exactly one for `multiple_choice` and
`code_reading`; at least two, and at least one wrong option, for `multi_select`);
every translation has the same option ids as English; `short_answer` has a
`model_answer` and no options; `code_reading` has a fenced code block that is
identical in every language; assessments reference existing questions, a
competency assessment only its own competency's questions, thresholds are 1-100.
This is the contract for the bulk generation of all 30 competencies (I6).

Besides errors, the validator prints **quality warnings** (J8) that do not fail
it unless `--strict` is passed (`python -m app.seeds.questions.validate
--strict`). Per competency, over English single-answer questions: the correct
option being the strictly longest in more than 50% of the questions (>= 4
questions with >= 3 options; the offending questions are listed), and one
letter holding more than 40% of the correct answers (>= 8 questions). The
thresholds are constants at the top of `validate.py`; fix warnings by
rebalancing option length/order in the seed, not by raising the thresholds.

## Recommendations: "what to study today" (I3)

`GET /recommendations/today` is a deterministic, explainable rule set (no LLM,
no stored state, read-only, never grants XP). Rules are pure functions in
`app.domain.recommendations`; the weights are constants there. Each competency
yields its candidate reasons; only the highest-scoring reason per competency is
kept, results are ordered by score (desc) then competency id, and cut to
`limit` (default 5, max 20).

| Kind | When | Score |
|---|---|---|
| `review_due` | an SRS review is due (any state) | 100 + days overdue (capped at 30) |
| `goal_deadline` | an active goal with a target date <= 14 days away (or past) is linked to a `learning`/`available` competency | 85 + 25 x closeness (85 at 14 days, 110 on/after the date) |
| `strengthen_weak` | `learning`, mastery < 40 or last recall quality < 3 | 70 + 10 x shortfall below 40, +5 on a recall lapse |
| `next_in_path` | first `available` step of a path under way (a step learning/mastered, not all mastered) | 55 |
| `take_quiz` | `learning`, has an active quiz, quiz coverage < 50% | 45 + 10 x gap below 50% |
| `continue_learning` | any other `learning` competency | 40 + 20 x distance from mastery 80 |

Quiz coverage is the Practice signal's: distinct active questions whose latest
finished answer is correct / active questions. A new user with nothing else
gets one starting point (score 50): the first `available` step of the first
learning path, else the first `available` competency. Goals have no structural
link to the catalog, so a goal is linked to a competency when its title or
description mentions the competency name (whole phrase, case-insensitive), or
the subject name (then the subject's weakest `learning` competency, else its
first `available`). The reason text is a localised template
(`app.domain.recommendation_messages`, `en` / `pt-BR`, English fallback).
