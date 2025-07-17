import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import BaseFilter

API_TOKEN = "ВАШ_ТОКЕН_БОТА"  # Вставьте сюда свой токен
SUPER_ADMIN_ID = 123456789     # Вставьте сюда свой user_id

# Фильтр доступа
class AccessFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        if message.chat.type == "private":
            return message.from_user.id == SUPER_ADMIN_ID
        elif message.chat.type in ("group", "supergroup"):
            return True  # Для теста разрешаем все группы
        return False

# Debug-хендлер для всех сообщений
async def debug_handler(message: types.Message):
    print(f"[DEBUG] chat_id={message.chat.id} user_id={message.from_user.id} text={message.text}")

# Хендлер для команд с фильтром
async def command_handler(message: types.Message):
    await message.reply("Команда доступна!")

async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    dp.message.register(debug_handler)  # Ловим все сообщения
    dp.message.register(command_handler, AccessFilter(), lambda m: m.text and m.text.startswith("/"))

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 