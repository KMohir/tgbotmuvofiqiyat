from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data.config import ADMINS
from loader import dp, db
import logging


@dp.my_chat_member_handler()
async def my_chat_member_handler(message: types.ChatMemberUpdated):
    # Проверяем, что событие произошло в группе или супергруппе
    if message.chat.type in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
        # Новый статус бота - "участник" (member) или "администратор" (administrator)
        if message.new_chat_member.status in [types.ChatMemberStatus.MEMBER, types.ChatMemberStatus.ADMINISTRATOR]:
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
    logging.info(f"Обработчик callback_query вызван с данными: {callback_query.data}")
    
    user_id = callback_query.from_user.id
    logging.info(f"Callback от пользователя {user_id}, тип: {type(user_id)}")
    logging.info(f"ADMINS: {ADMINS}, тип: {type(ADMINS)}")
    logging.info(f"Проверка: {user_id} in {ADMINS} = {user_id in ADMINS}")
    
    if user_id not in ADMINS:
        logging.warning(f"Пользователь {user_id} не найден в списке админов {ADMINS}")
        await callback_query.answer("У вас нет прав для выполнения этого действия", show_alert=True)
        return

    # Правильно разбираем callback_data для отрицательных ID групп
    parts = callback_query.data.split('_')
    logging.info(f"Разбор callback_data: {callback_query.data}")
    logging.info(f"Части после split('_'): {parts}")
    
    action = parts[0]  # allow или ban (первая часть)
    group_id = int('_'.join(parts[2:]))  # Объединяем остальные части для отрицательного ID
    logging.info(f"Действие: {action}, ID группы: {group_id}")

    if action == "allow":
        # Разрешаем группу
        db.unban_group(group_id)
        await callback_query.message.edit_text(
            f"✅ Группа {group_id} разрешена и добавлена в рассылку."
        )
        logging.info(f"Админ {callback_query.from_user.id} разрешил группу {group_id}")

    elif action == "ban":
        # Запрещаем группу и выходим из неё
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