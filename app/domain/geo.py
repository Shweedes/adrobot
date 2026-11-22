"""Разбор кодов стран."""

import re

from app.errors import ValidationFailed

_SPLIT = re.compile(r"[\s,;]+")
_ISO2 = re.compile(r"^[A-Z]{2}$")


def parse_geo(raw: str) -> list[str]:
    """Разбирает `"au, MX;ro"` в `["AU", "MX", "RO"]` без дубликатов.

    Raises:
        ValidationFailed: список пуст или код не из двух латинских букв.
    """
    codes = list(dict.fromkeys(c.upper() for c in _SPLIT.split(raw.strip()) if c))
    if not codes:
        raise ValidationFailed("Гео: укажите хотя бы один код страны")
    invalid = [c for c in codes if not _ISO2.match(c)]
    if invalid:
        raise ValidationFailed(
            f"Гео: «{', '.join(invalid)}» — нужны двухбуквенные коды вроде AU или MX"
        )
    return codes
