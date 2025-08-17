from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import User
from jobs import enqueue

user_router = Router()

@user_router.message(CommandStart())
async def cmd_start(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=" Подключиться", callback_data="connect")]
    ])
    await m.answer("Привет! Нажми, чтобы подключиться к YouTube Premium.", reply_markup=kb)

@user_router.callback_query(F.data == "connect")
async def on_connect(c: types.CallbackQuery):
    await c.message.answer("Введи свой email (без пароля):")
    await c.answer()

@user_router.message(F.text.contains("@"))
async def on_email(m: types.Message, session: AsyncSession):
    email = m.text.strip()
    q = select(User).where(User.tg_id == m.from_user.id)
    res = await session.execute(q)
    u = res.scalar_one_or_none()
    if not u:
        u = User(tg_id=m.from_user.id, email=email, status="new")
        session.add(u)
    else:
        u.email = email
        u.status = "new"
    await session.commit()
    await enqueue(session, kind="add_user", payload={"tg_id": m.from_user.id, "email": email})
    await m.answer("Принял заявку. Я добавлю тебя в семью и отпишусь здесь.")
