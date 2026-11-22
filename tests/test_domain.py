from datetime import datetime

import pytest

from app.domain.geo import parse_geo
from app.domain.ranges import resolve_range
from app.domain.shares import split_evenly
from app.errors import ValidationFailed


@pytest.mark.parametrize("n", range(1, 12))
def test_shares_always_sum_to_100(n):
    shares = split_evenly(n)
    assert len(shares) == n and sum(shares) == 100
    assert max(shares) - min(shares) <= 1


def test_shares_remainder_goes_first():
    assert split_evenly(3) == [34, 33, 33]
    assert split_evenly(0) == []


def test_parse_geo_normalizes_and_dedupes():
    assert parse_geo(" au, MX;ro  au ") == ["AU", "MX", "RO"]


@pytest.mark.parametrize("raw", ["", "  ", "AUS", "A1", "AU,1"])
def test_parse_geo_rejects_bad_input(raw):
    with pytest.raises(ValidationFailed):
        parse_geo(raw)


def test_ranges_are_inclusive():
    now = datetime(2026, 11, 20, 12, 0)
    assert resolve_range("today", "UTC", now) == (now.date(), now.date())
    assert str(resolve_range("7d", "UTC", now)[0]) == "2026-11-14"
    assert str(resolve_range("30d", "UTC", now)[0]) == "2026-10-22"
    assert str(resolve_range("yesterday", "UTC", now)[1]) == "2026-11-19"
