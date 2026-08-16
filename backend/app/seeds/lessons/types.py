"""Shared type for per-subject lesson content files (see the sibling
modules in this package — one per subject).

Each subject file exports a `LESSONS: dict[str, list[LessonModule]]`
mapping a competency slug to its ordered lesson modules. The number of
modules per competency should track the topic's real complexity, not a
fixed count: a narrow topic might need one module, SOLID needs one per
principle plus a synthesis module, and so on.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LessonModule:
    title: str
    content: str  # Markdown.
