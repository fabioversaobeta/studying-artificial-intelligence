"""Simplified SM-2 spaced-repetition algorithm (the same core algorithm used
by Anki/SuperMemo, without the optional bells and belts).

Quality is a 0-5 self-assessed recall rating supplied by the learner:
  0-2: forgot / recalled with serious difficulty -> restart the interval
  3-5: recalled correctly, with decreasing effort -> interval grows

Kept isolated from the ORM/service layer so the scheduling algorithm can be
swapped later (see docs/PENDING.md) without touching persistence code.
"""

from dataclasses import dataclass

MIN_EASE_FACTOR = 1.3
DEFAULT_EASE_FACTOR = 2.5
QUALITY_PASS_THRESHOLD = 3


@dataclass(frozen=True)
class ReviewState:
    interval_days: int
    ease_factor: float
    repetitions: int


def next_review_state(current: ReviewState, quality: int) -> ReviewState:
    if not 0 <= quality <= 5:
        raise ValueError("quality must be between 0 and 5")

    if quality < QUALITY_PASS_THRESHOLD:
        return ReviewState(interval_days=1, ease_factor=current.ease_factor, repetitions=0)

    if current.repetitions == 0:
        interval = 1
    elif current.repetitions == 1:
        interval = 6
    else:
        interval = round(current.interval_days * current.ease_factor)

    new_ease_factor = max(
        MIN_EASE_FACTOR,
        current.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
    )

    return ReviewState(
        interval_days=interval,
        ease_factor=round(new_ease_factor, 3),
        repetitions=current.repetitions + 1,
    )
