"""Async-клиент Keitaro Admin API v1: единственное место с HTTP."""

import logging
from datetime import date
from typing import Any

import httpx

from app.config import Settings
from app.errors import NotFoundError, UpstreamError
from app.keitaro.models import (
    Campaign,
    Domain,
    Group,
    Offer,
    Stats,
    StatsReport,
    Stream,
    TrafficSource,
)

log = logging.getLogger(__name__)


def build_http_client(settings: Settings) -> httpx.AsyncClient:
    """Создаёт HTTP-клиент с ключом API.

    Ретраи только при ошибке соединения: повторять POST после ответа небезопасно.
    """
    return httpx.AsyncClient(
        base_url=settings.keitaro_api_url,
        headers={
            "Api-Key": settings.keitaro_api_key.get_secret_value(),
            "Accept": "application/json",
        },
        timeout=httpx.Timeout(settings.keitaro_timeout),
        transport=httpx.AsyncHTTPTransport(retries=2),
    )


def _error_text(resp: httpx.Response) -> str:
    """Достаёт из ответа Keitaro текст ошибки."""
    try:
        data = resp.json()
    except ValueError:
        return resp.text[:200]
    if isinstance(data, dict):
        for key in ("error", "message", "errors"):
            if data.get(key):
                return str(data[key])[:300]
    return str(data)[:300]


class KeitaroClient:
    """Реализация `KeitaroPort` поверх HTTP."""

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def _request(
        self, method: str, path: str, *, json: Any = None, params: dict | None = None
    ) -> Any:
        """Выполняет запрос и переводит ошибки HTTP в доменные ошибки."""
        try:
            resp = await self._http.request(method, path, json=json, params=params)
        except httpx.TimeoutException as exc:
            raise UpstreamError("Keitaro не ответил вовремя, попробуйте ещё раз") from exc
        except httpx.HTTPError as exc:
            raise UpstreamError("Не удалось связаться с Keitaro") from exc

        if resp.status_code == 404:
            raise NotFoundError("Объект не найден в Keitaro")
        if resp.status_code in (401, 403):
            raise UpstreamError("Keitaro отклонил API-ключ: проверьте KEITARO_API_KEY")
        if resp.status_code >= 400:
            log.warning("Keitaro %s %s -> %s", method, path, resp.status_code)
            raise UpstreamError(
                f"Keitaro вернул {resp.status_code} на {method} /{path}: {_error_text(resp)}"
            )
        return resp.json() if resp.content else None

    async def list_domains(self) -> list[Domain]:
        """Список доменов."""
        return [Domain.model_validate(i) for i in await self._request("GET", "domains")]

    async def list_groups(self, group_type: str = "campaigns") -> list[Group]:
        """Список групп заданного типа: Keitaro требует параметр `type`."""
        data = await self._request("GET", "groups", params={"type": group_type})
        return [Group.model_validate(i) for i in data]

    async def list_traffic_sources(self) -> list[TrafficSource]:
        """Список источников трафика."""
        data = await self._request("GET", "traffic_sources")
        return [TrafficSource.model_validate(i) for i in data]

    async def list_offers(self) -> list[Offer]:
        """Список офферов."""
        return [Offer.model_validate(i) for i in await self._request("GET", "offers")]

    async def list_campaigns(self) -> list[Campaign]:
        """Список кампаний."""
        return [Campaign.model_validate(i) for i in await self._request("GET", "campaigns")]

    async def get_campaign(self, campaign_id: int) -> Campaign:
        """Кампания по ID."""
        return Campaign.model_validate(await self._request("GET", f"campaigns/{campaign_id}"))

    async def create_campaign(self, payload: dict) -> Campaign:
        """Создаёт кампанию."""
        return Campaign.model_validate(await self._request("POST", "campaigns", json=payload))

    async def delete_campaign(self, campaign_id: int) -> None:
        """Удаляет кампанию; Keitaro переносит её в архив."""
        await self._request("DELETE", f"campaigns/{campaign_id}")

    async def list_streams(self, campaign_id: int) -> list[Stream]:
        """Потоки кампании."""
        data = await self._request("GET", f"campaigns/{campaign_id}/streams")
        return [Stream.model_validate(i) for i in data]

    async def create_stream(self, payload: dict) -> Stream:
        """Создаёт поток."""
        return Stream.model_validate(await self._request("POST", "streams", json=payload))

    async def update_stream(self, stream_id: int, payload: dict) -> Stream:
        """Обновляет переданные поля потока."""
        data = await self._request("PUT", f"streams/{stream_id}", json=payload)
        return Stream.model_validate(data)

    async def stream_stats(
        self, campaign_id: int, date_from: date, date_to: date, timezone: str
    ) -> StatsReport:
        """Клики, уники и боты по потокам кампании и итого за период.

        Итог берётся из summary отчёта: один посетитель мог попасть в несколько потоков,
        поэтому сумма по потокам завышает уникальные клики.
        """
        body = {
            "range": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
                "timezone": timezone,
            },
            "metrics": ["clicks", "campaign_unique_clicks", "bots"],
            "grouping": ["stream_id"],
            "filters": [{"name": "campaign_id", "operator": "EQUALS", "expression": campaign_id}],
            "summary": True,
            "limit": 500,
            "offset": 0,
        }
        data = await self._request("POST", "report/build", json=body) or {}
        rows = data.get("rows") or []
        per_stream = {
            int(r["stream_id"]): Stats.from_row(r) for r in rows if r.get("stream_id") is not None
        }
        if data.get("summary"):
            total = Stats.from_row(data["summary"])
        else:
            total = Stats(
                clicks=sum(s.clicks for s in per_stream.values()),
                unique=sum(s.unique for s in per_stream.values()),
                bots=sum(s.bots for s in per_stream.values()),
            )
        return StatsReport(per_stream=per_stream, total=total)
