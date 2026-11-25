"""Фейковый Keitaro в памяти с тем же контрактом, что у `KeitaroPort`."""

from app.errors import NotFoundError, UpstreamError
from app.keitaro.models import (
    Campaign,
    Domain,
    Group,
    Offer,
    Stats,
    StatsReport,
    Stream,
    StreamOffer,
    TrafficSource,
)


class FakeKeitaro:
    """Хранит кампании и потоки в словарях; ошибки включаются атрибутами."""

    def __init__(self) -> None:
        self.offers = [
            Offer(id=1, name="Miaflow spin", state="active"),
            Offer(id=2, name="Miaflow prize", state="active"),
            Offer(id=3, name="Other offer", state="active"),
        ]
        self.domains = [Domain(id=10, name="in.posdk.xyz")]
        self.groups = [
            Group(id=21, name="FORTESTS", type="offers"),
            Group(id=20, name="FORTESTS", type="campaigns"),
        ]
        self.sources = [TrafficSource(id=30, name="FORTESTS")]
        self.campaigns: dict[int, Campaign] = {}
        self.streams: dict[int, Stream] = {}
        self.deleted: list[int] = []
        self.last_campaign_payload: dict = {}
        self.created_stream_payloads: list[dict] = []
        self.fail_on_stream_number: int | None = None
        self.campaign_error: str | None = None
        self.stats_error: Exception | None = None
        self._next_id = 100
        self._streams_created = 0

    def _id(self) -> int:
        self._next_id += 1
        return self._next_id

    async def list_offers(self):
        return list(self.offers)

    async def list_domains(self):
        return list(self.domains)

    async def list_groups(self, group_type="campaigns"):
        return [g for g in self.groups if g.type == group_type]

    async def list_traffic_sources(self):
        return list(self.sources)

    async def list_campaigns(self):
        return list(self.campaigns.values())

    async def get_campaign(self, campaign_id):
        if campaign_id not in self.campaigns:
            raise NotFoundError("Объект не найден в Keitaro")
        return self.campaigns[campaign_id]

    async def create_campaign(self, payload):
        if self.campaign_error:
            raise UpstreamError(self.campaign_error)
        self.last_campaign_payload = payload
        campaign_id = self._id()
        self.campaigns[campaign_id] = Campaign(
            id=campaign_id,
            name=payload["name"],
            alias="abc123",
            state="active",
            domain_id=payload["domain_id"],
        )
        return self.campaigns[campaign_id]

    async def delete_campaign(self, campaign_id):
        self.deleted.append(campaign_id)
        self.campaigns.pop(campaign_id, None)

    async def list_streams(self, campaign_id):
        return [s for s in self.streams.values() if s.campaign_id == campaign_id]

    async def create_stream(self, payload):
        self._streams_created += 1
        if self.fail_on_stream_number == self._streams_created:
            raise UpstreamError("Keitaro вернул 500: boom")
        self.created_stream_payloads.append(payload)
        stream = Stream.model_validate({"id": self._id(), **payload})
        self.streams[stream.id] = stream
        return stream

    async def update_stream(self, stream_id, payload):
        stream = self.streams[stream_id]
        stream.offers = [StreamOffer(**o) for o in payload["offers"]]
        return stream

    async def stream_stats(self, campaign_id, date_from, date_to, timezone):
        if self.stats_error:
            raise self.stats_error
        streams = await self.list_streams(campaign_id)
        per_stream = {s.id: Stats(clicks=10, unique=8, bots=2) for s in streams}
        return StatsReport(per_stream=per_stream, total=Stats(clicks=20, unique=16, bots=4))
