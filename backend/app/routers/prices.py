from fastapi import APIRouter, HTTPException

from app.schemas import PriceResponse
from app.services.price_engine import get_price

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/{symbol}", response_model=PriceResponse)
async def get_symbol_price(symbol: str):
    price_data = await get_price(symbol.upper())
    if not price_data:
        raise HTTPException(status_code=404, detail=f"Price not found for {symbol}")
    return PriceResponse(**price_data)