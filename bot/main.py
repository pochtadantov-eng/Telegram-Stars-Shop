import asyncio
import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from . import banners, config
from .db import DB
from .handlers import build


async def main():
    logging.basicConfig(level=logging.INFO)
    cfg = config.load()
    banners.ensure(cfg.brand)
    db = DB(cfg.db_path)
    await db.init()
    bot = Bot(cfg.token)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(build(cfg, db))
    await bot.set_my_commands([])
    if os.getenv("PORT"):  # хостингам с health-check (Koyeb/Render web) нужен открытый порт
        app = web.Application()
        app.router.add_get("/", lambda _: web.Response(text="ok"))
        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", int(os.environ["PORT"])).start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
