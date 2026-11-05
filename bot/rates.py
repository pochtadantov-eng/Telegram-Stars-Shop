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


_usdt: tuple[float, Decimal] | None = None


async def usdt_rub() -> Decimal:
    """Курс USDT/RUB (кэш 60 с, Binance -> CoinGecko)."""
    global _usdt
    if _usdt and time.monotonic() - _usdt[0] < TTL:
        return _usdt[1]
    async with aiohttp.ClientSession() as s:
        for fn in (
            lambda: _get(s, "https://api.binance.com/api/v3/ticker/price", symbol="USDTRUB"),
            lambda: _get(s, "https://api.coingecko.com/api/v3/simple/price", ids="tether", vs_currencies="rub"),
        ):
            try:
                d = await fn()
                rate = Decimal(d["price"]) if "price" in d else Decimal(str(d["tether"]["rub"]))
                _usdt = (time.monotonic(), rate)
                return rate
            except Exception as e:  # noqa: BLE001
                log.warning("usdt rate failed: %s", e)
    if _usdt:
        return _usdt[1]
    raise RuntimeError("USDT rate unavailable")


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
