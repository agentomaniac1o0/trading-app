from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Setting, Trade, TraderJudgment
from app.schemas import TradeClose, TradeCreate, TraderJudgmentCreate


async def create_trade(db: AsyncSession, data: TradeCreate) -> Trade:
    trade = Trade(
        id=uuid4().hex[:8],
        date_open=datetime.utcnow().strftime("%Y-%m-%d"),
        asset=data.asset,
        symbol=data.symbol,
        market=data.market,
        direction=data.direction,
        price_open=data.price_open,
        quantity=data.quantity,
        cost=data.cost,
        stop_loss=data.stop_loss,
        status="open",
        signal_source=data.signal_source,
        notes=data.notes,
    )
    db.add(trade)
    await db.commit()
    await db.refresh(trade)
    return trade


async def get_trades(
    db: AsyncSession,
    status: str | None = None,
    market: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Trade]:
    stmt = select(Trade).order_by(Trade.date_open.desc())
    if status:
        stmt = stmt.where(Trade.status == status)
    if market:
        stmt = stmt.where(Trade.market == market)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_trade(db: AsyncSession, trade_id: str) -> Trade | None:
    result = await db.execute(select(Trade).where(Trade.id == trade_id))
    return result.scalar_one_or_none()


async def close_trade(db: AsyncSession, trade_id: str, data: TradeClose) -> Trade | None:
    trade = await get_trade(db, trade_id)
    if not trade or trade.status == "closed":
        return None

    qty_to_close = data.quantity_close if data.quantity_close else trade.quantity
    qty_to_close = min(qty_to_close, trade.quantity)

    close_date = data.date_close or datetime.utcnow().strftime("%Y-%m-%d")

    if trade.direction == "LONG":
        pnl_part = (data.price_close - trade.price_open) * qty_to_close
    else:
        pnl_part = (trade.price_open - data.price_close) * qty_to_close

    cost_part = trade.cost * (qty_to_close / trade.quantity) if trade.quantity else 0

    if qty_to_close >= trade.quantity:
        trade.status = "closed"
        trade.date_close = close_date
        trade.price_close = data.price_close
        trade.pnl = pnl_part
        trade.pnl_pct = (pnl_part / trade.cost) * 100 if trade.cost else 0
    else:
        trade.quantity -= qty_to_close
        trade.cost -= cost_part

        closed_trade = Trade(
            id=uuid4().hex[:8],
            date_open=trade.date_open,
            asset=trade.asset,
            symbol=trade.symbol,
            market=trade.market,
            direction=trade.direction,
            price_open=trade.price_open,
            quantity=qty_to_close,
            cost=cost_part,
            stop_loss=trade.stop_loss,
            status="closed",
            date_close=close_date,
            price_close=data.price_close,
            pnl=pnl_part,
            pnl_pct=(pnl_part / cost_part) * 100 if cost_part else 0,
            signal_source=trade.signal_source,
            notes=trade.notes,
        )
        db.add(closed_trade)

    trade.updated_at = datetime.utcnow().isoformat()
    await db.commit()
    await db.refresh(trade)
    return trade


async def get_open_position_cost(db: AsyncSession) -> float:
    result = await db.execute(
        select(Trade).where(Trade.status == "open")
    )
    open_trades = list(result.scalars().all())
    return sum(t.cost for t in open_trades)


async def get_closed_pnl(db: AsyncSession) -> float:
    result = await db.execute(
        select(Trade).where(Trade.status == "closed")
    )
    closed_trades = list(result.scalars().all())
    return sum(t.pnl or 0 for t in closed_trades)


async def count_trades(db: AsyncSession, status: str | None = None) -> int:
    stmt = select(Trade)
    if status:
        stmt = stmt.where(Trade.status == status)
    result = await db.execute(stmt)
    return len(list(result.scalars().all()))


async def count_winning_trades(db: AsyncSession) -> int:
    result = await db.execute(
        select(Trade).where(Trade.status == "closed", Trade.pnl > 0)
    )
    return len(list(result.scalars().all()))


async def get_setting(db: AsyncSession, key: str) -> str | None:
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    return setting.value if setting else None


async def set_setting(db: AsyncSession, key: str, value: str) -> Setting:
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        setting = Setting(key=key, value=value)
        db.add(setting)
    await db.commit()
    await db.refresh(setting)
    return setting


async def create_judgments(
    db: AsyncSession, data: list[TraderJudgmentCreate]
) -> list[TraderJudgment]:
    symbol = data[0].symbol
    await delete_judgments(db, symbol, source="auto")
    records = []
    for d in data:
        j = TraderJudgment(
            id=uuid4().hex[:8],
            symbol=d.symbol,
            direction=d.direction,
            trader=d.trader,
            judgment=d.judgment,
            reason=d.reason,
            source="auto",
        )
        db.add(j)
        records.append(j)
    await db.commit()
    return records


async def get_judgments(db: AsyncSession, symbol: str) -> list[TraderJudgment]:
    """Get latest judgments for a symbol (newest per trader)."""
    result = await db.execute(
        select(TraderJudgment)
        .where(TraderJudgment.symbol == symbol)
        .order_by(TraderJudgment.created_at.desc())
    )
    all_judgments = list(result.scalars().all())
    seen = set()
    latest = []
    for j in all_judgments:
        if j.trader not in seen:
            seen.add(j.trader)
            latest.append(j)
    return latest


async def delete_judgments(db: AsyncSession, symbol: str, source: str) -> int:
    result = await db.execute(
        select(TraderJudgment).where(
            TraderJudgment.symbol == symbol,
            TraderJudgment.source == source,
        )
    )
    old = list(result.scalars().all())
    for j in old:
        await db.delete(j)
    await db.commit()
    return len(old)