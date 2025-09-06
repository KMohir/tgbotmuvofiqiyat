from datetime import datetime, timedelta
from functools import wraps
import asyncio

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


    # Закомментировано - используется обработчик из admin_image_sender.py
    # @dp.message_handler(commands=['set_group_video'])
    # async def set_group_video_command(message: types.Message, state: FSMContext):
    #     args = message.get_args().split()
    #     if not args:
    #         # Запустить мастер с клавиатурой выбора проекта
    #         from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    #         from handlers.users.admin_image_sender import GroupVideoStates
    #         kb = InlineKeyboardMarkup(row_width=2)
    #         kb.add(
    #             InlineKeyboardButton("Centris Towers", callback_data="project_centr"),
    #             InlineKeyboardButton("Golden Lake", callback_data="project_golden"),
    #             InlineKeyboardButton("Оба", callback_data="project_both")
    #         )
    #         await message.answer("Выберите проект для группы:", reply_markup=kb)
    #         await state.set_state(GroupVideoStates.waiting_for_project.state)
    #         await state.update_data(chat_id=message.chat.id)
    #         return
    #     if len(args) != 2 or args[0] not in ['centris', 'golden'] or not args[1].isdigit():
    #         await message.reply("Используйте: /set_group_video centris [номер_сезона] или /set_group_video golden [номер_сезона]")
    #         return
    #     project, season_number = args[0], args[1]
    #     if project == 'centris':
    #         db.set_group_video_settings(
    #             message.chat.id,
    #             centris_enabled=True,
    #             centris_season=season_number,
    #             centris_start_video=0,
    #             golden_enabled=False,
    #             golden_start_video=0
    #         )
    #         await message.reply(f"В группе включена рассылка Centris Towers, сезон №{season_number}")
    #     else:
    #         db.set_group_video_settings(
    #             message.chat.id,
    #             centris_enabled=False,
    #             centris_season=None,
    #             golden_enabled=True,
    #             golden_season=season_number
    #         )
    #         await message.reply(f"В группе включена рассылка Golden Lake, сезон №{season_number}")

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

    # Команда для просмотра настроек видео рассылки группы
    @dp.message_handler(commands=['show_group_video_settings'])
    async def show_group_video_settings_command(message: types.Message):
        """
        Команда для просмотра текущих настроек видео рассылки в группе
        """
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            # Проверяем права пользователя
            if not (db.is_superadmin(user_id) or db.is_admin(user_id)):
                await message.reply("У вас нет прав для этой команды.")
                return
            
            # Проверяем, что команда используется в группе
            if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
                await message.reply("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
                return
            
            # Получаем настройки группы
            settings = db.get_group_video_settings(chat_id)
            if not settings:
                await message.reply(
                    "📹 **GURUH VIDEO SOZLAMALARI**\n\n"
                    "❌ **Hech qanday sozlamalar topilmadi!**\n\n"
                    "Video tarqatishni yoqish uchun /set_group_video buyrug'ini ishlating."
                )
                return
            
            # Получаем стартовые позиции
            centris_start = db.get_group_video_start(chat_id, 'centris')
            golden_start = db.get_group_video_start(chat_id, 'golden')
            
            # Получаем информацию о сезонах
            centris_season_name = "N/A"
            golden_season_name = "N/A"
            
            if settings[1]:  # centris_season
                centris_season_info = db.get_season_by_id(settings[1])
                if centris_season_info:
                    centris_season_name = centris_season_info[1]  # season_name
            
            if settings[5]:  # golden_season
                golden_season_info = db.get_season_by_id(settings[5])
                if golden_season_info:
                    golden_season_name = golden_season_info[1]  # season_name
            
            # Формируем ответ
            response = "📹 **GURUH VIDEO SOZLAMALARI**\n\n"
            
            # Centris Towers
            response += "🏢 **Centris Towers:**\n"
            if settings[0]:  # centris_enabled
                response += f"   ✅ Yoqilgan\n"
                response += f"   📺 Seson: {centris_season_name}\n"
                response += f"   🎬 Boshlash videosi: {centris_start[1] if centris_start[0] else 0}\n"
            else:
                response += "   ❌ O'chirilgan\n"
            
            response += "\n"
            
            # Golden Lake
            response += "🏘️ **Golden Lake:**\n"
            if settings[4]:  # golden_enabled
                response += f"   ✅ Yoqilgan\n"
                response += f"   📺 Seson: {golden_season_name}\n"
                response += f"   🎬 Boshlash videosi: {golden_start[1] if golden_start[0] else 0}\n"
            else:
                response += "   ❌ O'chirilgan\n"
            
            response += "\n"
            
            # Статус подписки
            is_subscribed = db.get_subscription_status(chat_id)
            response += f"📡 **Obuna holati:** {'✅ Faol' if is_subscribed else '❌ Faol emas'}\n"
            
            # Whitelist статус
            is_whitelisted = db.is_group_whitelisted(chat_id)
            response += f"🔒 **Whitelist:** {'✅ Ruxsat berilgan' if is_whitelisted else '❌ Ruxsat berilmagan'}\n"
            
            await message.reply(response, parse_mode='Markdown')
            
        except Exception as e:
            await message.reply(f"❌ Xatolik yuz berdi: {e}")


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

    @dp.message_handler(commands=['send_content'], state="*")
    async def send_content_command(message: types.Message, state: FSMContext):
        """
        Команда для пересылки сообщения во все зарегистрированные группы
        """
        try:
            user_id = message.from_user.id
            
            # Проверяем права пользователя
            if not (db.is_superadmin(user_id) or db.is_admin(user_id)):
                await message.reply("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
                return
            
            # Парсим аргументы команды
            args = message.get_args().split()
            show_details = True  # По умолчанию показываем детали
            
            if args and args[0] in ['--quiet', '--brief', '-q']:
                show_details = False
            
            # Сохраняем настройку в состоянии
            await state.update_data(show_details=show_details)
            
            # Переходим в состояние ожидания ID сообщения
            from handlers.users.group_video_states import SendContentStates
            await state.set_state(SendContentStates.waiting_for_message_id.state)
            
            if show_details:
                await message.reply("📤 **Xabar ID yuboring**\n\nIltimos, yuborish kerak bo'lgan xabarning ID yoki havolasini yuboring.\n\nMasalan: `https://t.me/c/2550852551/802` yoki `802`\n\n💡 **Qisqa natija uchun:** `/send_content --quiet`")
            else:
                await message.reply("📤 **Xabar ID yuboring**\n\nIltimos, yuborish kerak bo'lgan xabarning ID yoki havolasini yuboring.\n\nMasalan: `https://t.me/c/2550852551/802` yoki `802`")
                
        except Exception as e:
            await message.reply(f"❌ **Xatolik yuz berdi!**\n\n{str(e)}")

    @dp.message_handler(state="SendContentStates:waiting_for_message_id")
    async def process_message_id(message: types.Message, state: FSMContext):
        """
        Обработка ID сообщения и пересылка во все группы
        """
        try:
            user_id = message.from_user.id
            message_text = message.text.strip()
            
            # Получаем настройку детального вывода из состояния
            data = await state.get_data()
            show_details = data.get('show_details', True)
            
            # Парсим ID сообщения из ссылки или получаем напрямую
            message_id = None
            source_chat_id = None
            
            if message_text.startswith('https://t.me/c/'):
                # Парсим ссылку типа https://t.me/c/2550852551/802
                try:
                    parts = message_text.split('/')
                    if len(parts) >= 5:
                        chat_id_part = parts[4]  # 2550852551
                        message_id_part = parts[5]  # 802
                        
                        # Преобразуем в правильный формат ID группы
                        source_chat_id = int(f"-100{chat_id_part}")
                        message_id = int(message_id_part)
                except (ValueError, IndexError):
                    await message.reply("❌ **Noto'g'ri havola format!**\n\nIltimos, to'g'ri havola yuboring.\nMasalan: `https://t.me/c/2550852551/802`")
                    return
            elif message_text.isdigit():
                # Если передан только ID сообщения, используем группу с видео как источник
                source_chat_id = -1002550852551
                message_id = int(message_text)
            else:
                await message.reply("❌ **Noto'g'ri format!**\n\nIltimos, havola yoki raqam yuboring.\nMasalan: `https://t.me/c/2550852551/802` yoki `802`")
                return
            
            # Получаем все зарегистрированные группы
            groups_settings = db.get_all_groups_with_settings()
            if not groups_settings:
                await message.reply("❌ **Hech qanday guruh topilmadi!**\n\nRo'yxatdan o'tgan guruhlar yo'q.")
                await state.finish()
                return
            
            # Получаем информацию о пользователе
            user_name = message.from_user.first_name or "Noma'lum"
            user_username = f"@{message.from_user.username}" if message.from_user.username else "Username yo'q"
            
            sent_count = 0
            failed_count = 0
            
            # Инициализируем ответ в зависимости от режима
            if show_details:
                response = "📤 **Xabar yuborish natijalari:**\n\n"
            else:
                response = ""
            
            # Пересылаем сообщение во все группы
            for group_data in groups_settings:
                try:
                    chat_id = int(group_data[0])  # chat_id
                    group_name = group_data[9] if len(group_data) > 9 else "Noma'lum guruh"  # group_name
                    
                    # Пересылаем сообщение
                    await message.bot.copy_message(
                        chat_id=chat_id,
                        from_chat_id=source_chat_id,
                        message_id=message_id,
                        caption=f"📤 **Admin tomonidan yuborilgan:**\n\n👤 **Admin:** {user_name}\n🔗 **Username:** {user_username}\n🆔 **ID:** `{user_id}`\n\n📝 **Xabar:**"
                    )
                    
                    sent_count += 1
                    if show_details:
                        response += f"✅ **{group_name}**: Yuborildi\n"
                    
                    # Небольшая задержка между отправками
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    failed_count += 1
                    if show_details:
                        response += f"❌ **{group_name}**: Xatolik - {str(e)[:50]}...\n"
                    continue
            
            # Формируем итоговый ответ
            if show_details:
                # Детальный режим - показываем все
                response += f"\n📊 **Jami natijalar:**\n"
                response += f"✅ Yuborilgan: {sent_count} guruh\n"
                response += f"❌ Xatolik: {failed_count} guruh\n"
                response += f"📋 Jami: {len(groups_settings)} guruh"
                
                # Разбиваем на части, если сообщение слишком длинное
                if len(response) > 4096:
                    parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
                    for i, part in enumerate(parts):
                        await message.answer(f"📤 **Qism {i+1}/{len(parts)}:**\n\n{part}")
                else:
                    await message.answer(response)
            else:
                # Краткий режим - показываем только итоги
                brief_response = f"📤 **Xabar yuborildi!**\n\n✅ **Muvaffaqiyatli:** {sent_count} guruh\n❌ **Xatolik:** {failed_count} guruh\n📋 **Jami:** {len(groups_settings)} guruh"
                await message.answer(brief_response)
            
            await state.finish()
                
        except Exception as e:
            await message.reply(f"❌ **Xatolik yuz berdi!**\n\n{str(e)}")
            await state.finish()


except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('user commands', formatted_date_time, f"error {exx}")