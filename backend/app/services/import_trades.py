import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Setting, Trade

logger = logging.getLogger(__name__)


async def import_trades(db: AsyncSession, path: str | None = None) -> dict:
    file_path = path or settings.import_trades_path
    try:
        with open(file_path) as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error("trades.json not found at %s", file_path)
        return {"imported": 0, "error": "File not found"}
    except json.JSONDecodeError:
        logger.error("Invalid JSON in %s", file_path)
        return {"imported": 0, "error": "Invalid JSON"}

    initial_capital = data.get("initial_capital", settings.initial_capital)
    cash = data.get("cash", initial_capital)

    existing = await db.execute(select(Trade))
    existing_ids = {t.id for t in existing.scalars().all()}
    trades_data = data.get("trades", [])

    imported = 0
    skipped = 0
    for t in trades_data:
        if t.get("id") in existing_ids:
            skipped += 1
            continue
        trade = Trade(
            id=t.get("id"),
            date_open=t["date_open"],
            asset=t.get("asset", ""),
            symbol=t.get("symbol", ""),
            market=t.get("market", ""),
            direction=t.get("direction", "LONG"),
            price_open=t.get("price_open", 0),
            quantity=t.get("quantity", 0),
            cost=t.get("cost", 0),
            status=t.get("status", "open"),
            date_close=t.get("date_close"),
            price_close=t.get("price_close"),
            pnl=t.get("pnl"),
            pnl_pct=t.get("pnl_pct"),
            signal_source=t.get("signal"),
            notes=t.get("notes", ""),
        )
        db.add(trade)
        imported += 1

    capital_setting = await db.execute(select(Setting).where(Setting.key == "initial_capital"))
    if not capital_setting.scalar_one_or_none():
        db.add(Setting(key="initial_capital", value=str(initial_capital)))

    cash_setting = await db.execute(select(Setting).where(Setting.key == "cash"))
    if not cash_setting.scalar_one_or_none():
        db.add(Setting(key="cash", value=str(cash)))

    await db.commit()
    logger.info("Imported %d trades, skipped %d existing", imported, skipped)
    return {"imported": imported, "skipped": skipped}