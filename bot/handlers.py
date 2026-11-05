import logging
import re
import time
from decimal import Decimal, InvalidOperation

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from . import keyboards as K
from .config import Config
from .db import DB
from .pricing import fmt_rub, stars_price, to_crypto, ton_price
from .rates import ton_rub, usdt_rub
from .ui import show

log = logging.getLogger(__name__)
ORDER_TTL = 30 * 60
TON_ADDR = re.compile(r"^[A-Za-z0-9_-]{48}$")
USERNAME = re.compile(r"^@?[A-Za-z][A-Za-z0-9_]{4,31}$")


class S(StatesGroup):
    stars_qty = State()
    stars_target = State()
    ton_qty = State()
    ton_wallet = State()


def build(cfg: Config, db: DB) -> Router:
    r = Router()

    def home_text():
        return (
            "<b>Добро пожаловать!</b>\n\n"
            f"⭐ Telegram Stars — <b>{fmt_rub(cfg.star_price)} ₽</b> за 1 звезду\n"
            "💎 TON — по актуальному рыночному курсу\n\n"
            "Выбери, что хочешь купить 👇"
        )

    # ---------- меню ----------
    @r.message(CommandStart())
    async def start(m: Message, command: CommandObject, state: FSMContext):
        await state.clear()
        ref = int(command.args[4:]) if command.args and command.args.startswith("ref_") and command.args[4:].isdigit() else None
        await db.upsert_user(m.from_user.id, m.from_user.username, ref)
        await show(m, "home", home_text(), K.main(cfg))

    @r.callback_query(F.data == "menu")
    async def menu(c: CallbackQuery, state: FSMContext):
        await state.clear()
        await c.answer()
        await show(c, "home", home_text(), K.main(cfg))

    # ---------- звёзды ----------
    @r.callback_query(F.data == "stars")
    async def stars(c: CallbackQuery, state: FSMContext):
        await state.clear()
        await c.answer()
        await show(c, "stars", (
            "<b>⭐ Telegram Stars</b>\n\n"
            f"Цена: <b>{fmt_rub(cfg.star_price)} ₽</b> за 1 звезду\n"
            f"Минимум: {cfg.min_stars} ⭐\n\nВыбери пакет или введи своё количество."
        ), K.stars_menu(cfg))

    async def stars_qty_chosen(target, state: FSMContext, qty: int):
        await state.update_data(qty=qty)
        await show(target, "stars", (
            f"<b>⭐ {qty} звёзд</b> — {fmt_rub(stars_price(qty, cfg.star_price))} ₽\n\n"
            "Кому отправить звёзды?"
        ), K.recipient())

    @r.callback_query(F.data.regexp(r"^s:\d+$"))
    async def stars_pick(c: CallbackQuery, state: FSMContext):
        await c.answer()
        await stars_qty_chosen(c, state, int(c.data[2:]))

    @r.callback_query(F.data == "s:custom")
    async def stars_custom(c: CallbackQuery, state: FSMContext):
        await c.answer()
        await state.set_state(S.stars_qty)
        await show(c, "stars", f"✏️ Введи количество звёзд числом ({cfg.min_stars}–{cfg.max_stars}):", K.back("stars"))

    @r.message(S.stars_qty)
    async def stars_qty_input(m: Message, state: FSMContext):
        t = (m.text or "").strip()
        if not t.isdigit() or not cfg.min_stars <= int(t) <= cfg.max_stars:
            return await m.answer(f"Нужно целое число от {cfg.min_stars} до {cfg.max_stars}.")
        await state.set_state(None)
        await stars_qty_chosen(m, state, int(t))

    async def crypto_rates() -> dict[str, Decimal]:
        """Курсы монет->₽ для включённых способов (недоступные пропускаются)."""
        out = {}
        for cur, enabled, fn in (("USDT", cfg.pay_crypto_usdt, usdt_rub), ("TON", cfg.pay_crypto_ton, ton_rub)):
            if enabled:
                try:
                    out[cur] = await fn()
                except Exception:  # noqa: BLE001
                    log.warning("no rate for %s", cur)
        return out

    PLACES = {"USDT": 2, "TON": 3}

    async def make_stars_order(target, state: FSMContext, user, username: str):
        """После выбора получателя — выбор способа оплаты (рубли или крипта)."""
        data = await state.get_data()
        qty = data["qty"]
        rub = stars_price(qty, cfg.star_price)
        await state.update_data(target=username)
        opts = [("RUB", f"💳 Рубли · {fmt_rub(rub)} ₽")]
        for cur, rate in (await crypto_rates()).items():
            opts.append((cur, f"{'💵' if cur == 'USDT' else '💎'} {cur} · {to_crypto(rub, rate, PLACES[cur])}"))
        await show(target, "stars", (
            f"<b>⭐ {qty} звёзд</b> для {username}\n\nВыбери способ оплаты:"
        ), K.pay_method(opts))

    @r.callback_query(F.data.regexp(r"^sp:(RUB|USDT|TON)$"))
    async def stars_pay(c: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        if "qty" not in data or "target" not in data:
            await c.answer("Сессия устарела, начни заново", show_alert=True)
            return await show(c, "home", home_text(), K.main(cfg))
        cur = c.data[3:]
        rub = stars_price(data["qty"], cfg.star_price)
        amt, rate = rub, None
        if cur != "RUB":
            rate = (await crypto_rates()).get(cur)
            if rate is None:
                return await c.answer("Этот способ сейчас недоступен", show_alert=True)
            amt = to_crypto(rub, rate, PLACES[cur])
        await c.answer()
        oid = await db.create_order(c.from_user.id, "stars", data["qty"], data["target"], rub, rate, cur, amt)
        await state.clear()
        await show_order(c, oid)

    @r.callback_query(F.data == "s_me")
    async def stars_me(c: CallbackQuery, state: FSMContext):
        if not c.from_user.username:
            await c.answer("У тебя нет @username — введи его вручную", show_alert=True)
            return await stars_other(c, state)
        await c.answer()
        await make_stars_order(c, state, c.from_user, "@" + c.from_user.username)

    @r.callback_query(F.data == "s_other")
    async def stars_other(c: CallbackQuery, state: FSMContext):
        await c.answer()
        await state.set_state(S.stars_target)
        await show(c, "stars", "Отправь @username получателя звёзд:", K.back("stars"))

    @r.message(S.stars_target)
    async def stars_target_input(m: Message, state: FSMContext):
        t = (m.text or "").strip()
        if not USERNAME.match(t):
            return await m.answer("Не похоже на username. Пример: <code>@durov</code>", parse_mode="HTML")
        await make_stars_order(m, state, m.from_user, "@" + t.lstrip("@"))

    # ---------- TON ----------
    async def rate_or_fail(target):
        try:
            return await ton_rub()
        except Exception:  # noqa: BLE001
            text = "Не удалось получить курс TON. Попробуй через минуту."
            if isinstance(target, CallbackQuery):
                await target.answer(text, show_alert=True)
            else:
                await target.answer(text)
            return None

    @r.callback_query(F.data == "ton")
    async def ton(c: CallbackQuery, state: FSMContext):
        await state.clear()
        rate = await rate_or_fail(c)
        if rate is None:
            return
        await c.answer()
        eff = rate * (1 + cfg.ton_markup / 100)
        await show(c, "ton", (
            "<b>💎 TON</b>\n\n"
            f"Актуальный курс: <b>1 TON = {fmt_rub(eff.quantize(Decimal('0.01')))} ₽</b>\n"
            f"Минимум: {cfg.min_ton} TON\n\nВыбери количество или введи своё."
        ), K.ton_menu(cfg, rate))

    async def ton_qty_chosen(target, state: FSMContext, qty: Decimal):
        rate = await rate_or_fail(target)
        if rate is None:
            return
        await state.update_data(qty=str(qty))
        await state.set_state(S.ton_wallet)
        rub = ton_price(qty, rate, cfg.ton_markup)
        await show(target, "ton", (
            f"<b>💎 {qty.normalize():f} TON</b> — {fmt_rub(rub)} ₽\n\n"
            "Отправь адрес TON-кошелька, на который отправить монеты:"
        ), K.back("ton"))

    @r.callback_query(F.data.regexp(r"^t:\d+$"))
    async def ton_pick(c: CallbackQuery, state: FSMContext):
        await c.answer()
        await ton_qty_chosen(c, state, Decimal(c.data[2:]))

    @r.callback_query(F.data == "t:custom")
    async def ton_custom(c: CallbackQuery, state: FSMContext):
        await c.answer()
        await state.set_state(S.ton_qty)
        await show(c, "ton", f"✏️ Введи количество TON (от {cfg.min_ton}):", K.back("ton"))

    @r.message(S.ton_qty)
    async def ton_qty_input(m: Message, state: FSMContext):
        try:
            q = Decimal((m.text or "").replace(",", ".").strip())
        except InvalidOperation:
            return await m.answer("Введи число, например <code>12.5</code>", parse_mode="HTML")
        if not cfg.min_ton <= q <= 100000 or q.as_tuple().exponent < -4:
            return await m.answer(f"От {cfg.min_ton} TON, не больше 4 знаков после запятой.")
        await ton_qty_chosen(m, state, q)

    @r.message(S.ton_wallet)
    async def ton_wallet_input(m: Message, state: FSMContext):
        addr = (m.text or "").strip()
        if not TON_ADDR.match(addr):
            return await m.answer("Адрес TON — 48 символов (например <code>UQ…</code>). Проверь и отправь снова.", parse_mode="HTML")
        rate = await rate_or_fail(m)
        if rate is None:
            return
        qty = Decimal((await state.get_data())["qty"])
        rub = ton_price(qty, rate, cfg.ton_markup)
        oid = await db.create_order(m.from_user.id, "ton", qty.normalize(), addr, rub, rate)
        await state.clear()
        await show_order(m, oid)

    # ---------- заказ и оплата ----------
    def order_text(o) -> str:
        pay_cur = o["pay_cur"]
        if o["kind"] == "stars":
            what, to = f"⭐ {o['qty']} звёзд", f"Получатель: {o['target']}"
            if pay_cur != "RUB":
                to += f"\nКурс зафиксирован: 1 {pay_cur} = {fmt_rub(Decimal(o['rate']).quantize(Decimal('0.01')))} ₽"
        else:
            what = f"💎 {Decimal(o['qty']).normalize():f} TON"
            to = f"Кошелёк: <code>{o['target']}</code>\nКурс зафиксирован: {fmt_rub(Decimal(o['rate']).quantize(Decimal('0.01')))} ₽"
        if pay_cur == "RUB":
            due = f"{fmt_rub(Decimal(o['rub']))} ₽"
            details = cfg.pay_details_stars if o["kind"] == "stars" else cfg.pay_details_ton
        else:
            due = f"{o['pay_amt']} {pay_cur} (≈ {fmt_rub(Decimal(o['rub']))} ₽)"
            details = cfg.pay_crypto_usdt if pay_cur == "USDT" else cfg.pay_crypto_ton
        return (
            f"<b>Заказ #{o['id']}</b>\n\n{what}\n{to}\n\n"
            f"К оплате: <b>{due}</b>\n\n{details}\n\n"
            "После перевода нажми «Я оплатил». Заказ действует 30 минут."
        )

    async def show_order(target, oid: int):
        o = await db.order(oid)
        await show(target, "order", order_text(o), K.order_kb(oid))

    @r.callback_query(F.data.startswith("cancel:"))
    async def cancel(c: CallbackQuery):
        await db.set_status(int(c.data[7:]), "cancelled", ("new",))
        await c.answer("Заказ отменён")
        await show(c, "home", home_text(), K.main(cfg))

    @r.callback_query(F.data.startswith("paid:"))
    async def paid(c: CallbackQuery, bot: Bot):
        o = await db.order(int(c.data[5:]))
        if not o or o["user_id"] != c.from_user.id:
            return await c.answer("Заказ не найден", show_alert=True)
        if time.time() - o["created"] > ORDER_TTL and o["status"] == "new":
            await db.set_status(o["id"], "cancelled", ("new",))
            return await c.answer("Заказ истёк. Оформи новый.", show_alert=True)
        if not await db.set_status(o["id"], "review", ("new",)):
            return await c.answer("Заказ уже в обработке")
        await c.answer("Принято!")
        await show(c, "order", (
            f"<b>Заказ #{o['id']}</b>\n\n⏳ Проверяем оплату. Обычно это занимает несколько минут — "
            "я напишу, как только всё будет готово."
        ), K.kb([K.cb("‹ Меню", "menu")]))
        who = f"@{c.from_user.username}" if c.from_user.username else c.from_user.full_name
        for admin in cfg.admin_ids:
            try:
                await bot.send_message(admin, f"🆕 Оплата заказа\n\n{order_text(o)}\n\nПокупатель: {who} (<code>{c.from_user.id}</code>)",
                                       parse_mode="HTML", reply_markup=K.admin_kb(o["id"]))
            except Exception as e:  # noqa: BLE001
                log.warning("admin notify failed: %s", e)

    @r.callback_query(F.data.startswith("adm:"))
    async def admin_action(c: CallbackQuery, bot: Bot):
        if c.from_user.id not in cfg.admin_ids:
            return await c.answer("Нет доступа", show_alert=True)
        _, action, oid = c.data.split(":")
        o = await db.order(int(oid))
        status = "done" if action == "done" else "rejected"
        if not o or not await db.set_status(o["id"], status, ("review", "new")):
            return await c.answer("Уже обработан", show_alert=True)
        mark = "✅ Выдано" if status == "done" else "❌ Отклонено"
        await c.message.edit_text(c.message.html_text + f"\n\n<b>{mark}</b>", parse_mode="HTML")
        msg = (f"✅ Заказ #{o['id']} выполнен! Спасибо за покупку 💜" if status == "done"
               else f"❌ Заказ #{o['id']} отклонён — оплата не найдена. Напиши в поддержку.")
        try:
            await bot.send_message(o["user_id"], msg, reply_markup=K.kb([K.cb("🏠 В меню", "menu")]))
        except Exception as e:  # noqa: BLE001
            log.warning("user notify failed: %s", e)
        await c.answer(mark)

    @r.message(Command("orders"))
    async def orders(m: Message):
        if m.from_user.id not in cfg.admin_ids:
            return
        rows = await db.review_orders()
        if not rows:
            return await m.answer("Нет заказов на проверке.")
        for o in rows:
            await m.answer(order_text(o), parse_mode="HTML", reply_markup=K.admin_kb(o["id"]))

    # ---------- кабинет и рефералка ----------
    @r.callback_query(F.data == "profile")
    async def profile(c: CallbackQuery):
        await c.answer()
        st = await db.stats(c.from_user.id)
        await show(c, "profile", (
            "<b>👤 Кабинет</b>\n\n"
            f"Твой ID: <code>{c.from_user.id}</code>\n"
            f"Выполнено заказов: {st['orders']}\n"
            f"Потрачено: {fmt_rub(st['spent'])} ₽\n"
            f"Приглашено друзей: {st['invited']}"
        ), K.back())

    @r.callback_query(F.data == "invite")
    async def invite(c: CallbackQuery, bot: Bot):
        await c.answer()
        me = await bot.me()
        link = f"https://t.me/{me.username}?start=ref_{c.from_user.id}"
        st = await db.stats(c.from_user.id)
        bonus = st["ref_turnover"] * cfg.ref_percent / 100
        await show(c, "invite", (
            "<b>🎁 Пригласить друзей</b>\n\n"
            f"Получай <b>{cfg.ref_percent.normalize():f}%</b> с каждой покупки приглашённых.\n\n"
            f"Приглашено: {st['invited']}\nЗаработано: {fmt_rub(bonus.quantize(Decimal('0.01')))} ₽\n\n"
            f"Твоя ссылка:\n<code>{link}</code>\n\nВывод бонусов — через поддержку."
        ), K.invite_kb(link))

    return r
