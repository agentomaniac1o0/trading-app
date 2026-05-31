import logging
import time
from datetime import datetime, timezone

import ccxt
import yfinance as yf

from app.config import settings

logger = logging.getLogger(__name__)

_crypto_exchange = None
_price_cache: dict[str, tuple[float, str, str]] = {}
_cache_ttl = settings.price_cache_ttl

CRYPTO_SYMBOLS = {
    "BTC": "BTC/USDT",
    "ETH": "ETH/USDT",
    "BNB": "BNB/USDT",
    "XRP": "XRP/USDT",
    "SOL": "SOL/USDT",
    "TRX": "TRX/USDT",
    "DOGE": "DOGE/USDT",
    "ADA": "ADA/USDT",
    "AVAX": "AVAX/USDT",
    "DOT": "DOT/USDT",
    "LINK": "LINK/USDT",
    "LTC": "LTC/USDT",
    "ALGO": "ALGO/USDT",
    "DEXE": "DEXE/USDT",
    "HYPE": "HYPE/USDT",
    "LEO": "LEO/USDT",
    "ZEC": "ZEC/USDT",
    "XLM": "XLM/USDT",
    "XMR": "XMR/USDT",
    "WBT": "WBT/USDT",
    "BCH": "BCH/USDT",
    "TON": "TON/USDT",
    "HBAR": "HBAR/USDT",
    "M": "M/USDT",
    "SUI": "SUI/USDT",
    "SHIB": "SHIB/USDT",
    "CRO": "CRO/USDT",
    "NEAR": "NEAR/USDT",
    "XAUT": "XAUT/USDT",
    "TAO": "TAO/USDT",
    "MNT": "MNT/USDT",
    "PAXG": "PAXG/USDT",
    "UNI": "UNI/USDT",
    "OKB": "OKB/USDT",
    "ONDO": "ONDO/USDT",
    "HTX": "HTX/USDT",
    "PI": "PI/USDT",
    "BGB": "BGB/USDT",
    "SKY": "SKY/USDT",
    "ICP": "ICP/USDT",
    "PEPE": "PEPE/USDT",
    "MORPHO": "MORPHO/USDT",
    "ETC": "ETC/USDT",
    "AAVE": "AAVE/USDT",
    "WLD": "WLD/USDT",
    "RENDER": "RENDER/USDT",
    "KCS": "KCS/USDT",
    "QNT": "QNT/USDT",
    "ATOM": "ATOM/USDT",
    "POL": "POL/USDT",
    "NEXO": "NEXO/USDT",
    "KAS": "KAS/USDT",
    "LAB": "LAB/USDT",
    "JST": "JST/USDT",
    "ENA": "ENA/USDT",
    "VVV": "VVV/USDT",
    "APT": "APT/USDT",
    "FIL": "FIL/USDT",
    "GT": "GT/USDT",
    "XDC": "XDC/USDT",
    "FLR": "FLR/USDT",
    "INJ": "INJ/USDT",
    "ARB": "ARB/USDT",
    "PUMP": "PUMP/USDT",
    "BDX": "BDX/USDT",
    "FET": "FET/USDT",
    "JUP": "JUP/USDT",
    "HASH": "HASH/USDT",
    "STX": "STX/USDT",
    "IMX": "IMX/USDT",
    "OP": "OP/USDT",
    "GRT": "GRT/USDT",
    "FLOW": "FLOW/USDT",
}


def _get_crypto_exchange():
    global _crypto_exchange
    if _crypto_exchange is None:
        _crypto_exchange = ccxt.kucoin(
            {
                "apiKey": settings.kucoin_api_key,
                "secret": settings.kucoin_api_secret,
                "password": settings.kucoin_passphrase,
                "enableRateLimit": True,
            }
        )
    return _crypto_exchange


async def get_price(symbol: str) -> dict | None:
    now = time.time()
    if symbol in _price_cache:
        cached_price, cached_time, cached_source = _price_cache[symbol]
        if now - cached_time < _cache_ttl:
            return {
                "symbol": symbol,
                "price": cached_price,
                "currency": "USD",
                "timestamp": datetime.fromtimestamp(cached_time, tz=timezone.utc).isoformat(),
                "source": cached_source,
            }

    if symbol in CRYPTO_SYMBOLS:
        return await _get_crypto_price(symbol)
    return await _get_yfinance_price(symbol)


async def _get_crypto_price(symbol: str) -> dict | None:
    try:
        exchange = _get_crypto_exchange()
        pair = CRYPTO_SYMBOLS.get(symbol, f"{symbol}/USDT")
        ticker = exchange.fetch_ticker(pair)
        price = ticker.get("last")
        if price:
            now = time.time()
            _price_cache[symbol] = (price, now, "kucoin")
            return {
                "symbol": symbol,
                "price": price,
                "currency": "USD",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "kucoin",
            }
    except Exception:
        logger.warning("Kucoin price fetch failed for %s", symbol)

    try:
        yf_symbol = f"{symbol}-USD"
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period="1d")
        if not hist.empty:
            price = round(float(hist["Close"].iloc[-1]), 4)
            now = time.time()
            _price_cache[symbol] = (price, now, "yfinance")
            return {
                "symbol": symbol,
                "price": price,
                "currency": "USD",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "yfinance",
            }
    except Exception:
        logger.warning("Yfinance fallback failed for crypto %s", symbol)
    return None


async def _get_yfinance_price(symbol: str) -> dict | None:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if not hist.empty:
            price = round(hist["Close"].iloc[-1], 4)
            now = time.time()
            _price_cache[symbol] = (price, now, "yfinance")
            return {
                "symbol": symbol,
                "price": price,
                "currency": "USD",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "yfinance",
            }
    except Exception:
        logger.warning("Yfinance price fetch failed for %s", symbol)
    return None


async def get_historical_prices(symbol: str, days: int = 7) -> list[dict] | None:
    try:
        if symbol in CRYPTO_SYMBOLS:
            exchange = _get_crypto_exchange()
            pair = CRYPTO_SYMBOLS[symbol]
            since = exchange.milliseconds() - days * 86400000
            ohlcv = exchange.fetch_ohlcv(pair, "1d", since=since)
            return [
                {"date": datetime.fromtimestamp(c[0] / 1000, tz=timezone.utc).strftime("%Y-%m-%d"),
                 "price": round(c[4], 4)}
                for c in ohlcv
            ]
        else:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=f"{days}d")
            if hist.empty:
                return None
            return [
                {"date": str(idx.date()),
                 "price": round(float(row["Close"]), 4)}
                for idx, row in hist.iterrows()
            ]
    except Exception:
        logger.warning("Historical price fetch failed for %s", symbol)
        return None