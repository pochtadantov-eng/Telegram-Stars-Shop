from decimal import Decimal

from aiogram.types import InlineKeyboardButton as B, InlineKeyboardMarkup

from .pricing import fmt_rub, stars_price, ton_price


def kb(*rows) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[list(r) for r in rows])


def cb(text, data):
    return B(text=text, callback_data=data)


def main(cfg):
    return kb(
        [cb("⭐ Звёзды", "stars"), cb("💎 TON", "ton")],
        [cb("👤 Кабинет", "profile"), cb("🎁 Пригласить друзей", "invite")],
        [B(text="💬 Отзывы", url=cfg.reviews_url), B(text="🛟 Поддержка", url=cfg.support_url)],
    )


def back(to="menu"):
    return kb([cb("‹ Назад", to)])


STAR_PRESETS = (50, 100, 250, 500, 1000, 2500)
TON_PRESETS = (1, 5, 10, 25, 50, 100)


def stars_menu(cfg):
    rows, row = [], []
    for n in STAR_PRESETS:
        row.append(cb(f"{n} ⭐ · {fmt_rub(stars_price(n, cfg.star_price))} ₽", f"s:{n}"))
        if len(row) == 2:
            rows.append(row); row = []
    rows += [[cb("✏️ Другое количество", "s:custom")], [cb("‹ Назад", "menu")]]
    return kb(*rows)


def ton_menu(cfg, rate: Decimal):
    rows, row = [], []
    for n in TON_PRESETS:
        row.append(cb(f"{n} TON · {fmt_rub(ton_price(Decimal(n), rate, cfg.ton_markup))} ₽", f"t:{n}"))
        if len(row) == 2:
            rows.append(row); row = []
    rows += [[cb("✏️ Другое количество", "t:custom")], [cb("‹ Назад", "menu")]]
    return kb(*rows)


def recipient():
    return kb([cb("🙋 Себе", "s_me"), cb("🎯 Другому", "s_other")], [cb("‹ Назад", "stars")])


def order_kb(oid: int):
    return kb([cb("✅ Я оплатил", f"paid:{oid}")], [cb("✖️ Отменить", f"cancel:{oid}"), cb("‹ Меню", "menu")])


def admin_kb(oid: int):
    return kb([cb("✅ Выдано", f"adm:done:{oid}"), cb("❌ Отклонить", f"adm:rej:{oid}")])


def invite_kb(link: str):
    from urllib.parse import quote
    share = f"https://t.me/share/url?url={quote(link)}&text={quote('Звёзды по 1.1 ₽ и TON по рыночному курсу 🚀')}"
    return kb([B(text="📤 Поделиться", url=share)], [cb("‹ Назад", "menu")])
