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
    from data.config import ADMINS, SUPER_ADMIN_ID


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
    def admin_required(superadmin_only=False):
        def decorator(func):
            @wraps(func)
            async def wrapper(message: types.Message, *args, **kwargs):
                user_id = int(message.from_user.id)
                if superadmin_only:
                    if not db.is_superadmin(user_id):
                        await message.reply("Только главный админ может использовать эту команду.")
                        return
                else:
                    if not db.is_admin(user_id):
                        await message.reply("У вас нет прав администратора.")
                        return
                return await func(message, *args, **kwargs)
            return wrapper
        return decorator

    @dp.message_handler(commands=['add_admin'])
    async def add_admin_command(message: types.Message):
        user_id = int(message.from_user.id)
        if not db.is_superadmin(user_id):
            await message.reply("Только супер-админ может добавлять админов.")
            return
        args = message.get_args().split()
        if not args or not args[0].isdigit():
            await message.reply("Используйте: /add_admin [user_id]")
            return
        new_admin_id = int(args[0])
        if db.is_admin(new_admin_id):
            await message.reply("Этот пользователь уже админ.")
            return
        if db.add_admin(new_admin_id):
            await message.reply(f"Пользователь {new_admin_id} добавлен в админы.")
        else:
            await message.reply("Ошибка при добавлении админа.")

    @dp.message_handler(commands=['remove_admin'])
    async def remove_admin_command(message: types.Message):
        user_id = int(message.from_user.id)
        if not db.is_superadmin(user_id):
            await message.reply("Только супер-админ может удалять админов.")
            return
        args = message.get_args().split()
        if not args or not args[0].isdigit():
            await message.reply("Используйте: /remove_admin [user_id]")
            return
        remove_admin_id = int(args[0])
        if not db.is_admin(remove_admin_id):
            await message.reply("Этот пользователь не является админом.")
            return
        if db.remove_admin(remove_admin_id):
            await message.reply(f"Пользователь {remove_admin_id} удалён из админов.")
        else:
            await message.reply("Ошибка при удалении админа.")

    @dp.message_handler(commands=['list_admins'])
    async def list_admins_command(message: types.Message):
        user_id = int(message.from_user.id)
        if not (db.is_superadmin(user_id) or db.is_admin(user_id)):
            await message.reply("У вас нет прав для этой команды.")
            return
        admins = db.get_all_admins()
        if not admins:
            await message.reply("Список админов пуст.")
            return
        text = "Список обычных админов:\n"
        for admin_id, is_super in admins:
            text += f"{admin_id}{' (супер-админ)' if is_super else ''}\n"
        await message.reply(text)


    @dp.message_handler(commands=['set_group_video'])
    async def set_group_video_command(message: types.Message, state: FSMContext):
        args = message.get_args().split()
        if not args:
            # Запустить мастер с клавиатурой выбора проекта
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            from handlers.users.admin_image_sender import GroupVideoStates
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Centris Towers", callback_data="project_centr"),
                InlineKeyboardButton("Golden Lake", callback_data="project_golden"),
                InlineKeyboardButton("Оба", callback_data="project_both")
            )
            await message.answer("Выберите проект для группы:", reply_markup=kb)
            await state.set_state(GroupVideoStates.waiting_for_project.state)
            await state.update_data(chat_id=message.chat.id)
            return
        if len(args) != 2 or args[0] not in ['centris', 'golden'] or not args[1].isdigit():
            await message.reply("Используйте: /set_group_video centris [номер_сезона] или /set_group_video golden [номер_сезона]")
            return
        project, season_number = args[0], args[1]
        if project == 'centris':
            db.set_group_video_settings(
                message.chat.id,
                centris_enabled=True,
                centris_season=season_number,
                centris_start_video=0,
                golden_enabled=False,
                golden_start_video=0
            )
            await message.reply(f"В группе включена рассылка Centris Towers, сезон №{season_number}")
        else:
            db.set_group_video_settings(
                message.chat.id,
                centris_enabled=False,
                centris_season=None,
                golden_enabled=True,
                golden_season=season_number
            )
            await message.reply(f"В группе включена рассылка Golden Lake, сезон №{season_number}")

    @dp.message_handler(commands=['disable_group_video'])
    async def disable_group_video_command(message: types.Message):
        args = message.get_args().split()
        if len(args) != 1 or args[0] not in ['centris', 'golden']:
            await message.reply("Используйте: /disable_group_video centris или /disable_group_video golden")
            return
        project = args[0]
        settings = db.get_group_video_settings(message.chat.id)
        if project == 'centris':
            db.set_group_video_settings(
                chat_id=message.chat.id,
                centris_enabled=False,
                centris_season=None,
                golden_enabled=settings[2],
                golden_season=settings[3]
            )
            await message.reply("Рассылка Centris Towers отключена для этой группы.")
        else:
            db.set_group_video_settings(
                chat_id=message.chat.id,
                centris_enabled=settings[0],
                centris_season=settings[1],
                golden_enabled=False,
                golden_season=None
            )
            await message.reply("Рассылка Golden Lake отключена для этой группы.")


    @dp.message_handler(commands=['set_centr_time'])
    async def set_centr_time_command(message: types.Message):
        args = message.get_args().split()
        if not (1 <= len(args) <= 2):
            await message.reply("Используйте: /set_centr_time <08:00> [20:00]")
            return
        centris_time_1 = args[0]
        centris_time_2 = args[1] if len(args) == 2 else None
        cursor = db.conn.cursor()
        if centris_time_2:
            cursor.execute("UPDATE group_video_settings SET centris_time_1 = %s, centris_time_2 = %s WHERE chat_id = %s", (centris_time_1, centris_time_2, message.chat.id))
        else:
            cursor.execute("UPDATE group_video_settings SET centris_time_1 = %s, centris_time_2 = NULL WHERE chat_id = %s", (centris_time_1, message.chat.id))
        db.conn.commit()
        cursor.close()
        await message.reply(f"Время рассылки Centris Towers обновлено: {centris_time_1}" + (f" и {centris_time_2}" if centris_time_2 else ""))

    @dp.message_handler(commands=['set_golden_time'])
    async def set_golden_time_command(message: types.Message):
        args = message.get_args().split()
        if len(args) != 1:
            await message.reply("Используйте: /set_golden_time <11:00>")
            return
        golden_time = args[0]
        cursor = db.conn.cursor()
        cursor.execute("UPDATE group_video_settings SET golden_time = %s WHERE chat_id = %s", (golden_time, message.chat.id))
        db.conn.commit()
        cursor.close()
        await message.reply(f"Время рассылки Golden Lake обновлено: {golden_time}")


except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('user commands', formatted_date_time, f"error {exx}")