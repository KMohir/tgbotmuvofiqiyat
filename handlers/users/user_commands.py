from aiogram import types
from aiogram.dispatcher.filters.builtin import Command
import pandas as pd
import io
from aiogram.types import InputFile
from db import db
from loader import dp

# ID администратора
ADMIN_ID = 5657091547

@dp.message_handler(commands=['get_registration_time'])
async def get_registration_time_command(message: types.Message):
    user_id = message.from_user.id
    if not db.user_exists(user_id):
        lang = db.get_lang(user_id) if db.user_exists(user_id) else 'uz'
        if lang == "uz":
            await message.reply("Siz hali ro'yxatdan o'tmagansiz!")
        else:
            await message.reply("Вы еще не зарегистрированы!")
        return

    reg_time = db.get_registration_time(user_id)
    if reg_time:
        lang = db.get_lang(user_id)
        if lang == "uz":
            await message.reply(f"Siz ro'yxatdan o'tgan vaqtingiz: {reg_time} (O'zbekiston vaqti)")
        else:
            await message.reply(f"Время вашей регистрации: {reg_time} (по узбекскому времени)")
    else:
        await message.reply("Не удалось получить время регистрации.")

@dp.message_handler(commands=['get_all_users'], user_id=ADMIN_ID)
async def get_all_users_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("Sizda bu buyruqni bajarish uchun ruxsat yo'q.")
        return

    users_data = db.get_all_users_data()

    if not users_data:
        await message.reply("Foydalanuvchilar bazada mavjud emas.")
        return

    df = pd.DataFrame(users_data, columns=[
        'User ID', 'Til', 'Ism', 'Telefon', 'Datetime'
    ])

    df = df.fillna('Belgilanmagan')

    excel_file = io.BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)

    await message.reply_document(
        InputFile(excel_file, filename="users_data.xlsx"),
        caption="Foydalanuvchilar ro'yxati"
    )