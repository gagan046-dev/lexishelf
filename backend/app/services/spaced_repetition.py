"""A simplified SM-2-style spaced-repetition schedule.

Pure and deterministic so it can be unit tested without a database.
"""

MIN_EASE = 1.3
MIN_INTERVAL_DAYS = 1.0
MAX_INTERVAL_DAYS = 180.0


def schedule_next(
    interval_days: float,
    ease: float,
    streak: int,
    result: str,
) -> tuple[float, float, int]:
    """Return (new_interval_days, new_ease, new_streak) for a review grading result."""
    if result == "again":
        return MIN_INTERVAL_DAYS, max(MIN_EASE, ease - 0.2), 0

    if result == "hard":
        next_interval = max(MIN_INTERVAL_DAYS, interval_days * 1.2)
        return min(next_interval, MAX_INTERVAL_DAYS), max(MIN_EASE, ease - 0.15), streak

    if result == "good":
        next_interval = max(MIN_INTERVAL_DAYS, interval_days * ease)
        return min(next_interval, MAX_INTERVAL_DAYS), ease, streak + 1

    if result == "easy":
        next_interval = max(MIN_INTERVAL_DAYS, interval_days * ease * 1.3)
        return min(next_interval, MAX_INTERVAL_DAYS), ease + 0.15, streak + 1

    raise ValueError(f"Unknown review result: {result!r}")
