from datetime import datetime, timedelta

try:


    from aiogram import types
    from aiogram.dispatcher import FSMContext
    from aiogram.dispatcher.filters.builtin import Command
    import pandas as pd
    import io
    from aiogram.types import InputFile
    from db import db
    from loader import dp
    from data.config import ADMINS


    @dp.message_handler(commands=['get_registration_time'], state="*")
    async def get_registration_time_command(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        reg_time = db.get_registration_time(user_id)
        if reg_time:
            await message.reply(f"Siz ro'yxatdan o'tgan vaqtingiz: {reg_time} (O'zbekiston vaqti)")
        else:
            await message.reply("Ro'yxatdan o'tish vaqtini olishda xatolik yuz berdi.")


    @dp.message_handler(commands=['get_all_users'], state="*")
    async def get_all_users_command(message: types.Message, state: FSMContext):
        if message.from_user.id not in ADMINS:
            await message.reply("Sizda bu buyruqni bajarish uchun ruxsat yo'q.")
            return

        users_data = db.get_all_users_data()


        if not users_data:
            await message.reply("Foydalanuvchilar bazada mavjud emas.")
            return

        try:
            df = pd.DataFrame(users_data, columns=[
                'User ID', 'Ism', 'Telefon', 'Datetime', 'Video Index', 'Preferred Time', 'Last Sent', 'Is Subscribed', 'Viewed Videos', 'Is Group', 'Is Banned'
            ])


            df = df.fillna('Belgilanmagan')

            excel_file = io.BytesIO()
            df.to_excel(excel_file, index=False, sheet_name='Users')
            excel_file.seek(0)

            await message.reply_document(
                InputFile(excel_file, filename="users_data.xlsx"),
                caption="Foydalanuvchilar ro'yxati"
            )
        except Exception as e:
            await message.reply(f"Excel faylini yaratishda xatolik yuz berdi: {str(e)}")


except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('user commands ',  f"{time }formatted_date_time",f"error {exx}" )