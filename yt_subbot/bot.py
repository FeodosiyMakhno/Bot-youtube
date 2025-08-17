import asyncio, contextlib, sys
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from database import Base, engine, SessionLocal
from handlers.user import user_router
from handlers.admin import admin_router
from jobs import worker
from config import BOT_TOKEN

class DBSessionMiddleware(BaseMiddleware):
    def __init__(self, session_factory):
        super().__init__()
        self.session_factory = session_factory
    async def __call__(self, handler, event, data):
        async with self.session_factory() as session:
            data["session"] = session
            return await handler(event, data)

async def on_startup(bot: Bot):
    await bot.set_my_commands([BotCommand(command="start", description="Начать")])

async def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN is empty. Set it in .env before running.", file=sys.stderr)
        return
    # создаём таблицы (для прототипа)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(DBSessionMiddleware(SessionLocal))
    dp.include_router(user_router)
    dp.include_router(admin_router)

    worker_task = asyncio.create_task(worker(SessionLocal))
    await on_startup(bot)
    try:
        await dp.start_polling(bot)
    finally:
        worker_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker_task

if __name__ == "__main__":
    asyncio.run(main())
