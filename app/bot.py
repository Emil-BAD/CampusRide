import os
from aiogram.fsm.storage.redis import RedisStorage
from app.core.redis import redis_client
from aiogram.client.default import DefaultBotProperties
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from app.routers import setup_routers
from aiogram.types import BotCommand

async def set_commands(bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="create", description="Создать поездку"),
        BotCommand(command="search", description="Найти поездку"),
        BotCommand(command="help", description="Помощь"),
    ]
    await bot.set_my_commands(commands)


bot = Bot(token=os.getenv('BOT_TOKEN'),
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=RedisStorage(redis_client))

setup_routers(dp)

async def start_bot():
    await set_commands(bot)
    await dp.start_polling(bot)