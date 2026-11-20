from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
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


class CancelOrder(StatesGroup):
    reason = State()


STATUS_RU = {
    "pending": "ожидает",
    "accepted": "в работе",
    "done": "успешно закрыта",
    "rejected": "отклонена",
    "cancelled": "отменена",
}


def kb_pending(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять",
                    callback_data=f"ord:accept:{order_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"ord:reject:{order_id}",
                ),
            ]
        ]
    )


def kb_accepted(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💚 Закрыть успешно",
                    callback_data=f"ord:done:{order_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🚫 Отменить",
                    callback_data=f"ord:cancel:{order_id}",
                ),
            ],
        ]
    )


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
            f"Продайте USDT или TON — заявка уйдёт оператору вручную.\n\n"
            f"Курс: 1 USDT = <b>{rates['USDT']:.2f} ₽</b>\n"
            f"Курс: 1 TON = <b>{rates['TON']:.2f} ₽</b>\n\n"
            f"Сети: USDT TRC20 / TON · нативная TON"
        )
        if is_admin(message.from_user.id):
            text += (
                "\n\n<b>Админ:</b> новые заявки приходят сюда.\n"
                "Команды: /orders · /rate"
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
        open_orders = await db.list_open()
        if not open_orders:
            await message.answer("Нет открытых заявок.")
            return
        for order in open_orders[:20]:
            user = await db.get_user(order["user_id"]) or {"id": order["user_id"]}
            kb = (
                kb_pending(order["id"])
                if order["status"] == "pending"
                else kb_accepted(order["id"])
            )
            await message.answer(
                format_order_admin(order, user),
                reply_markup=kb,
            )

    @router.callback_query(F.data.startswith("ord:"))
    async def order_action(
        cq: CallbackQuery, bot: Bot, state: FSMContext
    ) -> None:
        if not is_admin(cq.from_user.id):
            await cq.answer("Нет доступа", show_alert=True)
            return
        parts = cq.data.split(":")
        if len(parts) != 3:
            await cq.answer("Неверные данные")
            return
        _, action, oid = parts
        order_id = int(oid)
        before = await db.get_order(order_id)
        if not before:
            await cq.answer("Не найдено")
            return

        if action == "cancel":
            if before["status"] != "accepted":
                await cq.answer("Сначала примите заявку", show_alert=True)
                return
            await state.set_state(CancelOrder.reason)
            await state.update_data(cancel_order_id=order_id)
            await cq.message.answer(
                f"Причина отмены заявки #{order_id}?\n"
                "Напишите одним сообщением (увидит клиент)."
            )
            await cq.answer()
            return

        status_map = {
            "accept": "accepted",
            "reject": "rejected",
            "done": "done",
        }
        status = status_map.get(action)
        if not status:
            await cq.answer("Неизвестное действие")
            return

        order = await db.set_order_status(
            order_id, status, ref_bonus=cfg.ref_bonus
        )
        if not order:
            await cq.answer("Не найдено")
            return
        if order["status"] != status:
            await cq.answer(
                f"Сейчас статус: {STATUS_RU.get(order['status'], order['status'])}",
                show_alert=True,
            )
            return

        user = await db.get_user(order["user_id"]) or {"id": order["user_id"]}
        body = format_order_admin(order, user)
        if status == "accepted":
            await cq.message.edit_text(
                body + "\n\n<b>→ принята, в работе</b>",
                reply_markup=kb_accepted(order_id),
            )
            try:
                await bot.send_message(
                    order["user_id"],
                    f"✅ Заявка #{order['id']} принята оператором.\n"
                    "Ожидайте инструкции по переводу крипты.",
                )
            except Exception:
                pass
        elif status == "done":
            await cq.message.edit_text(body + "\n\n<b>→ успешно закрыта</b>")
            try:
                await bot.send_message(
                    order["user_id"],
                    f"💚 Заявка #{order['id']} успешно закрыта.\n"
                    f"Выплата: <b>{order['payout']:.2f} ₽</b>",
                )
            except Exception:
                pass
        elif status == "rejected":
            await cq.message.edit_text(body + "\n\n<b>→ отклонена</b>")
            try:
                await bot.send_message(
                    order["user_id"],
                    f"❌ Заявка #{order['id']} отклонена.\n"
                    "Бонусы (если списывались) возвращены на баланс.",
                )
            except Exception:
                pass
        await cq.answer("Готово")

    @router.message(StateFilter(CancelOrder.reason))
    async def cancel_reason(message: Message, state: FSMContext, bot: Bot) -> None:
        if not is_admin(message.from_user.id):
            return
        data = await state.get_data()
        order_id = data.get("cancel_order_id")
        await state.clear()
        if not order_id:
            await message.answer("Нет заявки для отмены.")
            return
        reason = (message.text or "").strip() or "без указания причины"
        order = await db.set_order_status(
            int(order_id),
            "cancelled",
            cancel_reason=reason,
        )
        if not order or order["status"] != "cancelled":
            await message.answer("Не удалось отменить (уже закрыта?).")
            return
        await message.answer(
            f"Заявка #{order['id']} отменена.\nПричина: {reason}"
        )
        try:
            await bot.send_message(
                order["user_id"],
                f"🚫 Заявка #{order['id']} отменена.\n"
                f"Причина: {reason}\n"
                "Бонусы (если списывались) возвращены на баланс.",
            )
        except Exception:
            pass

    return router


async def notify_admins(bot: Bot, cfg: Config, order: dict, user: dict) -> None:
    text = format_order_admin(order, user)
    text += (
        "\n\n<i>Ручной обмен: свяжитесь с клиентом, примите перевод крипты, "
        "выплатите на СБП/карту.</i>"
    )
    kb = kb_pending(order["id"])
    for admin_id in cfg.admin_ids:
        try:
            await bot.send_message(admin_id, text, reply_markup=kb)
        except Exception:
            continue
