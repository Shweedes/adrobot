"""Распределение долей трафика."""


def split_evenly(count: int) -> list[int]:
    """Делит 100% поровну; остаток достаётся первым элементам.

    Пример: `split_evenly(3) == [34, 33, 33]`.
    """
    if count <= 0:
        return []
    base, remainder = divmod(100, count)
    return [base + (1 if i < remainder else 0) for i in range(count)]
