"""Поиск офферов и разбор настроек справочников."""

from app.keitaro.models import Offer


async def test_search_ranks_exact_id_then_prefix_then_substring(catalog, fake):
    fake.offers = [
        Offer(id=700, name="alpha"),
        Offer(id=3, name="x 7 y"),
        Offer(id=7, name="beta"),
        Offer(id=8, name="7 prefix"),
    ]
    found = await catalog.search_offers("7")
    assert [o.id for o in found] == [7, 8, 700, 3]


async def test_empty_query_returns_active_offers_only(catalog, fake):
    fake.offers = [Offer(id=1, name="a"), Offer(id=2, name="b", state="deleted")]
    assert [o.id for o in await catalog.search_offers("")] == [1]


async def test_search_respects_limit(catalog, fake):
    fake.offers = [Offer(id=i, name=f"offer {i}") for i in range(1, 6)]
    assert len(await catalog.search_offers("", limit=2)) == 2
