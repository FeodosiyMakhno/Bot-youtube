from aiogram import Router, types
from aiogram.filters import Command
from config import ADMIN_ID

admin_router = Router()

@admin_router.message(Command("ping"))
async def admin_ping(m: types.Message):
    if m.from_user.id != ADMIN_ID:
        return
    await m.answer("Admin OK")
