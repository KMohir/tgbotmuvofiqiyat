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
    lang = db.get_lang(message.from_user.id) if db.user_exists(message.from_user.id) else 'uz'
    if lang == "uz":
        await message.reply("Kechirasiz, bu botda media fayllarni yuklash taqiqlangan.")
    elif lang == "ru":
        await message.reply("Извините, загрузка медиафайлов в этом боте запрещена.")