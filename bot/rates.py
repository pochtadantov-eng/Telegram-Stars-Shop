from __future__ import annotations

import logging
import random
import time
from datetime import datetime, timedelta, timezone

import aiohttp

from .config import Config
from .db import DB

log = logging.getLogger(__name__)

REFRESH_SEC = 30 * 60  # 30 минут
MARKUP_MIN = 13.0
MARKUP_MAX = 17.0


async def _cbr_usd_rub(session: aiohttp.ClientSession) -> float | None:
    try:
        async with session.get("https://www.cbr-xml-daily.ru/daily_json.js") as resp:
            if resp.status != 200:
                return None
            data = await resp.json(content_type=None)
            return float(data["Valute"]["USD"]["Value"])
    except Exception:
        log.exception("CBR USD failed")
        return None


async def _ton_usd(session: aiohttp.ClientSession) -> float | None:
    # Kraken TON/USD
    try:
        async with session.get(
            "https://api.kraken.com/0/public/Ticker?pair=TONUSD"
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                result = data.get("result") or {}
                for key, val in result.items():
                    if key.startswith("TON") and "c" in val:
                        return float(val["c"][0])
    except Exception:
        log.exception("Kraken TON failed")

    # CoinGecko fallback (id может меняться)
    for coin_id in ("ton-cryptocurrency", "toncoin", "the-open-network"):
        try:
            url = (
                "https://api.coingecko.com/api/v3/simple/price"
                f"?ids={coin_id}&vs_currencies=usd"
            )
            async with session.get(url) as resp:
                if resp.status != 200:
                    continue
                data = await resp.json()
                if coin_id in data and "usd" in data[coin_id]:
                    price = float(data[coin_id]["usd"])
                    if price > 0:
                        return price
        except Exception:
            continue
    return None


async def fetch_market_rates() -> dict[str, float] | None:
    """Живые курсы: USD/RUB (ЦБ) + TON/USD (Kraken) → рубли."""
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15)
        ) as session:
            usd_rub = await _cbr_usd_rub(session)
            ton_usd = await _ton_usd(session)
            if not usd_rub or usd_rub <= 0:
                return None
            usdt = usd_rub  # USDT ≈ USD
            if ton_usd and ton_usd > 0:
                ton = ton_usd * usd_rub
            else:
                # без TON — хотя бы USDT
                ton = None
            out = {"USDT": usdt}
            if ton:
                out["TON"] = ton
            return out if "TON" in out else None
    except Exception:
        log.exception("fetch_market_rates failed")
        return None


async def refresh_live_rates(cfg: Config, db: DB, *, force: bool = False) -> dict[str, float]:
    last_raw = await db.get_setting("rates_updated_at")
    last = float(last_raw) if last_raw else 0.0
    if not force and last and time.time() - last < REFRESH_SEC:
        return await get_rates(cfg, db)

    market = await fetch_market_rates()
    if not market:
        return await get_rates(cfg, db)

    usdt_m = random.uniform(MARKUP_MIN, MARKUP_MAX)
    ton_m = random.uniform(MARKUP_MIN, MARKUP_MAX)
    usdt = round(market["USDT"] + usdt_m, 2)
    ton = round(market["TON"] + ton_m, 2)
    await db.set_setting("usdt_rate", str(usdt))
    await db.set_setting("ton_rate", str(ton))
    await db.set_setting("usdt_market", str(round(market["USDT"], 4)))
    await db.set_setting("ton_market", str(round(market["TON"], 4)))
    await db.set_setting("usdt_markup", str(round(usdt_m, 2)))
    await db.set_setting("ton_markup", str(round(ton_m, 2)))
    await db.set_setting("rates_updated_at", str(time.time()))
    log.info(
        "Rates refreshed: USDT %s(+%s) TON %s(+%s)",
        usdt,
        round(usdt_m, 2),
        ton,
        round(ton_m, 2),
    )
    return {"USDT": usdt, "TON": ton}


async def get_rates(cfg: Config, db: DB) -> dict[str, float]:
    usdt = await db.get_setting("usdt_rate")
    ton = await db.get_setting("ton_rate")
    return {
        "USDT": float(usdt) if usdt else cfg.usdt_rate,
        "TON": float(ton) if ton else cfg.ton_rate,
    }


async def set_rate(db: DB, asset: str, value: float) -> None:
    key = "usdt_rate" if asset.upper() == "USDT" else "ton_rate"
    await db.set_setting(key, str(value))


def _msk_now(now: float | None = None) -> datetime:
    tz = timezone(timedelta(hours=3))
    return datetime.fromtimestamp(now or time.time(), tz=tz)


def period_start_ts(period: str, now: float | None = None) -> float:
    dt = _msk_now(now)
    p = (period or "week").lower()
    if p == "day":
        start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elif p == "month":
        start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start = dt - timedelta(days=dt.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.timestamp()


def period_ends_in(period: str, now: float | None = None) -> int:
    dt = _msk_now(now)
    p = (period or "week").lower()
    if p == "day":
        end = (dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif p == "month":
        if dt.month == 12:
            end = dt.replace(
                year=dt.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
        else:
            end = dt.replace(
                month=dt.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
    else:
        monday = dt - timedelta(days=dt.weekday())
        end = (monday + timedelta(days=7)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    return max(0, int(end.timestamp() - dt.timestamp()))


def week_start_ts(now: float | None = None) -> float:
    return period_start_ts("week", now)


def week_ends_in(now: float | None = None) -> int:
    return period_ends_in("week", now)
