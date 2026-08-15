"""Pure XP -> level formula. No I/O, no ORM — easy to unit test in isolation.

Growth is triangular: the XP required to reach each new level increases
linearly with the level number, so leveling up feels achievable early and
meaningfully harder later without needing an exponential curve.

    Level 1 ->  0 XP (start)
    Level 2 ->  100 XP cumulative
    Level 3 ->  300 XP cumulative
    Level 4 ->  600 XP cumulative
    Level 5 -> 1000 XP cumulative
    Level N -> 100 * N * (N-1) / 2 XP cumulative
"""

XP_PER_LEVEL_STEP = 100


def total_xp_required_for_level(level: int) -> int:
    """Cumulative XP required to *reach* the given level (level >= 1)."""
    if level <= 1:
        return 0
    return XP_PER_LEVEL_STEP * level * (level - 1) // 2


def compute_level(total_xp: int) -> int:
    """The highest level whose XP requirement `total_xp` satisfies."""
    if total_xp < 0:
        raise ValueError("total_xp cannot be negative")

    level = 1
    while total_xp >= total_xp_required_for_level(level + 1):
        level += 1
    return level


def xp_to_next_level(total_xp: int) -> int:
    """XP still needed to reach the next level from the current total."""
    current_level = compute_level(total_xp)
    return total_xp_required_for_level(current_level + 1) - total_xp
