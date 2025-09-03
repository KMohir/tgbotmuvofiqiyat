from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import Command
from data.config import ADMINS, SUPER_ADMIN_ID
from loader import dp
from db import db
import logging

# --- Удалены все проверки и действия, связанные с разрешением/запретом групп ---


@dp.my_chat_member_handler()
async def my_chat_member_handler(message: types.ChatMemberUpdated):
    # Проверяем, что событие произошло в группе или супергруппе
    if message.chat.type in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
        # Отправлять уведомление только если бот был добавлен впервые
        if message.old_chat_member.status in [types.ChatMemberStatus.LEFT, types.ChatMemberStatus.KICKED] and \
           message.new_chat_member.status in [types.ChatMemberStatus.MEMBER, types.ChatMemberStatus.ADMINISTRATOR]:
            group_id = message.chat.id
            group_title = message.chat.title
            added_by = message.from_user.id
            added_by_name = message.from_user.full_name

            # ПРОВЕРЯЕМ: Только супер-админ может добавлять бота в группу
            if not db.is_superadmin(added_by):
                logging.warning(f"Попытка добавить бота в группу {group_id} неавторизованным пользователем {added_by}")
                
                # Отправляем сообщение о том, что только супер-админ может добавлять бота
                try:
                    await message.bot.send_message(
                        group_id,
                        f"🚫 **Bot qo'shish ruxsati yo'q!**\n\n"
                        f"Botni faqat super-admin qo'sha oladi.\n"
                        f"Qo'shgan: {added_by_name} (ID: {added_by})\n\n"
                        f"Bot avtomatik ravishda guruhni tark etadi."
                    )
                except Exception as e:
                    logging.error(f"Ошибка при отправке сообщения о неавторизованном добавлении: {e}")
                
                # Бот выходит из группы
                try:
                    await message.bot.leave_chat(group_id)
                    logging.warning(f"Бот покинул группу {group_id} из-за неавторизованного добавления")
                except Exception as e:
                    logging.error(f"Ошибка при выходе из группы {group_id}: {e}")
                
                # Оповещаем супер-админов
                for admin in ADMINS:
                    try:
                        await dp.bot.send_message(
                            admin, 
                            f"🚫 **Неавторизованная попытка добавления бота!**\n\n"
                            f"📝 Группа: {group_title}\n"
                            f"🆔 ID группы: {group_id}\n"
                            f"👤 Попытался добавить: {added_by_name} (ID: {added_by})\n\n"
                            f"❌ Бот автоматически покинул группу."
                        )
                    except Exception as e:
                        logging.error(f"Ошибка при уведомлении админа {admin}: {e}")
                
                return

            # Если добавил супер-админ - добавляем группу в whitelist
            logging.info(f"Супер-админ {added_by} добавил бота в группу {group_id}")
            
            # Добавляем группу в базу (или обновляем статус подписки, если она уже была)
            db.add_user(
                user_id=group_id,
                name=group_title,
                phone=None,  # У групп нет номера телефона
                is_group=True  # Указываем, что это группа
            )
            
            # Автоматически добавляем группу в whitelist
            if db.add_group_to_whitelist_auto(group_id, group_title, added_by):
                logging.info(f"Группа '{group_title}' (ID: {group_id}) автоматически добавлена в whitelist")
            else:
                logging.error(f"Не удалось добавить группу '{group_title}' (ID: {group_id}) в whitelist")
            
            logging.info(f"Бот добавлен в группу '{group_title}' (ID: {group_id}). Группа добавлена/обновлена в базе.")

            # Оповещаем супер-админов об успешном добавлении
            for admin in ADMINS:
                try:
                    await dp.bot.send_message(
                        admin, 
                        f"✅ **Бот успешно добавлен в группу!**\n\n"
                        f"📝 Название: {group_title}\n"
                        f"🆔 ID группы: {group_id}\n"
                        f"👤 Добавил: {added_by_name} (ID: {added_by})\n\n"
                        f"🤖 Группа автоматически добавлена в whitelist и может использовать бота."
                    )
                except Exception as e:
                    logging.error(f"Ошибка при уведомлении админа {admin}: {e}")

        # Если бота удалили или заблокировали в группе
        elif message.new_chat_member.status in [types.ChatMemberStatus.LEFT, types.ChatMemberStatus.KICKED]:
            group_id = message.chat.id
            group_title = message.chat.title

            # Отписываем группу от рассылки
            db.set_subscription_status(group_id, False)
            logging.info(f"Бота удалили из группы '{group_title}' (ID: {group_id}). Группа отписана от рассылки.")

            # Оповещаем админов
            for admin in ADMINS:
                try:
                    await dp.bot.send_message(admin, f"🚪 Бот был удален из группы: {group_title}")
                except Exception as e:
                    logging.error(f"Ошибка при уведомлении админа {admin}: {e}")


@dp.callback_query_handler(lambda c: c.data.startswith(('allow_group_', 'ban_group_')))
async def handle_group_decision(callback_query: types.CallbackQuery):
    print("handle_group_decision вызван", callback_query.data, callback_query.from_user.id)
    logging.info(f"Обработчик callback_query вызван с данными: {callback_query.data}")
    
    user_id = callback_query.from_user.id
    logging.info(f"Callback от пользователя {user_id}, тип: {type(user_id)}")
    logging.info(f"ADMINS: {ADMINS}, тип: {type(ADMINS)}")
    logging.info(f"Проверка: {user_id} in {ADMINS} = {user_id in ADMINS}")
    
    # Разрешить действие только супер-админу и обычным админам из базы
    # if not (db.is_superadmin(user_id) or db.is_admin(user_id)):
    #     logging.warning(f"Пользователь {user_id} не найден в списке админов {ADMINS}")
    #     await callback_query.answer("У вас нет прав для выполнения этого действия", show_alert=True)
    #     return

    # Корректный разбор callback_data для отрицательных group_id
    # callback_data всегда вида: allow_group_{group_id} или ban_group_{group_id}
    prefix, _, group_id_str = callback_query.data.partition('_group_')
    action = prefix  # allow или ban
    group_id = int(group_id_str)
    logging.info(f"Действие: {action}, ID группы: {group_id}")

    # if action == "allow":
    #     db.unban_group(group_id)
    #     print(f"Статус группы {group_id} после allow: is_group_banned = {db.is_group_banned(group_id)}")
    #     await callback_query.message.edit_text(
    #         f"✅ Группа {group_id} разрешена и добавлена в рассылку."
    #     )
    #     logging.info(f"Админ {callback_query.from_user.id} разрешил группу {group_id}")

    # elif action == "ban":
    #     db.ban_group(group_id)
    #     try:
    #         await dp.bot.leave_chat(group_id)
    #         await callback_query.message.edit_text(
    #             f"❌ Группа {group_id} запрещена. Бот покинул группу."
    #         )
    #         logging.info(f"Админ {callback_query.from_user.id} запретил группу {group_id}, бот покинул группу")
    #     except Exception as e:
    #         await callback_query.message.edit_text(
    #             f"❌ Группа {group_id} запрещена, но не удалось покинуть группу: {e}"
    #         )
    #         logging.error(f"Ошибка при выходе из запрещенной группы {group_id}: {e}")

    await callback_query.answer() 


@dp.message_handler(Command('group_subscribe'), chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def group_subscribe(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    member = await message.bot.get_chat_member(chat_id, user_id)
    from data.config import ADMINS
    if member.is_chat_admin() or user_id in ADMINS:
        db.set_subscription_status(chat_id, True)
        await message.reply('Группа успешно подписана на рассылку!')
    else:
        await message.reply('У вас нет прав для выполнения этой команды. Только администраторы группы или супер-админы могут это делать.')

@dp.message_handler(Command('group_unsubscribe'), chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def group_unsubscribe(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    member = await message.bot.get_chat_member(chat_id, user_id)
    from data.config import ADMINS
    if member.is_chat_admin() or user_id in ADMINS:
        db.set_subscription_status(chat_id, False)
        await message.reply('Группа отписана от рассылки!')
    else:
        await message.reply('У вас нет прав для выполнения этой команды. Только администраторы группы или супер-админы могут это делать.')

# Ручная команда для мгновенной отправки тестового видео
@dp.message_handler(Command('send_test_video'), chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def send_test_video(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    member = await message.bot.get_chat_member(chat_id, user_id)
    from data.config import ADMINS
    if member.is_chat_admin() or user_id in ADMINS:
        from handlers.users.video_scheduler import send_group_video_new
        # Получаем стартовые значения для Centris
        centris_start_season_id, centris_start_video = db.get_group_video_start(chat_id, 'centris')
        golden_start_season_id, golden_start_video = db.get_group_video_start(chat_id, 'golden')
        sent = False
        if centris_start_season_id:
            await send_group_video_new(chat_id, 'centris', centris_start_season_id, centris_start_video)
            sent = True
        if golden_start_season_id:
            await send_group_video_new(chat_id, 'golden', golden_start_season_id, golden_start_video)
            sent = True
        if sent:
            await message.reply('Тестовое видео отправлено!')
        else:
            await message.reply('Нет настроек для отправки тестового видео.')
    else:
        await message.reply('У вас нет прав для выполнения этой команды. Только администраторы группы или супер-админы могут это делать.') 

@dp.message_handler(Command('migrate_group_video_settings'), chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def migrate_group_video_settings(message: types.Message):
    user_id = message.from_user.id
    from data.config import ADMINS
    if user_id not in ADMINS:
        await message.reply('Только супер-админ может использовать эту команду.')
        return
    updated = 0
    groups = db.get_all_groups_with_settings()
    for group in groups:
        chat_id = group[0]
        centris_season = group[2]  # centris_season
        centris_start_video = group[4]  # centris_start_video
        if centris_season:
            db.set_group_video_start(chat_id, 'centris', int(centris_season), int(centris_start_video))
            updated += 1
    await message.reply(f'Миграция завершена! Обновлено групп: {updated}') 

@dp.message_handler(Command('group_settings'), chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def group_settings(message: types.Message):
    chat_id = message.chat.id
    settings = db.get_group_video_settings(chat_id)
    centris_start_season_id, centris_start_video = db.get_group_video_start(chat_id, 'centris')
    golden_start_season_id, golden_start_video = db.get_group_video_start(chat_id, 'golden')
    is_subscribed = db.get_subscription_status(chat_id)
    text = (
        f"<b>Текущие настройки группы:</b>\n"
        f"centris_enabled: {settings[0] if settings else '-'}\n"
        f"centris_season: {settings[1] if settings else '-'}\n"
        f"centris_start_video: {settings[2] if settings else '-'}\n"
        f"golden_enabled: {settings[4] if settings else '-'}\n"
        f"golden_season: {settings[5] if settings else '-'}\n"
        f"golden_start_video: {settings[6] if settings else '-'}\n"
        f"centris_start_season_id: {centris_start_season_id}\n"
        f"centris_start_video: {centris_start_video}\n"
        f"golden_start_season_id: {golden_start_season_id}\n"
        f"golden_start_video: {golden_start_video}\n"
        f"is_subscribed: {is_subscribed}"
    )
    await message.reply(text, parse_mode='HTML')

# Команда для просмотра настроек видео рассылки группы (красивый формат)
@dp.message_handler(Command('show_group_video_settings'), chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def show_group_video_settings_command(message: types.Message):
    """
    Команда для просмотра текущих настроек видео рассылки в группе
    """
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        from data.config import ADMINS
        if user_id not in ADMINS:
            await message.reply('❌ Только супер-админ может использовать эту команду.')
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
        logging.error(f"Ошибка при показе настроек группы: {e}")
        await message.reply(f"❌ Xatolik yuz berdi: {e}")

@dp.message_handler(Command('set_centr_season'), chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def set_centr_season(message: types.Message):
    user_id = message.from_user.id
    from data.config import ADMINS
    if user_id not in ADMINS:
        await message.reply('Только супер-админ может использовать эту команду.')
        return
    args = message.get_args().strip()
    if not args.isdigit():
        await message.reply('Укажите id сезона, например: /set_centr_season 2')
        return
    season_id = int(args)
    db.set_group_video_start(message.chat.id, 'centris', season_id, db.get_group_video_start(message.chat.id, 'centris')[1])
    await message.reply(f'centris_start_season_id установлен: {season_id}') 

@dp.message_handler(Command('set_golden_season'), chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def set_golden_season(message: types.Message):
    user_id = message.from_user.id
    from data.config import ADMINS
    if user_id not in ADMINS:
        await message.reply('Только супер-админ может использовать эту команду.')
        return
    args = message.get_args().strip()
    if not args.isdigit():
        await message.reply('Укажите id сезона, например: /set_golden_season 2')
        return
    season_id = int(args)
    db.set_group_video_start(message.chat.id, 'golden', season_id, db.get_group_video_start(message.chat.id, 'golden')[1])
    await message.reply(f'golden_start_season_id установлен: {season_id}') 

@dp.message_handler(commands=['list_groups'])
async def list_groups_command(message: types.Message):
    groups = db.get_all_users()
    text = '<b>Список групп:</b>\n'
    for user_id, name, phone, dt, is_group in groups:
        if is_group:
            # Проверяем реальный статус в whitelist
            is_whitelisted = db.is_group_whitelisted(user_id)
            status = "Да" if is_whitelisted else "Нет"
            text += f'ID: <code>{user_id}</code> | {name} | Разрешена: <b>{status}</b>\n'
    await message.reply(text, parse_mode='HTML')

@dp.message_handler(commands=['unban_all_groups'])
async def unban_all_groups_command(message: types.Message):
    db.unban_all_groups()
    await message.reply('Все группы разблокированы.')

@dp.message_handler(Command('debug_video_sending'), chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def debug_video_sending(message: types.Message):
    """Диагностика проблем с отправкой видео"""
    user_id = message.from_user.id
    from data.config import ADMINS
    if user_id not in ADMINS:
        await message.reply('Только супер-админ может использовать эту команду.')
        return
    
    chat_id = message.chat.id
    
    # Проверяем whitelist
    is_whitelisted = db.is_group_whitelisted(chat_id)
    
    # Проверяем настройки группы
    settings = db.get_group_video_settings(chat_id)
    
    # Проверяем стартовые позиции
    centris_start = db.get_group_video_start(chat_id, 'centris')
    golden_start = db.get_group_video_start(chat_id, 'golden')
    
    # Проверяем просмотренные видео
    viewed_videos = db.get_group_viewed_videos(chat_id)
    
    # Проверяем планировщик
    from handlers.users.video_scheduler import scheduler
    jobs = scheduler.get_jobs()
    group_jobs = [job for job in jobs if job.id.startswith(f"group_") and str(chat_id) in job.id]
    
    text = f"""🔍 **ДИАГНОСТИКА ОТПРАВКИ ВИДЕО**

📋 **Группа:** {chat_id}
✅ **Whitelist:** {'Да' if is_whitelisted else 'Нет'}

⚙️ **Настройки:**
- Centris: {'Включен' if settings and settings[0] else 'Отключен'}
- Centris сезон: {settings[1] if settings else 'Не задан'}
- Centris стартовое видео: {settings[2] if settings else 'Не задано'}
- Golden: {'Включен' if settings and settings[4] else 'Отключен'}
- Golden сезон: {settings[5] if settings else 'Не задан'}
- Golden стартовое видео: {settings[6] if settings else 'Не задано'}

🎯 **Стартовые позиции:**
- Centris: сезон {centris_start[0]}, видео {centris_start[1]}
- Golden: сезон {golden_start[0]}, видео {golden_start[1]}

👀 **Просмотренные видео:** {len(viewed_videos)} шт.
📅 **Задачи в планировщике:** {len(group_jobs)} шт.

🔄 **Планировщик статус:** {'Запущен' if scheduler.running else 'Остановлен'}
"""
    
    await message.reply(text, parse_mode='HTML')

@dp.message_handler(Command('restart_scheduler'), chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def restart_scheduler_command(message: types.Message):
    """Принудительный перезапуск планировщика видео"""
    user_id = message.from_user.id
    from data.config import ADMINS
    if user_id not in ADMINS:
        await message.reply('Только супер-админ может использовать эту команду.')
        return
    
    try:
        from handlers.users.video_scheduler import schedule_group_jobs, scheduler
        
        # Перезапускаем планировщик
        if scheduler.running:
            scheduler.shutdown()
            await message.reply('🔄 Планировщик остановлен')
        
        # Создаем новые задачи
        schedule_group_jobs()
        
        # Запускаем планировщик
        if not scheduler.running:
            scheduler.start()
        
        # Проверяем количество задач
        jobs = scheduler.get_jobs()
        group_jobs = [job for job in jobs if job.id.startswith("group_")]
        
        await message.reply(
            f'✅ **Планировщик перезапущен!**\n\n'
            f'📅 Всего задач: {len(jobs)}\n'
            f'🏢 Задач для групп: {len(group_jobs)}\n'
            f'🔄 Статус: {"Запущен" if scheduler.running else "Остановлен"}',
            parse_mode='HTML'
        )
        
    except Exception as e:
        await message.reply(f'❌ Ошибка при перезапуске планировщика: {e}')

@dp.message_handler(Command('test_video_sending'), chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def test_video_sending_command(message: types.Message):
    """Тестовая отправка видео в группу"""
    user_id = message.from_user.id
    from data.config import ADMINS
    if user_id not in ADMINS:
        await message.reply('Только супер-админ может использовать эту команду.')
        return
    
    chat_id = message.chat.id
    
    try:
        from handlers.users.video_scheduler import send_group_video_new
        
        # Проверяем whitelist
        if not db.is_group_whitelisted(chat_id):
            await message.reply('❌ Группа не в whitelist! Сначала добавьте группу в whitelist.')
            return
        
        # Проверяем настройки
        settings = db.get_group_video_settings(chat_id)
        if not settings or (not settings[0] and not settings[4]):
            await message.reply('❌ Группа не настроена для рассылки видео! Используйте /set_group_video')
            return
        
        # Пытаемся отправить видео
        sent = False
        
        if settings[0] and settings[1]:  # Centris включен
            centris_start = db.get_group_video_start(chat_id, 'centris')
            if centris_start[0]:
                result = await send_group_video_new(chat_id, 'centris', centris_start[0], centris_start[1])
                if result:
                    sent = True
                    await message.reply('✅ Centris видео отправлено!')
                else:
                    await message.reply('⚠️ Centris видео не отправлено (возможно, все просмотрены)')
        
        if settings[4] and settings[5]:  # Golden включен
            golden_start = db.get_group_video_start(chat_id, 'golden')
            if golden_start[0]:
                result = await send_group_video_new(chat_id, 'golden_lake', golden_start[0], golden_start[1])
                if result:
                    sent = True
                    await message.reply('✅ Golden Lake видео отправлено!')
                else:
                    await message.reply('⚠️ Golden Lake видео не отправлено (возможно, все просмотрены)')
        
        if not sent:
            await message.reply('❌ Не удалось отправить ни одного видео. Проверьте настройки и статус.')
            
    except Exception as e:
        await message.reply(f'❌ Ошибка при тестовой отправке: {e}')

@dp.message_handler(commands=['force_remove_group'])
async def force_remove_group_command(message: types.Message):
    """Принудительно удалить группу из whitelist (только для супер-админов)"""
    user_id = message.from_user.id
    
    if not db.is_superadmin(user_id):
        await message.reply("❌ Только супер-админ может использовать эту команду.")
        return
    
    args = message.get_args().strip()
    if not args:
        await message.reply("📝 **Использование:**\n\n`/force_remove_group <chat_id>`\n\nПример: `/force_remove_group -1001234567890`")
        return
    
    try:
        chat_id = int(args)
        
        if not db.is_group_whitelisted(chat_id):
            await message.reply(f"❌ Группа {chat_id} не находится в whitelist.")
            return
        
        # Удаляем группу из whitelist
        success = db.remove_group_from_whitelist(chat_id)
        if success:
            # Бот покидает группу
            try:
                await message.bot.leave_chat(chat_id)
                await message.reply(f"✅ **Группа {chat_id} удалена из whitelist и бот покинул группу.**")
                logging.info(f"Супер-админ {user_id} принудительно удалил группу {chat_id} из whitelist")
            except Exception as e:
                await message.reply(f"✅ Группа {chat_id} удалена из whitelist, но не удалось покинуть группу: {e}")
                logging.error(f"Ошибка при выходе из группы {chat_id}: {e}")
        else:
            await message.reply(f"❌ Ошибка при удалении группы {chat_id} из whitelist.")
            
    except ValueError:
        await message.reply("❌ Неверный chat ID. Введите отрицательное число (например: -1001234567890)")
    except Exception as e:
        logging.error(f"Ошибка при принудительном удалении группы: {e}")
        await message.reply("❌ Системная ошибка при удалении группы.")

@dp.message_handler(chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def debug_group_message(message: types.Message):
    print(f"[DEBUG] Получено сообщение в группе: chat_id={message.chat.id}, user_id={message.from_user.id}, text={message.text}")
    # Не отвечаем в чат, только логируем 