"""Периоды статистики."""

from datetime import date, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from app.errors import ValidationFailed

RangeKey = Literal["today", "yesterday", "7d", "30d"]
"""Допустимые периоды статистики."""

_DAYS_BACK = {"today": 0, "7d": 6, "30d": 29}


def resolve_range(key: str, timezone: str, now: datetime | None = None) -> tuple[date, date]:
    """Возвращает границы периода (включительно) в часовом поясе Keitaro.

    Raises:
        ValidationFailed: неизвестный ключ периода.
    """
    today = (now or datetime.now(ZoneInfo(timezone))).date()
    if key == "yesterday":
        day = today - timedelta(days=1)
        return day, day
    if key in _DAYS_BACK:
        return today - timedelta(days=_DAYS_BACK[key]), today
    raise ValidationFailed(f"Неизвестный период: {key}")
