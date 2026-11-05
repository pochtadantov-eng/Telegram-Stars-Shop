from decimal import ROUND_CEILING, Decimal

CENT = Decimal("0.01")


def stars_price(qty: int, price_per_star: Decimal) -> Decimal:
    return (Decimal(qty) * price_per_star).quantize(CENT, rounding=ROUND_CEILING)


def ton_price(amount: Decimal, rate_rub: Decimal, markup_percent: Decimal = Decimal(0)) -> Decimal:
    rate = rate_rub * (Decimal(1) + markup_percent / Decimal(100))
    return (amount * rate).quantize(CENT, rounding=ROUND_CEILING)


def fmt_rub(v: Decimal) -> str:
    s = f"{v:,.2f}".replace(",", " ")
    return s[:-3] if s.endswith(".00") else s.replace(".", ",")


def to_crypto(rub: Decimal, rate_rub: Decimal, places: int) -> Decimal:
    """Сумма в монете (USDT/TON) по курсу монета->₽, с округлением вверх."""
    q = Decimal(1).scaleb(-places)
    return (rub / rate_rub).quantize(q, rounding=ROUND_CEILING)
