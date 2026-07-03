"""
Crypto-Arb API Router – expose positions and history for Trading App frontend.
Reads JSON files written by the crypto-arb engine on VM 101.
"""
import json
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/crypto-arb", tags=["crypto-arb"])

DATA_DIR = os.path.expanduser("~/crypto-arb/data")
POSITIONS_FILE = os.path.join(DATA_DIR, "positions.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")


def _read_json(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


@router.get("/positions")
async def get_positions():
    """Get all arb positions (open + closed)."""
    return _read_json(POSITIONS_FILE)


@router.get("/positions/active")
async def get_active_positions():
    """Get only active (open) arb positions, enriched with KuCoin actual unrealised P&L."""
    positions = _read_json(POSITIONS_FILE)
    active = [p for p in positions if p.get("status") == "open"]
    
    # Enrich with KuCoin per-coin unrealised P&L
    if os.path.exists(FUNDING_FILE):
        with open(FUNDING_FILE) as f:
            funding = json.load(f)
        per_coin = funding.get("per_coin", {})
        for p in active:
            coin = p.get("coin", "")
            if coin in per_coin:
                p["kucoin_unrealised_pnl"] = per_coin[coin].get("upnl", 0)
                p["kucoin_roe_pct"] = per_coin[coin].get("roe_pct", 0)
                p["kucoin_entry"] = per_coin[coin].get("entry", p.get("entry_price", 0))
                p["kucoin_mark"] = per_coin[coin].get("mark", p.get("current_price", 0))
    
    return active


@router.get("/positions/closed")
async def get_closed_positions():
    """Get closed arb positions."""
    positions = _read_json(POSITIONS_FILE)
    return [p for p in positions if p.get("status") == "closed"]


@router.get("/history")
async def get_history():
    """Get full trade history."""
    return _read_json(HISTORY_FILE)


@router.get("/summary")
async def get_summary():
    """Get current performance summary."""
    positions = _read_json(POSITIONS_FILE)
    history = _read_json(HISTORY_FILE)

    active = [p for p in positions if p.get("status") == "open"]
    closed = [p for p in positions if p.get("status") == "closed"]

    total_invested = sum(p.get("cost", 0) for p in active)
    unrealized_pnl = sum(p.get("unrealized_pnl", 0) for p in active)

    # Realized P&L from history.json (net_pnl field)
    close_entries = [h for h in history if h.get("type") == "close"]
    total_realized_pnl = sum(h.get("net_pnl", 0) for h in close_entries)

    # Today's realized P&L
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_closes = [h for h in close_entries if h.get("timestamp", "").startswith(today_str)]
    today_realized_pnl = sum(h.get("net_pnl", 0) for h in today_closes)

    # KuCoin actuals from funding snapshot
    funding = {}
    if os.path.exists(FUNDING_FILE):
        with open(FUNDING_FILE) as f:
            funding = json.load(f)

    return {
        "active_count": len(active),
        "closed_count": len(closed),
        "total_invested": round(total_invested, 2),
        "total_realized_pnl": round(total_realized_pnl, 4),
        "unrealized_pnl": round(unrealized_pnl, 4),
        "today_pnl": round(today_realized_pnl, 4),
        "kucoin_unrealised_pnl": funding.get("unrealised_pnl_total", 0),
        "kucoin_today_realised": funding.get("today_realised_pnl", 0),
        "kucoin_total_realised": funding.get("total_realised_pnl", total_realized_pnl),
        "kucoin_total_pnl": funding.get("total_including_unrealised", 0),
        "account_equity": funding.get("account_equity", 0),
        "updated_at": datetime.now().isoformat(),
    }


# ─── Write endpoints (for crypto-arb engine on VM 101 to push data) ───

from pydantic import BaseModel


class PositionSync(BaseModel):
    positions: list[dict]


class HistorySync(BaseModel):
    entries: list[dict]


@router.post("/sync/positions")
async def sync_positions(data: PositionSync):
    """Accept position data from crypto-arb engine."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(POSITIONS_FILE, "w") as f:
        json.dump(data.positions, f, indent=2, default=str)
    return {"status": "ok", "count": len(data.positions)}


@router.post("/sync/history")
async def sync_history(data: HistorySync):
    """Accept history entries from crypto-arb engine."""
    os.makedirs(DATA_DIR, exist_ok=True)
    existing = _read_json(HISTORY_FILE)
    existing.extend(data.entries)
    with open(HISTORY_FILE, "w") as f:
        json.dump(existing, f, indent=2, default=str)
    return {"status": "ok", "count": len(existing)}


# ─── Portfolio (live KuCoin balance snapshot) ───

PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolio_snapshot.json")


class PortfolioSync(BaseModel):
    coins: list[dict]
    spot_total: float
    futures_total: float
    total_value: float
    arb_positions: int
    timestamp: str


@router.post("/sync/portfolio")
async def sync_portfolio(data: PortfolioSync):
    """Accept portfolio snapshot from crypto-arb engine on VM 101."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(data.model_dump(), f, indent=2, default=str)
    return {"status": "ok"}


@router.get("/portfolio")
async def get_portfolio():
    """Get latest portfolio snapshot from KuCoin."""
    if not os.path.exists(PORTFOLIO_FILE):
        return {"total_value": 0, "coins": [], "spot_total": 0, "futures_total": 0, "arb_positions": 0}
    with open(PORTFOLIO_FILE) as f:
        return json.load(f)


# ─── Funding P&L (from KuCoin, tracked by funding_tracker.py) ───

FUNDING_FILE = os.path.join(DATA_DIR, "funding_snapshot.json")


@router.post("/sync/funding")
async def sync_funding(data: dict):
    """Accept funding snapshot from crypto-arb engine on VM 101."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FUNDING_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)
    return {"status": "ok"}


@router.get("/funding")
async def get_funding():
    """Get latest KuCoin P&L snapshot (realised + unrealised incl. funding fees)."""
    if not os.path.exists(FUNDING_FILE):
        return {
            "account_equity": 0,
            "unrealised_pnl_total": 0,
            "today_realised_pnl": 0,
            "total_realised_pnl": 0,
            "total_including_unrealised": 0,
            "per_coin": {},
        }
    with open(FUNDING_FILE) as f:
        return json.load(f)


# ─── Activity Log (engine transparency) ───

ACTIVITY_FILE = os.path.join(DATA_DIR, "activity.jsonl")


@router.get("/activity")
async def get_activity(limit: int = 100):
    """Get recent engine activity events (scan, candidates, positions, errors)."""
    if not os.path.exists(ACTIVITY_FILE):
        return []
    with open(ACTIVITY_FILE) as f:
        lines = f.readlines()
    events = []
    for line in lines[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(events))