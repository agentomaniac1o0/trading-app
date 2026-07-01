import glob
import os
import re
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.schemas import PortfolioJudgment, PortfolioReviewAsset, PortfolioReviewResponse
from app.services.price_engine import get_price

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])

REPORTS_DIR = os.path.expanduser("~/trading-crew/data/reports")

MARKET_CATEGORIES = [
    "crashprophet",
    "diamondhands",
    "cryptoanalysis",
    "equities",
    "forex",
    "commodities",
    "real-estate",
    "trader-perspectives",
    "crypto-arb-weekly",
]


def _find_latest_report() -> str | None:
    pattern = os.path.join(REPORTS_DIR, "report_[0-9]*.txt")
    files = glob.glob(pattern)
    if not files:
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


def _parse_header(line: str):
    line = line.lstrip("\u2022").strip().replace("**", "")
    m = re.match(r"(.+?)\s*\(([\w=.\-]+)\)\s*(?:[–\-]\s*\w+\s*)?\((\w+)\s*(?:x)?(\d+)\b", line)
    if not m:
        return None
    name = m.group(1).strip()
    sym = m.group(2)
    direction = m.group(3).upper()
    qty = int(m.group(4))
    pm = re.search(r"\$([0-9,]+\.?[0-9]*)", line)
    pnl_m = re.search(r"([+\-][0-9.]+)%", line)
    price = float(pm.group(1).replace(",", "")) if pm else 0.0
    pnl = float(pnl_m.group(1)) if pnl_m else 0.0
    return name, sym, direction, qty, price, pnl


def _parse_judgment(line: str):
    m = re.match(
        r"\s*[–\-]\s*(Buffett|Lynch|Soros|Wood|Saylor)\s*:\s*(.+?)\s*[–\-]\s*(.*)",
        line,
    )
    if m:
        return m.group(1).lower(), m.group(2).strip().upper(), m.group(3).strip()
    return None


def _parse_portfolio_review(text: str, report_time: str | None = None) -> PortfolioReviewResponse | None:
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')

    idx = text.find("## PORTFOLIO")
    if idx < 0:
        idx = text.upper().find("PORTFOLIO_REVIEW")
        if idx < 0:
            return None

    section = text[idx:]
    after_heading = section.split("\n", 1)[1] if "\n" in section else section
    after_heading = after_heading.strip()

    date_match = re.search(r"Trading Report[^0-9]*(\d{4}-\d{2}-\d{2})", text)
    if not date_match:
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    report_date = date_match.group(1) if date_match else datetime.utcnow().strftime("%Y-%m-%d")

    lines = after_heading.strip().split("\n")
    assets: list[PortfolioReviewAsset] = []
    current_asset: dict | None = None

    for line in lines:
        if line.startswith("##") or line.startswith("<h2") or line.startswith("<p"):
            if "risikohinweis" in line.lower() or "kein anlage" in line.lower():
                break
            if "risikohinweis" not in line.lower():
                continue
        line = line.strip()
        if not line:
            continue
        if line.startswith("\u2022"):
            h = _parse_header(line)
            if h:
                current_asset = {
                    "name": h[0],
                    "sym": h[1],
                    "dir": h[2],
                    "qty": h[3],
                    "price": h[4],
                    "pnl": h[5],
                    "judgments": [],
                }
                assets.append(current_asset)
        elif current_asset is not None and (line.startswith("\u2013") or line.startswith("-")):
            j = _parse_judgment(line)
            if j:
                current_asset["judgments"].append(
                    PortfolioJudgment(trader=j[0], judgment=j[1], reason=j[2])
                )

    if not assets:
        return None

    return PortfolioReviewResponse(
        report_date=report_date,
        report_time=report_time,
        assets=[
            PortfolioReviewAsset(
                name=a["name"],
                symbol=a["sym"],
                direction=a["dir"],
                quantity=a["qty"],
                live_price=a["price"],
                pnl_pct=a["pnl"],
                judgments=a["judgments"],
            )
            for a in assets
        ],
    )



@router.get("/portfolio-review", response_model=PortfolioReviewResponse | None)
async def latest_portfolio_review(db: AsyncSession = Depends(get_db)):
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
            logger.warning("Portfolio review parse failed: %s", e)

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


@router.get("/market/{category}")
async def get_market_report(category: str):
    if category not in MARKET_CATEGORIES:
        raise HTTPException(status_code=404, detail=f"Unknown category: {category}")

    pattern = os.path.join(REPORTS_DIR, f"{category}_*.txt")
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if not files:
        raise HTTPException(status_code=404, detail=f"No report found for {category}")

    basename = os.path.basename(files[0])
    with open(files[0], encoding="utf-8") as f:
        content = f.read()

    content = re.sub(r"^```(?:html|markdown)?\s*\n", "", content)
    content = re.sub(r"\n```\s*$", "", content)

    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", basename)
    report_date = date_match.group(1) if date_match else "unknown"

    time_match = re.search(r"_(\d{2}-\d{2})\.txt$", basename)
    if not time_match:
        mtime = os.path.getmtime(files[0])
        report_time = datetime.fromtimestamp(mtime).strftime("%H:%M")
    else:
        report_time = time_match.group(1).replace("-", ":")

    return {
        "category": category,
        "report_date": report_date,
        "report_time": report_time,
        "content": content,
    }


@router.get("/market")
async def list_market_reports():
    result = {}
    for cat in MARKET_CATEGORIES:
        pattern = os.path.join(REPORTS_DIR, f"{cat}_*.txt")
        files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        result[cat] = {
            "available": len(files) > 0,
            "latest_date": os.path.basename(files[0]).split("_", 1)[1].replace(".txt", "") if files else None,
        }
    return result
