from __future__ import annotations

from .config import Config
from .db import DB


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


def week_start_ts(now: float | None = None) -> float:
    import time
    from datetime import datetime, timezone, timedelta

    # Неделя с понедельника 00:00 Europe/Moscow (UTC+3)
    tz = timezone(timedelta(hours=3))
    dt = datetime.fromtimestamp(now or time.time(), tz=tz)
    monday = dt - timedelta(days=dt.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return monday.timestamp()


def week_ends_in(now: float | None = None) -> int:
    import time
    from datetime import datetime, timezone, timedelta

    tz = timezone(timedelta(hours=3))
    dt = datetime.fromtimestamp(now or time.time(), tz=tz)
    monday = dt - timedelta(days=dt.weekday())
    next_monday = (monday + timedelta(days=7)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return max(0, int(next_monday.timestamp() - dt.timestamp()))
