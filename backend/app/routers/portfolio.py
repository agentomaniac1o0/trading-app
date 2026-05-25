from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.config import settings
from app.database import get_db
from app.schemas import LivePortfolioResponse, LivePosition, PortfolioSummary
from app.services.price_engine import get_price

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioSummary)
async def get_portfolio_summary(db: AsyncSession = Depends(get_db)):
    initial_capital_str = await crud.get_setting(db, "initial_capital")
    initial_capital = float(initial_capital_str) if initial_capital_str else settings.initial_capital

    invested = await crud.get_open_position_cost(db)
    closed_pnl = await crud.get_closed_pnl(db)
    cash = initial_capital - invested + closed_pnl
    portfolio_value = cash + invested
    total_pnl = closed_pnl
    total_pnl_pct = (total_pnl / initial_capital * 100) if initial_capital else 0

    open_positions = await crud.count_trades(db, status="open")
    closed_trades = await crud.count_trades(db, status="closed")
    winning = await crud.count_winning_trades(db)
    win_rate = (winning / closed_trades * 100) if closed_trades else 0

    return PortfolioSummary(
        initial_capital=initial_capital,
        cash=round(cash, 2),
        invested=round(invested, 2),
        portfolio_value=round(portfolio_value, 2),
        total_pnl=round(total_pnl, 2),
        total_pnl_pct=round(total_pnl_pct, 2),
        open_positions=open_positions,
        closed_trades=closed_trades,
        win_rate=round(win_rate, 1),
    )


@router.get("/live", response_model=LivePortfolioResponse)
async def get_live_portfolio(db: AsyncSession = Depends(get_db)):
    initial_capital_str = await crud.get_setting(db, "initial_capital")
    initial_capital = float(initial_capital_str) if initial_capital_str else settings.initial_capital

    open_trades = await crud.get_trades(db, status="open")

    positions: list[LivePosition] = []
    invested_cost = 0.0
    invested_market = 0.0
    unrealized_pnl = 0.0

    for trade in open_trades:
        price_data = await get_price(trade.symbol)
        price_current = price_data["price"] if price_data else trade.price_open
        market_value = round(price_current * trade.quantity, 2)
        if trade.direction == "LONG":
            position_pnl = round((price_current - trade.price_open) * trade.quantity, 2)
        else:
            position_pnl = round((trade.price_open - price_current) * trade.quantity, 2)
        position_pnl_pct = round((position_pnl / trade.cost) * 100, 2) if trade.cost else 0

        invested_cost += trade.cost
        invested_market += market_value
        unrealized_pnl += position_pnl

        positions.append(
            LivePosition(
                id=trade.id,
                symbol=trade.symbol,
                asset=trade.asset,
                direction=trade.direction,
                price_open=trade.price_open,
                quantity=trade.quantity,
                cost=trade.cost,
                price_current=round(price_current, 2),
                market_value=market_value,
                unrealized_pnl=position_pnl,
                unrealized_pnl_pct=position_pnl_pct,
            )
        )

    closed_pnl = await crud.get_closed_pnl(db)
    cash = initial_capital - invested_cost + closed_pnl
    total_pnl = round(closed_pnl + unrealized_pnl, 2)
    total_pnl_pct = round((total_pnl / initial_capital * 100), 2) if initial_capital else 0
    portfolio_value = round(cash + invested_market, 2)

    open_positions = len(open_trades)
    closed_trades = await crud.count_trades(db, status="closed")
    winning = await crud.count_winning_trades(db)
    win_rate = round((winning / closed_trades * 100), 1) if closed_trades else 0

    return LivePortfolioResponse(
        initial_capital=initial_capital,
        cash=round(cash, 2),
        invested_cost=round(invested_cost, 2),
        invested_market=round(invested_market, 2),
        portfolio_value=portfolio_value,
        total_pnl=total_pnl,
        total_pnl_pct=total_pnl_pct,
        unrealized_pnl=round(unrealized_pnl, 2),
        realized_pnl=round(closed_pnl, 2),
        open_positions=open_positions,
        closed_trades=closed_trades,
        win_rate=win_rate,
        positions=positions,
    )