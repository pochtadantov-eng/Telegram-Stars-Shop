import os
from dataclasses import dataclass
from decimal import Decimal

from dotenv import load_dotenv

load_dotenv()


def _ids(raw: str) -> list[int]:
    return [int(x) for x in raw.replace(" ", "").split(",") if x]


def _pay(name: str, default: str) -> str:
    return os.getenv(name, default).replace("\\n", "\n")


@dataclass(frozen=True)
class Config:
    token: str
    admin_ids: list[int]
    brand: str
    star_price: Decimal
    min_stars: int
    max_stars: int
    ton_markup: Decimal
    min_ton: Decimal
    ref_percent: Decimal
    pay_details: str
    pay_details_stars: str
    pay_details_ton: str
    support_url: str
    reviews_url: str
    db_path: str


def load() -> Config:
    return Config(
        token=os.environ["BOT_TOKEN"],
        admin_ids=_ids(os.getenv("ADMIN_IDS", "")),
        brand=os.getenv("BRAND", "STARS SHOP"),
        star_price=Decimal(os.getenv("STAR_PRICE_RUB", "1.1")),
        min_stars=int(os.getenv("MIN_STARS", "50")),
        max_stars=int(os.getenv("MAX_STARS", "50000")),
        ton_markup=Decimal(os.getenv("TON_MARKUP_PERCENT", "0")),
        min_ton=Decimal(os.getenv("MIN_TON", "1")),
        ref_percent=Decimal(os.getenv("REF_PERCENT", "3")),
        pay_details=_pay("PAY_DETAILS", "Реквизиты не настроены"),
        pay_details_stars=_pay("PAY_DETAILS_STARS", _pay("PAY_DETAILS", "Реквизиты не настроены")),
        pay_details_ton=_pay("PAY_DETAILS_TON", _pay("PAY_DETAILS", "Реквизиты не настроены")),
        support_url=os.getenv("SUPPORT_URL", "https://t.me/telegram"),
        reviews_url=os.getenv("REVIEWS_URL", "https://t.me/telegram"),
        db_path=os.getenv("DB_PATH", "data/shop.db"),
    )
