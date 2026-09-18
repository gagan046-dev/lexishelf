from app.services.spaced_repetition import MAX_INTERVAL_DAYS, MIN_EASE, MIN_INTERVAL_DAYS, schedule_next


def test_again_resets_streak_and_interval():
    interval, ease, streak = schedule_next(interval_days=10, ease=2.5, streak=4, result="again")

    assert interval == MIN_INTERVAL_DAYS
    assert streak == 0
    assert ease < 2.5


def test_ease_never_drops_below_floor():
    interval, ease, _ = schedule_next(interval_days=1, ease=MIN_EASE, streak=0, result="again")

    assert ease == MIN_EASE


def test_good_grows_interval_and_streak():
    interval, ease, streak = schedule_next(interval_days=2, ease=2.5, streak=1, result="good")

    assert interval == 5.0
    assert ease == 2.5
    assert streak == 2


def test_easy_grows_interval_faster_and_raises_ease():
    interval, ease, streak = schedule_next(interval_days=2, ease=2.5, streak=1, result="easy")

    assert interval > 5.0
    assert ease == 2.65
    assert streak == 2


def test_hard_grows_interval_slowly_and_lowers_ease():
    interval, ease, streak = schedule_next(interval_days=10, ease=2.5, streak=3, result="hard")

    assert interval == 12.0
    assert ease == 2.35
    assert streak == 3


def test_interval_is_capped():
    interval, _, _ = schedule_next(interval_days=MAX_INTERVAL_DAYS, ease=3.0, streak=10, result="easy")

    assert interval == MAX_INTERVAL_DAYS
