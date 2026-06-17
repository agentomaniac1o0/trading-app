"""
Background evaluation trigger and report-judgment sync.
Called when a trade is opened to start an async trader evaluation.
"""
import asyncio
import logging
import os
import re
import subprocess
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.routers.reports import _find_latest_report, _parse_portfolio_review
from app.schemas import TraderJudgmentCreate

EVAL_PYTHON = os.path.expanduser("~/trading-crew/.venv/bin/python")
EVAL_SCRIPT = os.path.expanduser("~/trading-crew/evaluate.py")
EVAL_LOG_DIR = os.path.expanduser("~/trading-app/data")
EVAL_LOG_FILE = os.path.join(EVAL_LOG_DIR, "eval_errors.log")

VALID_DIRECTIONS = {"LONG", "SHORT"}
VALID_MARKETS = {"stocks", "crypto", "forex", "commodities", "etf", "index"}
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.=^/]+$", re.ASCII)
ASSET_PATTERN = re.compile(r"^[A-Za-z0-9\s.\-&,/]+$", re.ASCII)
LOCK_TIMEOUT = 600

logger = logging.getLogger(__name__)

_EVAL_LOCKS: dict[str, float] = {}


def _cleanup_locks():
    now = time.time()
    stale = [k for k, ts in _EVAL_LOCKS.items() if now - ts > LOCK_TIMEOUT]
    for k in stale:
        logger.warning("Removing stale eval lock: %s (age: %.0fs)", k, now - _EVAL_LOCKS[k])
        del _EVAL_LOCKS[k]


def _validate_params(symbol: str, asset: str, direction: str, market: str) -> str | None:
    if direction not in VALID_DIRECTIONS:
        return f"Invalid direction: {direction}"
    if market.lower() not in VALID_MARKETS:
        return f"Invalid market: {market}"
    if not SYMBOL_PATTERN.match(symbol) or len(symbol) > 20:
        return f"Invalid symbol: {symbol}"
    if not ASSET_PATTERN.match(asset) or len(asset) > 100:
        return f"Invalid asset: {asset}"
    return None


def is_eval_running(symbol: str, direction: str) -> bool:
    _cleanup_locks()
    return f"{symbol}_{direction}" in _EVAL_LOCKS


async def sync_judgments_from_report(db: AsyncSession) -> int:
    """Parse latest report and persist portfolio judgments to DB."""
    path = _find_latest_report()
    if not path:
        logger.info("No report file found for sync")
        return 0

    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        logger.warning("Cannot read report %s: %s", path, e)
        return 0

    parsed = _parse_portfolio_review(text)
    if not parsed or not parsed.assets:
        logger.info("No portfolio review assets found in %s", path)
        return 0

    total = 0
    for asset in parsed.assets:
        if not asset.judgments:
            continue
        existing = await crud.get_judgments(db, asset.symbol)
        existing_keys = {(j.trader, j.direction) for j in existing}
        new_judgments = [
            TraderJudgmentCreate(
                symbol=asset.symbol,
                direction=asset.direction,
                trader=j.trader,
                judgment=j.judgment,
                reason=j.reason,
            )
            for j in asset.judgments
            if (j.trader, asset.direction) not in existing_keys
        ]
        if new_judgments:
            await crud.create_judgments(db, new_judgments)
            total += len(new_judgments)
            logger.info(
                "Synced %d judgments for %s %s",
                len(new_judgments), asset.symbol, asset.direction,
            )

    if total:
        logger.info("Report sync complete: %d new judgments", total)
    else:
        logger.info("Report sync: no new judgments needed")
    return total


async def trigger_evaluation(symbol: str, asset: str, direction: str, market: str):
    err = _validate_params(symbol, asset, direction, market)
    if err:
        logger.warning("Evaluation rejected: %s", err)
        return

    _cleanup_locks()

    lock_key = f"{symbol}_{direction}"
    if lock_key in _EVAL_LOCKS:
        logger.info("Evaluation already running for %s, skipping", lock_key)
        return
    _EVAL_LOCKS[lock_key] = time.time()

    if not os.path.exists(EVAL_SCRIPT):
        logger.error(
            "evaluate.py not found at %s. Cannot evaluate %s (%s %s). "
            "Install evaluate.py in trading-crew or the crew will generate "
            "judgments on next scheduled run.",
            EVAL_SCRIPT, symbol, asset, direction,
        )
        _EVAL_LOCKS.pop(lock_key, None)
        return

    try:
        os.makedirs(EVAL_LOG_DIR, exist_ok=True)
        with open(EVAL_LOG_FILE, "a") as err_fh:
            proc = subprocess.Popen(
                [
                    EVAL_PYTHON,
                    EVAL_SCRIPT,
                    "--symbol", symbol,
                    "--asset", asset,
                    "--direction", direction,
                    "--market", market,
                ],
                cwd=os.path.dirname(EVAL_SCRIPT),
                stdout=err_fh,
                stderr=err_fh,
            )
        logger.info(
            "Triggered evaluation for %s (%s %s) pid=%d",
            symbol, asset, direction, proc.pid,
        )
    except Exception as e:
        logger.error("Failed to trigger evaluation for %s: %s", symbol, e)
        _EVAL_LOCKS.pop(lock_key, None)
