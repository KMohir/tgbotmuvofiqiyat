from datetime import datetime, timedelta
from time import time

try:


    from aiogram import types
    from aiogram.dispatcher.filters import Text
    from loader import dp
    from db import db

    @dp.message_handler(Text(equals="FAQ ?"))
    async def unsubscribe(message: types.Message):
        user_id = message.from_user.id
        if not db.user_exists(user_id):
            await message.answer("Iltimos, /start buyrug'i bilan ro'yxatdan o'ting.")
            return

        db.set_subscription_status(user_id, 0)
        await message.answer("Siz yangiliklarni olishdan voz kechdingiz. Qayta obuna bo'lish uchun /start buyrug'ini ishlatishingiz mumkin.")
except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('subsription ',  f"{time }formatted_date_time",f"error {exx}" )