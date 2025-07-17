from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import Command
from data.config import ADMINS, SUPER_ADMIN_ID
from loader import dp, db
import logging
from aiogram.utils.exceptions import ChatAdminRequired
from aiogram.dispatcher.handler import CancelHandler


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

            # Проверяем, не заблокирована ли уже эта группа
            if db.is_group_banned(group_id):
                # Если группа заблокирована, сразу выходим из неё
                await dp.bot.leave_chat(group_id)
                logging.info(f"Бот автоматически покинул заблокированную группу '{group_title}' (ID: {group_id})")
                return

            # Добавляем группу в базу (или обновляем статус подписки, если она уже была)
            db.add_user(
                user_id=group_id,
                name=group_title,
                phone=None,  # У групп нет номера телефона
                is_group=True,  # Указываем, что это группа
                group_id=None  # Для самой группы group_id не нужен
            )
            logging.info(f"Бот добавлен в группу '{group_title}' (ID: {group_id}). Группа добавлена/обновлена в базе.")

            # Создаем клавиатуру для админа
            keyboard = InlineKeyboardMarkup(row_width=2)
            # --- Формирование callback_data ---
            allow_callback = f"allow_group_{group_id}"
            ban_callback = f"ban_group_{group_id}"
            
            logging.info(f"Создаем кнопки с callback_data: allow={allow_callback}, ban={ban_callback}")
            
            keyboard.add(
                InlineKeyboardButton("✅ Разрешить", callback_data=allow_callback),
                InlineKeyboardButton("❌ Запретить", callback_data=ban_callback)
            )

            # Оповещаем админов с кнопками
            for admin in ADMINS:
                await dp.bot.send_message(
                    admin, 
                    f"🤖 Бот был добавлен в новую группу:\n"
                    f"📝 Название: {group_title}\n"
                    f"🆔 ID группы: {group_id}\n"
                    f"👤 Добавил: {added_by_name} (ID: {added_by})\n\n"
                    f"Выберите действие:",
                    reply_markup=keyboard
                )

        # Если бота удалили или заблокировали в группе
        elif message.new_chat_member.status in [types.ChatMemberStatus.LEFT, types.ChatMemberStatus.KICKED]:
            group_id = message.chat.id
            group_title = message.chat.title

            # Отписываем группу от рассылки
            db.set_subscription_status(group_id, False)
            logging.info(f"Бота удалили из группы '{group_title}' (ID: {group_id}). Группа отписана от рассылки.")

            # Оповещаем админов
            for admin in ADMINS:
                await dp.bot.send_message(admin, f"🚪 Бот был удален из группы: {group_title}")


@dp.callback_query_handler(lambda c: c.data.startswith(('allow_group_', 'ban_group_')))
async def handle_group_decision(callback_query: types.CallbackQuery):
    print("handle_group_decision вызван", callback_query.data, callback_query.from_user.id)
    logging.info(f"Обработчик callback_query вызван с данными: {callback_query.data}")
    
    user_id = callback_query.from_user.id
    logging.info(f"Callback от пользователя {user_id}, тип: {type(user_id)}")
    logging.info(f"ADMINS: {ADMINS}, тип: {type(ADMINS)}")
    logging.info(f"Проверка: {user_id} in {ADMINS} = {user_id in ADMINS}")
    
    # Разрешить действие только супер-админу и обычным админам из базы
    if not (db.is_superadmin(user_id) or db.is_admin(user_id)):
        logging.warning(f"Пользователь {user_id} не найден в списке админов {ADMINS}")
        await callback_query.answer("У вас нет прав для выполнения этого действия", show_alert=True)
        return

    # Корректный разбор callback_data для отрицательных group_id
    # callback_data всегда вида: allow_group_{group_id} или ban_group_{group_id}
    prefix, _, group_id_str = callback_query.data.partition('_group_')
    action = prefix  # allow или ban
    group_id = int(group_id_str)
    logging.info(f"Действие: {action}, ID группы: {group_id}")

    if action == "allow":
        db.unban_group(group_id)
        print(f"Статус группы {group_id} после allow: is_group_banned = {db.is_group_banned(group_id)}")
        await callback_query.message.edit_text(
            f"✅ Группа {group_id} разрешена и добавлена в рассылку."
        )
        logging.info(f"Админ {callback_query.from_user.id} разрешил группу {group_id}")

    elif action == "ban":
        db.ban_group(group_id)
        try:
            await dp.bot.leave_chat(group_id)
            await callback_query.message.edit_text(
                f"❌ Группа {group_id} запрещена. Бот покинул группу."
            )
            logging.info(f"Админ {callback_query.from_user.id} запретил группу {group_id}, бот покинул группу")
        except Exception as e:
            await callback_query.message.edit_text(
                f"❌ Группа {group_id} запрещена, но не удалось покинуть группу: {e}"
            )
            logging.error(f"Ошибка при выходе из запрещенной группы {group_id}: {e}")

    await callback_query.answer() 


# Универсальный препроцессор для всех сообщений в группах
@dp.message_handler(chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def group_protect_filter(message: types.Message):
    if db.is_group_banned(message.chat.id):
        # Не отвечаем и не обрабатываем сообщения, если группа не разрешена
        raise CancelHandler()
    # В разрешённых группах — пропускаем всё
    pass


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
        centris_season = group[2]
        centris_start_video = group[3]
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
        f"golden_enabled: {settings[3] if settings else '-'}\n"
        f"golden_start_video: {settings[4] if settings else '-'}\n"
        f"centris_start_season_id: {centris_start_season_id}\n"
        f"centris_start_video: {centris_start_video}\n"
        f"golden_start_season_id: {golden_start_season_id}\n"
        f"golden_start_video: {golden_start_video}\n"
        f"is_subscribed: {is_subscribed}"
    )
    await message.reply(text, parse_mode='HTML') 

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
            banned = db.is_group_banned(user_id)
            status = "Нет" if banned else "Да"
            text += f'ID: <code>{user_id}</code> | {name} | Разрешена: <b>{status}</b>\n'
    await message.reply(text, parse_mode='HTML')

@dp.message_handler(commands=['unban_all_groups'])
async def unban_all_groups_command(message: types.Message):
    db.unban_all_groups()
    await message.reply('Бан снят со всех групп. Все группы теперь разрешены!')

@dp.message_handler(chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def debug_group_message(message: types.Message):
    print(f"[DEBUG] Получено сообщение в группе: chat_id={message.chat.id}, user_id={message.from_user.id}, text={message.text}")
    # Не отвечаем в чат, только логируем 