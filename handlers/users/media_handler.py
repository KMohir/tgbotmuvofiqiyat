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
