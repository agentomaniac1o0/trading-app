import time
from datetime import datetime

import ccxt
import yfinance as yf

from app.config import settings

_crypto_exchange = None
_price_cache: dict[str, tuple[float, str, str]] = {}
_cache_ttl = settings.price_cache_ttl

CRYPTO_SYMBOLS = {
    "BTC": "BTC/USDT",
    "ETH": "ETH/USDT",
    "SOL": "SOL/USDT",
    "XRP": "XRP/USDT",
    "ADA": "ADA/USDT",
    "DOGE": "DOGE/USDT",
    "DOT": "DOT/USDT",
    "AVAX": "AVAX/USDT",
    "MATIC": "MATIC/USDT",
    "LINK": "LINK/USDT",
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
                "timestamp": datetime.utcfromtimestamp(cached_time).isoformat(),
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
                "timestamp": datetime.utcnow().isoformat(),
                "source": "kucoin",
            }
    except Exception:
        pass
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
                "timestamp": datetime.utcnow().isoformat(),
                "source": "yfinance",
            }
    except Exception:
        pass
    return None


async def get_historical_prices(symbol: str, days: int = 7) -> list[dict] | None:
    try:
        if symbol in CRYPTO_SYMBOLS:
            exchange = _get_crypto_exchange()
            pair = CRYPTO_SYMBOLS[symbol]
            since = exchange.milliseconds() - days * 86400000
            ohlcv = exchange.fetch_ohlcv(pair, "1d", since=since)
            return [
                {"date": datetime.utcfromtimestamp(c[0] / 1000).strftime("%Y-%m-%d"),
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
        return None