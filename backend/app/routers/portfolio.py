import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.config import settings
from app.database import get_db
from app.schemas import (
    LivePortfolioResponse,
    LivePosition,
    PortfolioJudgment,
    PortfolioReviewAsset,
    PortfolioReviewResponse,
    PortfolioSummary,
)
from app.services.evaluator import is_eval_running, trigger_evaluation
from app.services.price_engine import get_price

from app.routers.reports import _find_latest_report, _parse_portfolio_review

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def _portfolio_trade_aggregates(trades: list) -> tuple[float, float, float, float, float]:
    """Compute invested/PNL aggregates from open trades. Returns:
    (unrealized_pnl, invested_long, invested_short_cost, invested_market_long, invested_market_short)
    """
    unrealized_pnl = 0.0
    invested_long = 0.0
    invested_short_cost = 0.0
    invested_market_long = 0.0
    invested_market_short = 0.0
    for trade in trades:
        market_value = trade.price_current * trade.quantity
        if trade.direction == "LONG":
            invested_long += trade.cost
            invested_market_long += market_value
            unrealized_pnl += (trade.price_current - trade.price_open) * trade.quantity
        else:
            invested_short_cost += trade.cost
            invested_market_short += market_value
            unrealized_pnl += (trade.price_open - trade.price_current) * trade.quantity
    return unrealized_pnl, invested_long, invested_short_cost, invested_market_long, invested_market_short


def _portfolio_kpis(initial_capital: float, closed_pnl: float, unrealized_pnl: float,
                    invested_long: float, invested_short_cost: float,
                    invested_market_long: float, invested_market_short: float) -> dict:
    """Compute all portfolio KPIs from aggregates."""
    total_pnl = round(closed_pnl + unrealized_pnl, 2)
    total_pnl_pct = round((total_pnl / initial_capital * 100), 2) if initial_capital else 0
    portfolio_value = round(initial_capital + total_pnl, 2)
    cash = round(initial_capital - invested_long + invested_short_cost + closed_pnl, 2)
    short_exposure = round(invested_market_short, 2)
    net_available = round(cash - short_exposure, 2)
    invested = round(invested_long + invested_short_cost, 2)
    invested_market = round(invested_market_long - invested_market_short, 2)
    return {
        "total_pnl": total_pnl, "total_pnl_pct": total_pnl_pct,
        "portfolio_value": portfolio_value, "cash": cash,
        "short_exposure": short_exposure, "net_available": net_available,
        "invested": invested, "invested_market": invested_market,
    }


async def _enrich_trades_with_prices(trades: list) -> list:
    """Attach current price to each trade."""
    enriched = []
    for trade in trades:
        price_data = await get_price(trade.symbol)
        price_current = price_data["price"] if price_data else trade.price_open
        trade.price_current = price_current
        enriched.append(trade)
    return enriched


@router.get("", response_model=PortfolioSummary)
async def get_portfolio_summary(db: AsyncSession = Depends(get_db)):
    initial_capital_str = await crud.get_setting(db, "initial_capital")
    initial_capital = float(initial_capital_str) if initial_capital_str else settings.initial_capital
    closed_pnl = await crud.get_closed_pnl(db)
    open_trades = await crud.get_trades(db, status="open")
    open_trades = await _enrich_trades_with_prices(open_trades)

    unrealized_pnl, invested_long, invested_short_cost, invested_market_long, invested_market_short = \
        _portfolio_trade_aggregates(open_trades)
    kpis = _portfolio_kpis(initial_capital, closed_pnl, unrealized_pnl,
                           invested_long, invested_short_cost,
                           invested_market_long, invested_market_short)

    open_positions = await crud.count_trades(db, status="open")
    closed_trades = await crud.count_trades(db, status="closed")
    winning = await crud.count_winning_trades(db)
    win_rate = (winning / closed_trades * 100) if closed_trades else 0

    return PortfolioSummary(
        initial_capital=initial_capital,
        cash=kpis["cash"],
        short_exposure=kpis["short_exposure"],
        net_available=kpis["net_available"],
        invested=kpis["invested"],
        portfolio_value=kpis["portfolio_value"],
        total_pnl=kpis["total_pnl"],
        total_pnl_pct=kpis["total_pnl_pct"],
        open_positions=open_positions,
        closed_trades=closed_trades,
        win_rate=round(win_rate, 1),
    )


@router.get("/review", response_model=PortfolioReviewResponse)
async def get_portfolio_review(db: AsyncSession = Depends(get_db)):
    open_trades = await crud.get_trades(db, status="open")

    if not open_trades:
        return PortfolioReviewResponse(
            report_date=datetime.utcnow().strftime("%Y-%m-%d"),
            report_time=datetime.utcnow().strftime("%H:%M"),
            assets=[],
        )

    by_key: dict[tuple[str, str], dict] = {}
    for trade in open_trades:
        price_data = await get_price(trade.symbol)
        price_current = price_data["price"] if price_data else trade.price_open

        key = (trade.symbol, trade.direction)
        if key not in by_key:
            by_key[key] = {
                "name": trade.asset,
                "symbol": trade.symbol,
                "direction": trade.direction,
                "total_qty": 0,
                "total_cost": 0,
                "total_pnl": 0,
                "price_current": price_current,
            }
        b = by_key[key]
        b["total_qty"] += trade.quantity
        b["total_cost"] += trade.cost

        if trade.direction == "LONG":
            pnl = (price_current - trade.price_open) * trade.quantity
        else:
            pnl = (trade.price_open - price_current) * trade.quantity
        b["total_pnl"] += pnl

    judgments_by_key: dict[tuple[str, str], list[PortfolioJudgment]] = {}
    judgments_by_symbol: dict[str, list[PortfolioJudgment]] = {}
    for trade in open_trades:
        sym = trade.symbol
        if sym in judgments_by_symbol:
            continue
        db_judgments = await crud.get_judgments(db, sym)
        if db_judgments:
            judgments_by_symbol[sym] = [
                PortfolioJudgment(trader=j.trader, judgment=j.judgment, reason=j.reason)
                for j in db_judgments
            ]

    path = _find_latest_report()
    if path:
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
            parsed = _parse_portfolio_review(text)
            if parsed:
                for asset in parsed.assets:
                    key = (asset.symbol, asset.direction)
                    if key not in judgments_by_key:
                        judgments_by_key[key] = asset.judgments
        except Exception as e:
            logger.warning("Report file read failed: %s", e)

    asset_info: dict[str, tuple[str, str]] = {}
    for trade in open_trades:
        if trade.symbol not in asset_info:
            asset_info[trade.symbol] = (trade.asset, trade.market)

    for key, b in by_key.items():
        sym = b["symbol"]
        lookup = (sym, b["direction"])
        has_any = lookup in judgments_by_key or sym in judgments_by_symbol
        if not has_any and not is_eval_running(sym, b["direction"]):
            name, market = asset_info.get(sym, (b["name"], "technologie"))
            asyncio.create_task(trigger_evaluation(sym, name, b["direction"], market))

    now = datetime.utcnow()
    assets = []
    for key, b in sorted(by_key.items()):
        pnl_pct = round(b["total_pnl"] / b["total_cost"] * 100, 2) if b["total_cost"] else 0
        qty = int(b["total_qty"])
        name_clean = b["name"].replace(f" ({b['symbol']})", "")
        sym = b["symbol"]
        dir_key = (sym, b["direction"])
        j = judgments_by_key.get(dir_key) or judgments_by_symbol.get(sym, [])

        assets.append(
            PortfolioReviewAsset(
                name=name_clean,
                symbol=sym,
                direction=b["direction"],
                quantity=qty,
                live_price=round(b["price_current"], 2),
                pnl_pct=pnl_pct,
                judgments=j,
            )
        )

    return PortfolioReviewResponse(
        report_date=now.strftime("%Y-%m-%d"),
        report_time=now.strftime("%H:%M"),
        assets=assets,
    )


@router.get("/live", response_model=LivePortfolioResponse)
async def get_live_portfolio(db: AsyncSession = Depends(get_db)):
    initial_capital_str = await crud.get_setting(db, "initial_capital")
    initial_capital = float(initial_capital_str) if initial_capital_str else settings.initial_capital
    open_trades = await crud.get_trades(db, status="open")
    open_trades = await _enrich_trades_with_prices(open_trades)

    unrealized_pnl, invested_long, invested_short_cost, invested_market_long, invested_market_short = \
        _portfolio_trade_aggregates(open_trades)
    closed_pnl = await crud.get_closed_pnl(db)
    kpis = _portfolio_kpis(initial_capital, closed_pnl, unrealized_pnl,
                           invested_long, invested_short_cost,
                           invested_market_long, invested_market_short)

    positions: list[LivePosition] = []
    for trade in open_trades:
        market_value = round(trade.price_current * trade.quantity, 2)
        if trade.direction == "LONG":
            position_pnl = round((trade.price_current - trade.price_open) * trade.quantity, 2)
        else:
            position_pnl = round((trade.price_open - trade.price_current) * trade.quantity, 2)
        position_pnl_pct = round((position_pnl / trade.cost) * 100, 2) if trade.cost else 0

        positions.append(LivePosition(
            id=trade.id, symbol=trade.symbol, asset=trade.asset,
            direction=trade.direction, price_open=trade.price_open,
            quantity=trade.quantity, cost=trade.cost,
            price_current=round(trade.price_current, 2),
            market_value=market_value,
            unrealized_pnl=position_pnl,
            unrealized_pnl_pct=position_pnl_pct,
        ))

    open_positions = len(open_trades)
    closed_trades = await crud.count_trades(db, status="closed")
    winning = await crud.count_winning_trades(db)
    win_rate = round((winning / closed_trades * 100), 1) if closed_trades else 0

    return LivePortfolioResponse(
        initial_capital=initial_capital,
        cash=kpis["cash"],
        short_exposure=kpis["short_exposure"],
        net_available=kpis["net_available"],
        invested_cost=kpis["invested"],
        invested_market=kpis["invested_market"],
        portfolio_value=kpis["portfolio_value"],
        total_pnl=kpis["total_pnl"],
        total_pnl_pct=kpis["total_pnl_pct"],
        unrealized_pnl=round(unrealized_pnl, 2),
        realized_pnl=round(closed_pnl, 2),
        open_positions=open_positions,
        closed_trades=closed_trades,
        win_rate=win_rate,
        positions=positions,
    )