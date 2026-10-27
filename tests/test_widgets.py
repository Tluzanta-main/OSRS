import pytest

from widgets import format_seconds


def test_none_shows_dash():
    assert format_seconds(None) == "-"


@pytest.mark.parametrize("seconds, expected", [
    (0, "0s"),
    (45, "45s"),
    (59, "59s"),   # last value before minutes appear
])
def test_under_a_minute_shows_seconds_only(seconds, expected):
    assert format_seconds(seconds) == expected


@pytest.mark.parametrize("seconds, expected", [
    (60, "1m 0s"),        # first value with minutes
    (187, "3m 7s"),       # 3 * 60 + 7
    (3599, "59m 59s"),    # last value before hours appear
])
def test_under_an_hour_shows_minutes_and_seconds(seconds, expected):
    assert format_seconds(seconds) == expected


@pytest.mark.parametrize("seconds, expected", [
    (3600, "1h 0m"),      # first value with hours
    (7300, "2h 1m"),      # 2 * 3600 + 1 * 60 + 40; the 40s is dropped
])
def test_an_hour_or_more_shows_hours_and_minutes(seconds, expected):
    assert format_seconds(seconds) == expected


def test_large_values_keep_counting_hours():
    assert format_seconds(90_000) == "25h 0m"  # 25 * 3600, no days unit
