from datetime import datetime, timedelta
from functools import wraps

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


    # Декоратор для проверки прав админа
    async def is_admin(user_id):
        return user_id == SUPER_ADMIN_ID or db.is_admin(user_id)

    # Новая функция проверки супер-админа
    async def is_superadmin(user_id):
        return user_id == SUPER_ADMIN_ID

    def admin_required(superadmin_only=False):
        def decorator(func):
            @wraps(func)
            async def wrapper(message: types.Message, *args, **kwargs):
                user_id = message.from_user.id
                if superadmin_only:
                    if not await is_superadmin(user_id):
                        await message.reply("Только главный админ может использовать эту команду.")
                        return
                else:
                    if not await is_admin(user_id):
                        await message.reply("У вас нет прав администратора.")
                        return
                return await func(message, *args, **kwargs)
            return wrapper
        return decorator

    def is_superadmin(user_id):
        return user_id in ADMINS

    @dp.message_handler(commands=['add_admin'])
    async def add_admin_command(message: types.Message):
        if not is_superadmin(message.from_user.id):
            await message.reply("Только супер-админ может добавлять админов.")
            return
        args = message.get_args().split()
        if not args or not args[0].isdigit():
            await message.reply("Используйте: /add_admin <user_id>")
            return
        user_id = int(args[0])
        if db.is_admin(user_id):
            await message.reply("Этот пользователь уже админ.")
            return
        if db.add_admin(user_id):
            await message.reply(f"Пользователь {user_id} добавлен в админы.")
        else:
            await message.reply("Ошибка при добавлении админа.")

    @dp.message_handler(commands=['remove_admin'])
    async def remove_admin_command(message: types.Message):
        if not is_superadmin(message.from_user.id):
            await message.reply("Только супер-админ может удалять админов.")
            return
        args = message.get_args().split()
        if not args or not args[0].isdigit():
            await message.reply("Используйте: /remove_admin <user_id>")
            return
        user_id = int(args[0])
        if not db.is_admin(user_id):
            await message.reply("Этот пользователь не является админом.")
            return
        if db.remove_admin(user_id):
            await message.reply(f"Пользователь {user_id} удалён из админов.")
        else:
            await message.reply("Ошибка при удалении админа.")

    @dp.message_handler(commands=['list_admins'])
    async def list_admins_command(message: types.Message):
        if not (is_superadmin(message.from_user.id) or db.is_admin(message.from_user.id)):
            await message.reply("У вас нет прав для этой команды.")
            return
        admins = db.get_all_admins()
        if not admins:
            await message.reply("Список админов пуст.")
            return
        text = "Список обычных админов:\n"
        for user_id in admins:
            text += f"{user_id}\n"
        await message.reply(text)


except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('user commands ',  f"{time }formatted_date_time",f"error {exx}" )