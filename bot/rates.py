import logging
import time
from decimal import Decimal

import aiohttp

log = logging.getLogger(__name__)
TTL = 60
_cache: tuple[float, Decimal] | None = None


async def _get(session: aiohttp.ClientSession, url: str, **params):
    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=8)) as r:
        r.raise_for_status()
        return await r.json()


async def _coingecko(s) -> Decimal:
    d = await _get(s, "https://api.coingecko.com/api/v3/simple/price", ids="the-open-network", vs_currencies="rub")
    return Decimal(str(d["the-open-network"]["rub"]))


async def _binance(s) -> Decimal:
    ton = await _get(s, "https://api.binance.com/api/v3/ticker/price", symbol="TONUSDT")
    usdt = await _get(s, "https://api.binance.com/api/v3/ticker/price", symbol="USDTRUB")
    return Decimal(ton["price"]) * Decimal(usdt["price"])


async def ton_rub() -> Decimal:
    """Актуальный курс TON/RUB (кэш 60 с, два источника, при сбое — последнее значение)."""
    global _cache
    if _cache and time.monotonic() - _cache[0] < TTL:
        return _cache[1]
    async with aiohttp.ClientSession() as s:
        for src in (_coingecko, _binance):
            try:
                rate = await src(s)
                _cache = (time.monotonic(), rate)
                return rate
            except Exception as e:  # noqa: BLE001
                log.warning("rate source %s failed: %s", src.__name__, e)
    if _cache:
        return _cache[1]
    raise RuntimeError("TON rate unavailable")
