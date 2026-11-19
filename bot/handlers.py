from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from .api import format_order_admin
from .config import Config
from .db import DB
from .rates import get_rates, set_rate


def build(cfg: Config, db: DB) -> Router:
    router = Router()

    def is_admin(uid: int) -> bool:
        return uid in cfg.admin_ids

    def open_kb() -> InlineKeyboardMarkup | None:
        if not cfg.webapp_url:
            return None
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Открыть обмен 💱",
                        web_app=WebAppInfo(url=cfg.webapp_url),
                    )
                ]
            ]
        )

    @router.message(CommandStart())
    async def start(message: Message, command: CommandObject) -> None:
        ref = None
        if command.args and command.args.startswith("r"):
            raw = command.args[1:]
            if raw.isdigit():
                ref = int(raw)
        await db.upsert_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            referrer_id=ref,
        )
        rates = await get_rates(cfg, db)
        text = (
            f"<b>{cfg.brand_title}</b>\n"
            f"Продайте USDT или TON быстро и безопасно.\n\n"
            f"Курс: 1 USDT = <b>{rates['USDT']:.2f} ₽</b>\n"
            f"Курс: 1 TON = <b>{rates['TON']:.2f} ₽</b>\n\n"
            f"Сети: USDT TRC20 / TON · нативная TON"
        )
        kb = open_kb()
        if kb:
            await message.answer(text, reply_markup=kb)
        else:
            await message.answer(
                text + "\n\n⚠️ WEBAPP_URL не задан — Mini App недоступна."
            )

    @router.message(Command("app"))
    async def open_app(message: Message) -> None:
        kb = open_kb()
        if not kb:
            await message.answer("WEBAPP_URL не настроен.")
            return
        await message.answer("Откройте Mini App:", reply_markup=kb)

    @router.message(Command("rate"))
    async def rate_cmd(message: Message, command: CommandObject) -> None:
        if not is_admin(message.from_user.id):
            return
        parts = (command.args or "").split()
        if len(parts) != 2:
            rates = await get_rates(cfg, db)
            await message.answer(
                "Использование: <code>/rate USDT 96</code> или <code>/rate TON 550</code>\n"
                f"Сейчас: USDT={rates['USDT']}, TON={rates['TON']}"
            )
            return
        asset, value = parts[0].upper(), parts[1]
        if asset not in ("USDT", "TON"):
            await message.answer("Актив: USDT или TON")
            return
        try:
            num = float(value.replace(",", "."))
        except ValueError:
            await message.answer("Неверное число")
            return
        await set_rate(db, asset, num)
        await message.answer(f"Курс {asset} = <b>{num:.2f} ₽</b>")

    @router.message(Command("orders"))
    async def orders_cmd(message: Message) -> None:
        if not is_admin(message.from_user.id):
            return
        pending = await db.list_pending()
        if not pending:
            await message.answer("Нет ожидающих заявок.")
            return
        for order in pending[:20]:
            user = await db.get_user(order["user_id"]) or {"id": order["user_id"]}
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Выплачено",
                            callback_data=f"ord:done:{order['id']}",
                        ),
                        InlineKeyboardButton(
                            text="❌ Отклонить",
                            callback_data=f"ord:rej:{order['id']}",
                        ),
                    ]
                ]
            )
            await message.answer(
                format_order_admin(order, user),
                reply_markup=kb,
            )

    @router.callback_query(F.data.startswith("ord:"))
    async def order_action(cq: CallbackQuery, bot: Bot) -> None:
        if not is_admin(cq.from_user.id):
            await cq.answer("Нет доступа", show_alert=True)
            return
        _, action, oid = cq.data.split(":")
        order_id = int(oid)
        status = "done" if action == "done" else "rejected"
        order = await db.set_order_status(
            order_id, status, ref_bonus=cfg.ref_bonus
        )
        if not order:
            await cq.answer("Не найдено")
            return
        if order["status"] != status and order["status"] != "pending":
            # already processed earlier path returns current
            pass
        label = "выплачена" if status == "done" else "отклонена"
        await cq.message.edit_text(cq.message.html_text + f"\n\n<b>→ {label}</b>")
        try:
            if status == "done":
                await bot.send_message(
                    order["user_id"],
                    f"✅ Заявка #{order['id']} выплачена.\n"
                    f"Сумма: <b>{order['payout']:.2f} ₽</b>",
                )
            else:
                await bot.send_message(
                    order["user_id"],
                    f"❌ Заявка #{order['id']} отклонена. Бонусы возвращены на баланс.",
                )
        except Exception:
            pass
        await cq.answer("Готово")

    return router


async def notify_admins(bot: Bot, cfg: Config, order: dict, user: dict) -> None:
    text = format_order_admin(order, user)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Выплачено",
                    callback_data=f"ord:done:{order['id']}",
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"ord:rej:{order['id']}",
                ),
            ]
        ]
    )
    for admin_id in cfg.admin_ids:
        try:
            await bot.send_message(admin_id, text, reply_markup=kb)
        except Exception:
            continue
