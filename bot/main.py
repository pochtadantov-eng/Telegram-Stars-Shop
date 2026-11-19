from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import MenuButtonWebApp, WebAppInfo

from . import config
from .api import create_app
from .db import DB
from .handlers import build, notify_admins


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    cfg = config.load()
    Path(cfg.db_path).parent.mkdir(parents=True, exist_ok=True)

    db = DB(cfg.db_path)
    await db.init()

    bot = Bot(
        cfg.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    bot_username = ""
    try:
        me = await bot.get_me()
        bot_username = me.username or ""
    except Exception:
        logging.exception(
            "Не удалось получить профиль бота (проверьте BOT_TOKEN). "
            "HTTP/Mini App всё равно стартуют."
        )

    app = create_app(cfg, db, bot_username=bot_username)

    async def _notify(order, user):
        await notify_admins(bot, cfg, order, user)

    async def _notify_user(user_id: int, text: str):
        try:
            await bot.send_message(user_id, text)
        except Exception:
            logging.exception("notify_user failed for %s", user_id)

    app["notify_order"] = _notify
    app["notify_user"] = _notify_user

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", cfg.port)
    await site.start()
    logging.info("HTTP on :%s | bot @%s", cfg.port, bot_username or "?")

    if cfg.webapp_url and bot_username:
        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="Обмен",
                    web_app=WebAppInfo(url=cfg.webapp_url),
                )
            )
        except Exception:
            logging.exception("Failed to set menu button")

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(build(cfg, db))

    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
