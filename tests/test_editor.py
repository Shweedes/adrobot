import pytest

from app.errors import ConflictError, ForbiddenError, NotFoundError
from app.keitaro.models import Campaign


async def _make(creator, fake):
    created = await creator.create(name="c", geo="AU", offer_id=1)
    offer_stream = next(s for s in fake.streams.values() if s.position == 2)
    redirect_stream = next(s for s in fake.streams.values() if s.position == 1)
    return created.id, offer_stream.id, redirect_stream.id


def _offers(view, stream_id):
    return next(s for s in view.streams if s.id == stream_id).offers


async def test_view_contains_streams_and_stats(creator, editor, fake):
    cid, offer_sid, redirect_sid = await _make(creator, fake)
    view = await editor.get_details(cid, "today")

    assert [s.kind for s in view.streams] == ["redirect", "offers"]
    assert view.streams[0].target == "https://google.com"
    assert view.streams[0].filters[0].values == ["AU"]
    assert view.streams[1].stats.clicks == 10 and view.streams[1].stats.unique == 8
    assert (view.totals.clicks, view.totals.unique, view.totals.bots) == (20, 16, 4)
    assert view.campaign.tracking_url == "https://in.posdk.xyz/abc123"
    assert _offers(view, offer_sid)[0].name == "Miaflow spin"


async def test_add_offer_rebalances_shares_to_100(creator, editor, fake):
    cid, sid, _ = await _make(creator, fake)

    view = await editor.add_offer(cid, sid, 2, "today")
    assert [(o.offer_id, o.share) for o in _offers(view, sid)] == [(1, 50), (2, 50)]

    view = await editor.add_offer(cid, sid, 3, "today")
    assert sorted(o.share for o in _offers(view, sid)) == [33, 33, 34]


async def test_cannot_add_same_offer_twice(creator, editor, fake):
    cid, sid, _ = await _make(creator, fake)
    with pytest.raises(ConflictError):
        await editor.add_offer(cid, sid, 1, "today")


async def test_cannot_add_unknown_offer(creator, editor, fake):
    cid, sid, _ = await _make(creator, fake)
    with pytest.raises(NotFoundError):
        await editor.add_offer(cid, sid, 999, "today")


async def test_remove_offer_gives_traffic_to_remaining(creator, editor, fake):
    cid, sid, _ = await _make(creator, fake)
    await editor.add_offer(cid, sid, 2, "today")

    view = await editor.remove_offer(cid, sid, 1, "today")
    assert [(o.offer_id, o.share) for o in _offers(view, sid)] == [(2, 100)]


async def test_last_offer_can_be_removed_and_added_back(creator, editor, fake):
    cid, sid, _ = await _make(creator, fake)

    view = await editor.remove_offer(cid, sid, 1, "today")
    assert _offers(view, sid) == []

    view = await editor.add_offer(cid, sid, 1, "today")
    assert [(o.offer_id, o.share) for o in _offers(view, sid)] == [(1, 100)]


async def test_cannot_remove_missing_offer(creator, editor, fake):
    cid, sid, _ = await _make(creator, fake)
    with pytest.raises(NotFoundError):
        await editor.remove_offer(cid, sid, 3, "today")


async def test_redirect_stream_has_no_offers_to_edit(creator, editor, fake):
    cid, _, redirect_sid = await _make(creator, fake)
    with pytest.raises(ConflictError):
        await editor.add_offer(cid, redirect_sid, 2, "today")


async def test_foreign_campaigns_are_protected(editor, fake):
    fake.campaigns[5] = Campaign(id=5, name="someone_elses_campaign", state="active")
    with pytest.raises(ForbiddenError):
        await editor.get_details(5, "today")
    assert await editor.list_campaigns("") == []
