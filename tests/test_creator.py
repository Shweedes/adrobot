import re

import pytest

from app.errors import (
    ConfigurationError,
    ConflictError,
    NotFoundError,
    UpstreamError,
    ValidationFailed,
)
from app.keitaro.models import Campaign, Domain


async def test_creates_campaign_with_two_ordered_streams(creator, fake):
    result = await creator.create(name="campaign1", geo="au, mx", offer_id=2)

    assert result.name == "test_ivanov_campaign1"
    assert result.geo == ["AU", "MX"]
    assert result.tracking_url == "https://in.posdk.xyz/abc123"

    geo, offer = sorted(fake.streams.values(), key=lambda s: s.position)
    assert (geo.position, offer.position) == (1, 2)
    assert geo.action_payload == "https://google.com"
    assert geo.filters[0].name == "country" and geo.filters[0].mode == "accept"
    assert geo.filters[0].values() == ["AU", "MX"]
    assert [(o.offer_id, o.share) for o in offer.offers] == [(2, 100)]
    assert offer.filters == []
    assert geo.action_type and offer.action_type, "Keitaro требует action_type у обоих потоков"


async def test_campaign_uses_configured_domain_group_and_source(creator, fake):
    await creator.create(name="c", geo="AU", offer_id=1)
    payload = fake.last_campaign_payload
    assert payload["domain_id"] == 10 and payload["traffic_source_id"] == 30
    assert payload["group_id"] == 20, "нужна группа кампаний, а не одноимённая группа офферов"
    assert payload["type"] == "position" and payload["cost_type"] == "CPC"
    assert re.fullmatch(r"[A-Za-z0-9]{6}", payload["alias"]), "alias обязателен в Keitaro API"


async def test_prefix_is_not_duplicated(creator):
    result = await creator.create(name="test_ivanov_x", geo="AU", offer_id=1)
    assert result.name == "test_ivanov_x"


async def test_prefix_only_name_is_rejected(creator):
    with pytest.raises(ValidationFailed):
        await creator.create(name="test_ivanov_", geo="AU", offer_id=1)


async def test_duplicate_name_is_rejected(creator, fake):
    await creator.create(name="dup", geo="AU", offer_id=1)
    with pytest.raises(ConflictError):
        await creator.create(name="dup", geo="AU", offer_id=1)
    assert len(fake.campaigns) == 1


async def test_unknown_offer_creates_nothing(creator, fake):
    with pytest.raises(NotFoundError):
        await creator.create(name="c", geo="AU", offer_id=999)
    assert fake.campaigns == {}


async def test_failed_second_stream_rolls_campaign_back(creator, fake, uow):
    fake.fail_on_stream_number = 2
    with pytest.raises(UpstreamError):
        await creator.create(name="c", geo="AU", offer_id=1)

    assert len(fake.deleted) == 1 and fake.campaigns == {}
    assert not await uow.campaigns.name_exists("test_ivanov_c")


async def test_wrong_config_names_are_reported_together(creator, fake):
    fake.domains = [Domain(id=1, name="other.com")]
    fake.sources = []
    with pytest.raises(ConfigurationError) as exc:
        await creator.create(name="c", geo="AU", offer_id=1)

    message = exc.value.message
    assert "KEITARO_DOMAIN" in message and "other.com" in message, "видно, какие домены есть"
    assert "KEITARO_SOURCE" in message
    assert "KEITARO_GROUP" not in message, "группа найдена, о ней не говорим"
    assert fake.campaigns == {}


async def test_name_taken_by_archived_campaign_gives_friendly_error(creator, fake):
    fake.campaign_error = (
        "Keitaro вернул 422 на POST /campaigns: "
        "{'name': ['Name has already been used in the archive']}"
    )
    with pytest.raises(ConflictError) as exc:
        await creator.create(name="c", geo="AU", offer_id=1)
    assert "архив" in exc.value.message


async def test_geo_stream_is_regular_and_offer_stream_is_default(creator, fake):
    await creator.create(name="types", geo="AU", offer_id=1)
    by_position = sorted(fake.created_stream_payloads, key=lambda p: p["position"])
    assert [p["type"] for p in by_position] == ["regular", "default"]


async def test_name_is_free_again_after_campaign_deleted_in_keitaro(creator, fake):
    first = await creator.create(name="again", geo="AU", offer_id=1)
    await fake.delete_campaign(first.id)

    second = await creator.create(name="again", geo="AU", offer_id=1)
    assert second.id != first.id and second.name == "test_ivanov_again"


async def test_name_taken_in_keitaro_admin_is_rejected(creator, fake):
    fake.campaigns[1] = Campaign(id=1, name="test_ivanov_manual", state="active")
    with pytest.raises(ConflictError):
        await creator.create(name="manual", geo="AU", offer_id=1)
