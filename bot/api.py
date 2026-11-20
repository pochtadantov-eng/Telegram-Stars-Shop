from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from aiohttp import web

from .auth import extract_init_data, parse_start_param, validate_init_data
from .config import Config
from .db import DB
from .rates import (
    get_rates,
    period_ends_in,
    period_start_ts,
    refresh_live_rates,
    week_ends_in,
    week_start_ts,
)

ASSETS = ("USDT", "TON")
METHODS = {
    "USDT": ("cryptobot", "trc20", "ton", "xrocket"),
    "TON": ("ton", "cryptobot", "xrocket"),
}


def _money(v: float) -> str:
    return f"{v:,.2f}".replace(",", " ").replace(".", ",")


def create_app(cfg: Config, db: DB, bot_username: str | None = None) -> web.Application:
    app = web.Application()
    app["cfg"] = cfg
    app["db"] = db
    app["bot_username"] = bot_username or ""

    async def user_from_request(request: web.Request) -> dict[str, Any]:
        init_data = extract_init_data(request)
        if not init_data:
            if request.headers.get("X-Dev-User"):
                try:
                    uid = int(request.headers["X-Dev-User"])
                except ValueError as exc:
                    raise web.HTTPUnauthorized(text="invalid user") from exc
                user = {"id": uid, "username": "dev", "first_name": "Dev"}
                return await db.upsert_user(
                    user_id=uid,
                    username="dev",
                    first_name="Dev",
                    last_name=None,
                    photo_url=None,
                    referrer_id=None,
                )
            raise web.HTTPUnauthorized(
                text="no initData — откройте Mini App из Telegram-бота"
            )

        user = validate_init_data(init_data, cfg.token)
        if not user:
            raise web.HTTPUnauthorized(
                text="invalid initData — проверьте BOT_TOKEN на Render "
                "(должен быть токен именно этого бота, без пробелов)"
            )

        start = parse_start_param(init_data)
        referrer_id = None
        if start and start.startswith("r"):
            raw = start[1:]
            if raw.isdigit():
                referrer_id = int(raw)

        return await db.upsert_user(
            user_id=int(user["id"]),
            username=user.get("username"),
            first_name=user.get("first_name"),
            last_name=user.get("last_name"),
            photo_url=user.get("photo_url"),
            referrer_id=referrer_id,
        )

    async def api_health(_: web.Request) -> web.Response:
        token_ok = bool(cfg.token) and ":" in cfg.token and " " not in cfg.token
        return web.json_response(
            {
                "ok": True,
                "bot_username": app["bot_username"],
                "token_configured": token_ok,
                "webapp_url": cfg.webapp_url or None,
            }
        )

    async def api_config(_: web.Request) -> web.Response:
        rates = await refresh_live_rates(cfg, db)
        totals = await db.totals()
        usdt_m = await db.get_setting("usdt_market")
        ton_m = await db.get_setting("ton_market")
        return web.json_response(
            {
                "brand": cfg.brand,
                "brand_title": cfg.brand_title,
                "rates": rates,
                "market": {
                    "USD": float(usdt_m) if usdt_m else rates["USDT"],
                    "USDT": float(usdt_m) if usdt_m else rates["USDT"],
                    "TON": float(ton_m) if ton_m else rates["TON"],
                },
                "min_usdt": cfg.min_usdt,
                "min_ton": cfg.min_ton,
                "ref_bonus": cfg.ref_bonus,
                "delay_compensation": cfg.delay_compensation,
                "order_cooldown_sec": cfg.order_cooldown_sec,
                "order_sla_sec": cfg.order_sla_sec,
                "support_url": cfg.support_url,
                "weekly_prizes": cfg.weekly_prizes,
                "methods": METHODS,
                "assets": list(ASSETS),
                "payout_label": "СБП И КАРТА",
                "totals": totals,
                "bot_username": app["bot_username"],
                "terms": (
                    "Обмен ручной: после создания заявки она уходит оператору. "
                    "Оператор примет заявку, сообщит куда перевести крипту, "
                    "затем выплатит рубли на СБП/карту по курсу из заявки."
                ),
            }
        )

    async def api_me(request: web.Request) -> web.Response:
        user = await user_from_request(request)
        since = week_start_ts()
        week = await db.user_week_stats(user["id"], since)
        last_at = await db.last_order_at(user["id"])
        cooldown_left = 0
        if last_at:
            cooldown_left = max(
                0, int(cfg.order_cooldown_sec - (time.time() - last_at))
            )
        uname = app["bot_username"] or "bot"
        ref_link = f"https://t.me/{uname}?start=r{user['id']}"
        return web.json_response(
            {
                "id": user["id"],
                "username": user.get("username"),
                "first_name": user.get("first_name"),
                "photo_url": user.get("photo_url"),
                "deals": user["deals"],
                "usdt": user["usdt_sold"],
                "ton": user["ton_sold"],
                "turnover": user["turnover"],
                "bonus_balance": user["bonus_balance"],
                "ref_count": user["ref_count"],
                "ref_earned": user["ref_earned"],
                "week_turnover": week["week_turnover"],
                "week_place": week["place"],
                "ref_link": ref_link,
                "cooldown_left": cooldown_left,
                "is_admin": int(user["id"]) in cfg.admin_ids,
            }
        )

    async def api_rates(_: web.Request) -> web.Response:
        rates = await refresh_live_rates(cfg, db)
        return web.json_response(
            {
                "rates": rates,
                "week_ends_in": week_ends_in(),
            }
        )

    async def api_leaderboard(request: web.Request) -> web.Response:
        user = await user_from_request(request)
        period = str(request.rel_url.query.get("period") or "week").lower()
        if period not in ("day", "week", "month"):
            period = "week"
        since = period_start_ts(period)
        board = await db.leaderboard(since, limit=50)
        me = await db.user_week_stats(user["id"], since)
        items = []
        for i, row in enumerate(board, start=1):
            prize = (
                cfg.weekly_prizes[i - 1]
                if period == "week" and i - 1 < len(cfg.weekly_prizes)
                else 0
            )
            items.append(
                {
                    "place": i,
                    "id": row["id"],
                    "username": row.get("username"),
                    "first_name": row.get("first_name"),
                    "photo_url": row.get("photo_url"),
                    "turnover": row["week_turnover"],
                    "prize": prize,
                }
            )
        return web.json_response(
            {
                "items": items,
                "me": {
                    "place": me["place"],
                    "turnover": me["week_turnover"],
                },
                "period": period,
                "week_ends_in": period_ends_in(period),
                "prizes": cfg.weekly_prizes if period == "week" else [],
            }
        )

    async def api_admin_balances(request: web.Request) -> web.Response:
        user = await user_from_request(request)
        if int(user["id"]) not in cfg.admin_ids:
            raise web.HTTPForbidden(text="admin only")
        try:
            body = await request.json()
        except Exception as exc:
            raise web.HTTPBadRequest(text="invalid json") from exc

        try:
            usdt = float(body.get("usdt", user.get("usdt_sold") or 0))
            ton = float(body.get("ton", user.get("ton_sold") or 0))
        except (TypeError, ValueError) as exc:
            raise web.HTTPBadRequest(text="usdt/ton must be numbers") from exc
        if usdt < 0 or ton < 0:
            raise web.HTTPBadRequest(text="balances must be >= 0")

        rates = await refresh_live_rates(cfg, db)
        # Оборот в ₽ для места в топе = USDT×курс + TON×курс
        turnover = usdt * float(rates["USDT"]) + ton * float(rates["TON"])
        updated = await db.set_user_balances(
            int(user["id"]),
            usdt=usdt,
            ton=ton,
            turnover=turnover,
        )
        since = week_start_ts()
        week = await db.user_week_stats(int(user["id"]), since)
        return web.json_response(
            {
                "ok": True,
                "usdt": updated.get("usdt_sold", usdt),
                "ton": updated.get("ton_sold", ton),
                "turnover": updated.get("turnover", turnover),
                "week_place": week["place"],
                "week_turnover": week["week_turnover"],
                "rates": rates,
            }
        )

    async def api_orders(request: web.Request) -> web.Response:
        user = await user_from_request(request)
        orders = await db.list_orders(user["id"])
        return web.json_response({"orders": orders})

    async def api_create_order(request: web.Request) -> web.Response:
        user = await user_from_request(request)
        try:
            body = await request.json()
        except Exception as exc:
            raise web.HTTPBadRequest(text="invalid json") from exc

        asset = str(body.get("asset", "USDT")).upper()
        method = str(body.get("method", "")).lower()
        try:
            amount = float(body.get("amount", 0))
            bonus_used = float(body.get("bonus_used", 0) or 0)
        except (TypeError, ValueError) as exc:
            raise web.HTTPBadRequest(text="invalid amount") from exc

        phone = str(body.get("phone", "")).strip()
        bank = str(body.get("bank", "")).strip()
        full_name = (str(body.get("full_name") or "").strip() or None)
        card_number = (str(body.get("card_number") or "").strip() or None)
        want_pdf = bool(body.get("want_pdf", True))

        if asset not in ASSETS:
            raise web.HTTPBadRequest(text="unknown asset")
        if method not in METHODS.get(asset, ()):
            raise web.HTTPBadRequest(text="unknown method")

        min_amount = cfg.min_usdt if asset == "USDT" else cfg.min_ton
        if amount < min_amount:
            raise web.HTTPBadRequest(text=f"minimum {min_amount}")

        if not phone or not bank:
            raise web.HTTPBadRequest(text="phone and bank required")
        if not body.get("accept_terms"):
            raise web.HTTPBadRequest(text="terms required")

        last_at = await db.last_order_at(user["id"])
        if last_at and time.time() - last_at < cfg.order_cooldown_sec:
            left = int(cfg.order_cooldown_sec - (time.time() - last_at))
            raise web.HTTPBadRequest(text=f"cooldown:{left}")

        if bonus_used < 0:
            raise web.HTTPBadRequest(text="invalid bonus")
        if bonus_used > float(user["bonus_balance"]):
            raise web.HTTPBadRequest(text="not enough bonus")

        rates = await refresh_live_rates(cfg, db)
        rate = rates[asset]
        payout = round(amount * rate + bonus_used, 2)

        order = await db.create_order(
            {
                "user_id": user["id"],
                "asset": asset,
                "method": method,
                "amount": amount,
                "rate": rate,
                "payout": payout,
                "bonus_used": bonus_used,
                "phone": phone,
                "bank": bank,
                "full_name": full_name,
                "card_number": card_number,
                "want_pdf": want_pdf,
            }
        )

        # заявка уходит админу в этого же бота; клиенту — подтверждение
        notify = app.get("notify_order")
        if notify:
            await notify(order, user)
        notify_user = app.get("notify_user")
        if notify_user:
            await notify_user(
                user["id"],
                f"📨 Заявка #{order['id']} создана и отправлена оператору.\n"
                f"{order['amount']} {order['asset']} → {_money(order['payout'])} ₽\n"
                "Ожидайте принятия.",
            )

        return web.json_response({"order": order})

    app.router.add_get("/api/health", api_health)
    app.router.add_get("/api/config", api_config)
    app.router.add_get("/api/me", api_me)
    app.router.add_get("/api/rates", api_rates)
    app.router.add_get("/api/leaderboard", api_leaderboard)
    app.router.add_post("/api/admin/balances", api_admin_balances)
    app.router.add_get("/api/orders", api_orders)
    app.router.add_post("/api/orders", api_create_order)

    # static Mini App
    dist = Path(__file__).resolve().parent.parent / "webapp" / "dist"
    if dist.exists():
        app.router.add_get("/", lambda _: web.FileResponse(dist / "index.html"))

        async def spa_fallback(request: web.Request) -> web.StreamResponse:
            path = dist / request.match_info.get("path", "")
            if path.is_file():
                return web.FileResponse(path)
            return web.FileResponse(dist / "index.html")

        app.router.add_get("/{path:.*}", spa_fallback)
    else:

        async def stub(_: web.Request) -> web.Response:
            return web.Response(
                text="Mini App build missing. Run: cd webapp && npm i && npm run build",
                content_type="text/plain",
            )

        app.router.add_get("/", stub)

    return app


def format_order_admin(order: dict[str, Any], user: dict[str, Any]) -> str:
    uname = (
        f"@{user['username']}"
        if user.get("username")
        else user.get("first_name") or user["id"]
    )
    status = order.get("status", "pending")
    status_ru = {
        "pending": "ожидает",
        "accepted": "в работе",
        "done": "успешно",
        "rejected": "отклонена",
        "cancelled": "отменена",
    }.get(status, status)
    method = order["method"]
    method_ru = {
        "cryptobot": "Crypto Bot чеком",
        "trc20": "TRC20",
        "ton": "TON",
        "xrocket": "xRocket чеком",
    }.get(method, method)
    lines = [
        f"🆕 Заявка #{order['id']} · <b>{status_ru}</b>",
        f"Клиент: {uname} (<code>{user['id']}</code>)",
        f"Отдаёт: <b>{order['amount']} {order['asset']}</b> ({method_ru})",
        f"Курс: {_money(order['rate'])} ₽",
        f"К выплате: <b>{_money(order['payout'])} ₽</b>",
        f"Бонус: {_money(order['bonus_used'])} ₽",
        f"Телефон: <code>{order['phone']}</code>",
        f"Банк: {order['bank']}",
    ]
    if order.get("full_name"):
        lines.append(f"ФИО: {order['full_name']}")
    if order.get("card_number"):
        lines.append(f"Карта: <code>{order['card_number']}</code>")
    if order.get("want_pdf"):
        lines.append("PDF-чек: да")
    if order.get("cancel_reason"):
        lines.append(f"Причина отмены: {order['cancel_reason']}")
    return "\n".join(lines)
