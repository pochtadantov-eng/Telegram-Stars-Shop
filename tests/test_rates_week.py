from bot.rates import week_ends_in, week_start_ts


def test_week_window_positive():
    start = week_start_ts()
    left = week_ends_in()
    assert start > 0
    assert 0 < left <= 7 * 24 * 3600
