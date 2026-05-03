"""Basic smoke tests for the screener engine and API."""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_screener_run_empty_filters():
    """Run screener with no filters — should return 200 even with empty DB."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.post("/v1/screener/run", json={
            "filters": [],
            "logic": "AND",
            "exchange": ["NSE"],
            "sort_by": "market_cap",
            "sort_order": "desc",
            "page": 1,
            "per_page": 10,
        })
    assert r.status_code == 200
    body = r.json()
    assert "total" in body
    assert "results" in body


@pytest.mark.asyncio
async def test_screener_run_with_filters():
    """Screener with typical fundamental filters."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.post("/v1/screener/run", json={
            "filters": [
                {"field": "pe_ratio", "operator": "lt", "value": 25},
                {"field": "roe", "operator": "gt", "value": 15},
            ],
            "logic": "AND",
            "exchange": ["NSE", "BSE"],
            "sort_by": "composite_score",
            "sort_order": "desc",
            "page": 1,
            "per_page": 20,
        })
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_stock_search_empty():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.get("/v1/stocks/search?q=reliance")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
