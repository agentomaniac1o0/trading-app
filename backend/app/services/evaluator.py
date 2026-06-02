"""
Background evaluation trigger.
Called when a trade is opened to start an async trader evaluation.
"""

import logging
import os
import re
import subprocess
import time

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

    try:
        os.makedirs(EVAL_LOG_DIR, exist_ok=True)
        err_fh = open(EVAL_LOG_FILE, "a")
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
        logger.info("Triggered evaluation for %s (%s %s) pid=%d", symbol, asset, direction, proc.pid)
    except Exception as e:
        logger.error("Failed to trigger evaluation for %s: %s", symbol, e)
        _EVAL_LOCKS.pop(lock_key, None)
