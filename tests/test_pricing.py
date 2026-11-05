from decimal import Decimal as D

from bot.pricing import fmt_rub, stars_price, ton_price


def test_stars():
    assert stars_price(50, D("1.1")) == D("55.00")
    assert stars_price(333, D("1.1")) == D("366.30")


def test_ton_rounds_up_and_markup():
    assert ton_price(D("1"), D("300.123")) == D("300.13")
    assert ton_price(D("10"), D("300"), D("5")) == D("3150.00")


def test_fmt():
    assert fmt_rub(D("1234.5")) == "1 234,50"
    assert fmt_rub(D("55.00")) == "55"
