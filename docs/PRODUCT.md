# Product Vision

## What this is

A personal learning and career-development platform: a single place to set
learning goals, work through structured content across subjects and
competencies, practice through study sessions and challenges, track mastery
(not just activity), review with spaced repetition, and stay motivated
through gamification — all in service of becoming a stronger, AI-native
senior software engineer ready for international technical interviews.

This is a single-owner personal tool, not a multi-tenant SaaS product. It's
built to production-quality standards (see `docs/ARCHITECTURE.md`) because
that discipline is itself part of the learning goal, and because a tool used
for years needs to survive its own growth.

## Who it's for

One user (the platform owner) today. The domain model (subjects and
competencies as data, not code) is designed so it could support more users
later without a rewrite, but multi-tenancy, teams, and sharing are
explicitly out of scope until there's a real reason to build them.

## Core capabilities (v1 — see docs/ROADMAP.md for status)

- **Learning goals** — high-level objectives ("become interview-ready for
  senior backend roles").
- **Subjects & competencies** — the catalog of what can be learned,
  organized as a skill tree with prerequisites (locked → available →
  learning → mastered).
- **Learning paths** — curated sequences of competencies across subjects.
- **Study sessions** — logging time spent studying a competency.
- **Challenges** — practical, self-assessed exercises per competency.
- **Mastery** — a transparent, deterministic score (0-100) per competency,
  distinct from XP (see docs/DECISIONS.md).
- **Spaced repetition** — a review queue (SM-2-lite) that resurfaces
  competencies before they're forgotten.
- **Gamification** — XP, levels, streaks, achievements, and quests, to
  measure and reward *activity* (separately from mastery, which measures
  *knowledge*).
- **Dashboard** — level, XP, streak, active goals, due reviews, weakest
  competencies, recent activity.

## Planned, not yet built (see docs/ROADMAP.md and docs/PENDING.md)

- AI Mentor: an abstraction over an LLM provider for generating questions,
  evaluating explanations, and recommending what to study next.
- Formal assessments/quizzes (question banks) beyond self-assessed
  challenges.
- Interview simulation (coding / system design / behavioral) as first-class
  guided sessions.
- Career readiness scoring against a pasted job description.
- Automated (rather than self-assessed) challenge grading.

None of these are placeholder features in the running app — they simply
don't exist yet. The architecture (modular monolith, content as data,
service-layer abstractions) is built so each can be added without
restructuring what already works.

## Product principles

1. **Content is data.** Subjects, competencies, paths, challenges,
   achievements, and quests are database rows, seeded from
   `backend/app/seeds/`, never hardcoded in application logic.
2. **Activity ≠ knowledge.** XP tracks that you showed up. Mastery tracks
   whether you can actually do the thing. They're computed independently.
3. **Transparent over clever.** The mastery formula, leveling curve, and
   spaced-repetition algorithm are all simple, documented, and swappable —
   not black boxes, even when an AI-assisted version would be flashier.
4. **A real v1 over a fake complete one.** Every shipped feature works
   end-to-end against a real database. Nothing is wired up to look done
   while silently doing nothing.
