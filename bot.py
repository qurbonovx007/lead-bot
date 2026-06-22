import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat

from config import BOT_TOKEN, ADMIN_IDS
from handlers import router
from database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def set_commands(bot: Bot):
    # Oddiy userlar uchun — faqat /start ko'rinadi
    await bot.set_my_commands(
        commands=[
            BotCommand(command="start", description="Botni boshlash"),
        ],
        scope=BotCommandScopeDefault()
    )

    # Har bir admin uchun alohida — admin buyruqlari ham ko'rinadi
    for admin_id in ADMIN_IDS:
        try:
            await bot.set_my_commands(
                commands=[
                    BotCommand(command="start", description="Botni boshlash"),
                    BotCommand(command="stats", description="📊 Statistika"),
                    BotCommand(command="leads", description="📋 Leadlar ro'yxati"),
                    BotCommand(command="export", description="📤 CSV eksport"),
                    BotCommand(command="clear_leads", description="🗑 Bazani tozalash"),
                ],
                scope=BotCommandScopeChat(chat_id=admin_id)
            )
        except Exception as e:
            logger.warning(f"Admin {admin_id} uchun buyruq o'rnatilmadi: {e}")

async def main():
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await set_commands(bot)

    logger.info("Bot ishga tushdi ✅")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
