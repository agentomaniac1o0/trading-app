from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Setting, Trade
from app.schemas import TradeClose, TradeCreate


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

    trade.status = "closed"
    trade.date_close = data.date_close or datetime.utcnow().strftime("%Y-%m-%d")
    trade.price_close = data.price_close
    trade.updated_at = datetime.utcnow().isoformat()

    if trade.direction == "LONG":
        trade.pnl = (data.price_close - trade.price_open) * trade.quantity
    else:
        trade.pnl = (trade.price_open - data.price_close) * trade.quantity
    trade.pnl_pct = (trade.pnl / trade.cost) * 100 if trade.cost else 0

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