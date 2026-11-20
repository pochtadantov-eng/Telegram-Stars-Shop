from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


def _ids(raw: str) -> set[int]:
    out: set[int] = set()
    for part in (raw or "").split(","):
        part = part.strip()
        if part.isdigit():
            out.add(int(part))
    return out


def _prizes(raw: str) -> list[float]:
    items: list[float] = []
    for part in (raw or "3000,2000,1000").split(","):
        part = part.strip().replace(",", ".")
        if not part:
            continue
        try:
            items.append(float(part))
        except ValueError:
            continue
    return items or [3000.0, 2000.0, 1000.0]


@dataclass
class Config:
    token: str
    admin_ids: set[int]
    brand: str
    webapp_url: str
    usdt_rate: float
    ton_rate: float
    min_usdt: float
    min_ton: float
    ref_bonus: float
    delay_compensation: float
    order_cooldown_sec: int
    order_sla_sec: int
    support_url: str
    weekly_prizes: list[float] = field(default_factory=list)
    db_path: str = "data/exchange.db"
    port: int = 8080

    @property
    def brand_title(self) -> str:
        return f"{self.brand} | Exchange"


def load() -> Config:
    load_dotenv()
    # Render/мобильный ввод часто портит секреты (пробелы, кавычки, переносы)
    token = (os.getenv("BOT_TOKEN") or "").strip()
    token = token.strip("\"'").replace(" ", "").replace("\n", "").replace("\r", "")
    token = token.replace("\u00a0", "").replace("\u200b", "")
    if not token:
        raise SystemExit("BOT_TOKEN is required")
    if ":" not in token or not token.split(":", 1)[0].isdigit():
        raise SystemExit(
            "BOT_TOKEN выглядит неверно. Нужен вид 123456:AA…. "
            "Проверьте Environment на хостинге (без пробелов и кавычек)."
        )
    return Config(
        token=token,
        admin_ids=_ids(os.getenv("ADMIN_IDS", "")),
        brand=os.getenv("BRAND", "SwiftEx").strip() or "SwiftEx",
        webapp_url=os.getenv("WEBAPP_URL", "").strip().rstrip("/"),
        usdt_rate=float(os.getenv("USDT_RATE_RUB", "96")),
        ton_rate=float(os.getenv("TON_RATE_RUB", "550")),
        min_usdt=float(os.getenv("MIN_USDT", "32")),
        min_ton=float(os.getenv("MIN_TON", "1")),
        ref_bonus=float(os.getenv("REF_BONUS_RUB", "50")),
        delay_compensation=float(os.getenv("DELAY_COMPENSATION_RUB", "50")),
        order_cooldown_sec=int(os.getenv("ORDER_COOLDOWN_SEC", "900")),
        order_sla_sec=int(os.getenv("ORDER_SLA_SEC", "900")),
        support_url=os.getenv("SUPPORT_URL", "https://t.me/").strip(),
        weekly_prizes=_prizes(os.getenv("WEEKLY_PRIZES", "3000,2000,1000")),
        db_path=os.getenv("DB_PATH", "data/exchange.db"),
        port=int(os.getenv("PORT", "8080")),
    )
