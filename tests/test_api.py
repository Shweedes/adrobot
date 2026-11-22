import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_creator
from app.api.error_handlers import register_error_handlers
from app.api.routes import router


@pytest.fixture
async def http(creator):
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_creator] = lambda: creator
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def test_create_returns_201(http):
    r = await http.post("/api/campaigns", json={"name": "c", "geo": "AU", "offer_id": 1})
    assert r.status_code == 201
    assert r.json()["name"] == "test_ivanov_c"


async def test_request_validation_uses_error_envelope(http):
    r = await http.post("/api/campaigns", json={"name": "", "geo": "AU", "offer_id": 1})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"
    assert "Название" in r.json()["error"]["message"]


async def test_domain_validation_uses_error_envelope(http):
    r = await http.post("/api/campaigns", json={"name": "c", "geo": "AUS", "offer_id": 1})
    assert r.status_code == 422
    assert "Гео" in r.json()["error"]["message"]


async def test_conflict_maps_to_409(http):
    body = {"name": "c", "geo": "AU", "offer_id": 1}
    await http.post("/api/campaigns", json=body)
    r = await http.post("/api/campaigns", json=body)
    assert r.status_code == 409
