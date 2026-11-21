from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from app.config import settings

bot = Bot(settings.BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(m: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✨ Открыть Искры",
            web_app=WebAppInfo(url=settings.WEBAPP_URL),
        )
    ]])
    await m.answer("Играй в крестики-нолики и шахматы, собирай искры ✨", reply_markup=kb)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
