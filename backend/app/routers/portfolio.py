from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.config import settings
from app.database import get_db
from app.schemas import PortfolioSummary

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioSummary)
async def get_portfolio_summary(db: AsyncSession = Depends(get_db)):
    initial_capital_str = await crud.get_setting(db, "initial_capital")
    cash_str = await crud.get_setting(db, "cash")
    initial_capital = float(initial_capital_str) if initial_capital_str else settings.initial_capital
    cash = float(cash_str) if cash_str else settings.initial_capital

    invested = await crud.get_open_position_cost(db)
    closed_pnl = await crud.get_closed_pnl(db)
    portfolio_value = cash + invested + closed_pnl
    total_pnl = portfolio_value - initial_capital
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