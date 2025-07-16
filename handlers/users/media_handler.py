from datetime import datetime, timedelta

try:
    from aiogram import types
    from db import db
    from loader import dp

    @dp.message_handler(content_types=[
        types.ContentType.VIDEO,
        types.ContentType.PHOTO,
        types.ContentType.AUDIO,
        types.ContentType.DOCUMENT
    ])
    async def block_user_media(message: types.Message):


        await message.reply("Kechirasiz, bu botda media fayllarni yuklash taqiqlangan.")


except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('media handlar', formatted_date_time, f"error {exx}")