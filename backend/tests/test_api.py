import pytest
from httpx import ASGITransport, AsyncClient

from app.database import Base, get_db
from app.main import app

import sqlalchemy


_test_db_url = "sqlite+aiosqlite:///./test_trading.db"
_test_engine = sqlalchemy.ext.asyncio.create_async_engine(_test_db_url)
_test_session = sqlalchemy.ext.asyncio.async_sessionmaker(
    _test_engine, class_=sqlalchemy.ext.asyncio.AsyncSession, expire_on_commit=False
)


async def override_get_db():
    async with _test_session() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_db():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_trade():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/trades",
            json={
                "asset": "Bitcoin",
                "symbol": "BTC",
                "market": "crypto",
                "direction": "LONG",
                "price_open": 85000.0,
                "quantity": 0.01,
                "cost": 850.0,
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["asset"] == "Bitcoin"
    assert data["status"] == "open"
    assert data["direction"] == "LONG"


@pytest.mark.asyncio
async def test_list_trades():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/trades",
            json={
                "asset": "Bitcoin",
                "symbol": "BTC",
                "market": "crypto",
                "direction": "LONG",
                "price_open": 85000.0,
                "quantity": 0.01,
                "cost": 850.0,
            },
        )
        response = await client.get("/api/trades")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_close_trade():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_resp = await client.post(
            "/api/trades",
            json={
                "asset": "Bitcoin",
                "symbol": "BTC",
                "market": "crypto",
                "direction": "LONG",
                "price_open": 85000.0,
                "quantity": 0.01,
                "cost": 850.0,
            },
        )
        trade_id = create_resp.json()["id"]
        response = await client.patch(
            f"/api/trades/{trade_id}/close",
            json={"price_close": 90000.0},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "closed"
    assert data["price_close"] == 90000.0
    assert data["pnl"] == 50.0


@pytest.mark.asyncio
async def test_portfolio_summary():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/portfolio")
    assert response.status_code == 200
    data = response.json()
    assert "initial_capital" in data
    assert "cash" in data
    assert "total_pnl" in data