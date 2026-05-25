from fastapi import APIRouter, HTTPException, Query

from app.schemas import AssetResult, PriceHistoryPoint, PriceResponse
from app.services.asset_db import search_assets
from app.services.price_engine import get_historical_prices, get_price

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/search", response_model=list[AssetResult])
async def search_asset(q: str = Query("", min_length=1)):
    return search_assets(q)


@router.get("/{symbol}", response_model=PriceResponse)
async def get_symbol_price(symbol: str):
    price_data = await get_price(symbol.upper())
    if not price_data:
        raise HTTPException(status_code=404, detail=f"Price not found for {symbol}")
    return PriceResponse(**price_data)


@router.get("/{symbol}/history", response_model=list[PriceHistoryPoint])
async def get_price_history(symbol: str, days: int = Query(7, ge=1, le=90)):
    data = await get_historical_prices(symbol.upper(), days=days)
    if not data:
        raise HTTPException(status_code=404, detail=f"No history for {symbol}")
    return data