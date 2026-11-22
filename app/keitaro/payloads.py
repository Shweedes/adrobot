"""Тела запросов Keitaro Admin API: единственное место со знанием формата."""

import secrets
import string

from app.keitaro.models import Offer, StreamOffer


def new_alias(length: int = 6) -> str:
    """Генерирует короткий идентификатор кампании для ссылки; в API он обязателен."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def campaign_payload(*, name: str, group_id: int, source_id: int, domain_id: int) -> dict:
    """Кампания с ротацией по позиции и моделью затрат CPC.

    `cost_auto` берёт стоимость из параметра `cost`.
    """
    return {
        "name": name,
        "alias": new_alias(),
        "type": "position",
        "state": "active",
        "cost_type": "CPC",
        "cost_value": 0,
        "cost_currency": "USD",
        "cost_auto": True,
        "group_id": group_id,
        "traffic_source_id": source_id,
        "domain_id": domain_id,
    }


def geo_stream_payload(*, campaign_id: int, geo: list[str], redirect_url: str) -> dict:
    """Поток 1: пропускает страны из `geo` и перенаправляет их на `redirect_url`."""
    return {
        "campaign_id": campaign_id,
        "name": f"Geo {', '.join(geo)}",
        "type": "regular",
        "position": 1,
        "weight": 100,
        "schema": "redirect",
        "action_type": "http",
        "action_payload": redirect_url,
        "collect_clicks": True,
        "filter_or": False,
        "filters": [{"name": "country", "mode": "accept", "payload": geo}],
        "state": "active",
    }


def offer_stream_payload(*, campaign_id: int, offer: Offer) -> dict:
    """Поток 2: без фильтров, весь остальной трафик идёт на оффер.

    Keitaro требует `action_type` и у потоков с офферами.
    """
    return {
        "campaign_id": campaign_id,
        "name": f"Offer {offer.id}",
        "type": "regular",
        "position": 2,
        "weight": 100,
        "schema": "landings",
        "action_type": "http",
        "collect_clicks": True,
        "filter_or": False,
        "filters": [],
        "offers": [{"offer_id": offer.id, "share": 100, "state": "active"}],
        "state": "active",
    }


def offers_update_payload(offers: list[StreamOffer], shares: list[int]) -> dict:
    """Новый состав офферов потока с заданными долями."""
    return {
        "offers": [
            {"offer_id": o.offer_id, "share": share, "state": o.state or "active"}
            for o, share in zip(offers, shares, strict=True)
        ]
    }
