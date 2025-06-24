from aiogram import types
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

            # Добавляем группу в базу (или обновляем статус подписки, если она уже была)
            db.add_user(
                user_id=group_id,
                name=group_title,
                phone=None,  # У групп нет номера телефона
                is_group=True  # Указываем, что это группа
            )
            logging.info(f"Бот добавлен в группу '{group_title}' (ID: {group_id}). Группа добавлена/обновлена в базе.")

            # Оповещаем админов
            for admin in ADMINS:
                await dp.bot.send_message(admin, f"Бот был добавлен в новую группу: {group_title}")

        # Если бота удалили или заблокировали в группе
        elif message.new_chat_member.status in [types.ChatMemberStatus.LEFT, types.ChatMemberStatus.KICKED]:
            group_id = message.chat.id
            group_title = message.chat.title

            # Отписываем группу от рассылки
            db.set_subscription_status(group_id, False)
            logging.info(f"Бота удалили из группы '{group_title}' (ID: {group_id}). Группа отписана от рассылки.")

            # Оповещаем админов
            for admin in ADMINS:
                await dp.bot.send_message(admin, f"Бот был удален из группы: {group_title}") 