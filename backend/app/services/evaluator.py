"""
Background evaluation trigger.
Called when a trade is opened to start an async trader evaluation.
"""

import logging
import os
import re
import subprocess

EVAL_PYTHON = os.path.expanduser("~/trading-crew/.venv/bin/python")
EVAL_SCRIPT = os.path.expanduser("~/trading-crew/evaluate.py")

VALID_DIRECTIONS = {"LONG", "SHORT"}
VALID_MARKETS = {"stocks", "crypto", "forex", "commodities", "etf", "index"}
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.=^/]+$", re.ASCII)
ASSET_PATTERN = re.compile(r"^[A-Za-z0-9\s.\-&,/]+$", re.ASCII)

logger = logging.getLogger(__name__)

_EVAL_LOCKS: set[str] = set()


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


async def trigger_evaluation(symbol: str, asset: str, direction: str, market: str):
    err = _validate_params(symbol, asset, direction, market)
    if err:
        logger.warning("Evaluation rejected: %s", err)
        return

    lock_key = f"{symbol}_{direction}"
    if lock_key in _EVAL_LOCKS:
        logger.info("Evaluation already running for %s, skipping", lock_key)
        return
    _EVAL_LOCKS.add(lock_key)

    try:
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
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("Triggered evaluation for %s (%s %s) pid=%d", symbol, asset, direction, proc.pid)
    except Exception as e:
        logger.error("Failed to trigger evaluation for %s: %s", symbol, e)
    finally:
        _EVAL_LOCKS.discard(lock_key)
