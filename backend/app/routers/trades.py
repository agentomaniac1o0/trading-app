from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.schemas import TradeClose, TradeCreate, TradeResponse
from app.services.evaluator import trigger_evaluation
from app.services.price_engine import get_price

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("", response_model=list[TradeResponse])
async def list_trades(
    status: str | None = Query(None, pattern="^(open|closed)$"),
    market: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    trades = await crud.get_trades(db, status=status, market=market, limit=limit, offset=offset)
    return trades


@router.post("", response_model=TradeResponse, status_code=201)
async def create_trade(data: TradeCreate, db: AsyncSession = Depends(get_db)):
    trade = await crud.create_trade(db, data)
    import asyncio
    asyncio.create_task(trigger_evaluation(trade.symbol, trade.asset, trade.direction, trade.market))
    return trade


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: str, db: AsyncSession = Depends(get_db)):
    trade = await crud.get_trade(db, trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@router.patch("/{trade_id}/close", response_model=TradeResponse)
async def close_trade(
    trade_id: str,
    data: TradeClose,
    db: AsyncSession = Depends(get_db),
):
    trade_before = await crud.get_trade(db, trade_id)
    if not trade_before or trade_before.status == "closed":
        raise HTTPException(status_code=404, detail="Trade not found or already closed")

    price_data = await get_price(trade_before.symbol)
    if price_data:
        live_price = price_data["price"]
        deviation = abs(data.price_close - live_price) / live_price if live_price else 0
        if deviation > 0.5:
            logger.warning(
                "Close price deviation for %s: submitted=%.4f live=%.4f deviation=%.1f%%",
                trade_before.symbol, data.price_close, live_price, deviation * 100,
            )

    trade = await crud.close_trade(db, trade_id, data)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found or already closed")
    return trade