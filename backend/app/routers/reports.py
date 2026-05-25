import glob
import os
import re
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.schemas import PortfolioJudgment, PortfolioReviewAsset, PortfolioReviewResponse

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
]


def _find_latest_report() -> str | None:
    pattern = os.path.join(REPORTS_DIR, "report_*.txt")
    files = glob.glob(pattern)
    if not files:
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


def _parse_header(line: str):
    line = line.lstrip("\u2022").strip().replace("**", "")
    m = re.match(r"(.+?)\s*\((\w+)\)\s*\((\w+)\s*x(\d+)\)", line)
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
        r"\s*[–\-]\s*(Buffett|Lynch|Soros|Wood|Saylor)\s*:\s*(\w+)\s*[–\-]?\s*(.+)",
        line,
    )
    if m:
        return m.group(1).lower(), m.group(2).upper(), m.group(3).strip()
    return None


def _parse_portfolio_review(text: str) -> PortfolioReviewResponse | None:
    idx = text.find("## PORTFOLIO")
    if idx < 0:
        return None

    section = text[idx:]
    after_heading = section.split("\n", 1)[1] if "\n" in section else section
    after_heading = after_heading.strip()

    date_match = re.search(r"Trading Report[^0-9]*(\d{4}-\d{2}-\d{2})", text)
    report_date = date_match.group(1) if date_match else datetime.utcnow().strftime("%Y-%m-%d")

    lines = after_heading.strip().split("\n")
    assets: list[PortfolioReviewAsset] = []
    current_asset: dict | None = None

    for line in lines:
        if line.startswith("##"):
            break
        line = line.strip()
        if not line:
            continue
        if line.startswith("\u2022"):  # bullet
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
async def latest_portfolio_review():
    path = _find_latest_report()
    if not path:
        return None
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return _parse_portfolio_review(text)


@router.get("/market/{category}")
async def get_market_report(category: str):
    if category not in MARKET_CATEGORIES:
        raise HTTPException(status_code=404, detail=f"Unknown category: {category}")

    pattern = os.path.join(REPORTS_DIR, f"{category}_*.txt")
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if not files:
        raise HTTPException(status_code=404, detail=f"No report found for {category}")

    with open(files[0], encoding="utf-8") as f:
        content = f.read()

    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(files[0]))
    report_date = date_match.group(1) if date_match else "unknown"

    return {"category": category, "report_date": report_date, "content": content}


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
