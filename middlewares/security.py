"""
Middleware для проверки безопасности пользователей и групп
"""

import logging
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from data.config import SUPER_ADMIN_ID, ADMINS
from db import db

logger = logging.getLogger(__name__)


class VideoSecurityMiddleware(BaseMiddleware):
    """Middleware для проверки доступа пользователей и групп"""
    
    def __init__(self):
        super(VideoSecurityMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        """Обработка сообщений с проверкой безопасности"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        chat_type = message.chat.type

        # Если есть активное состояние FSM — ничего не блокируем
        try:
            state = data.get('state')
            if state is not None:
                current_state = await state.get_state()
                if current_state:
                    return
        except Exception:
            pass

        # Супер-админы имеют полный доступ
        if self.is_super_admin(user_id):
            return

        # Обработка приватных чатов
        if chat_type == types.ChatType.PRIVATE:
            await self.check_private_chat_access(message, user_id)
        
        # Обработка групп и супергрупп
        elif chat_type in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            await self.check_group_access(message, chat_id)

    async def check_private_chat_access(self, message: types.Message, user_id: int):
        """Проверка доступа в приватном чате"""
        # Супер-админы имеют полный доступ без проверки статуса
        if self.is_super_admin(user_id):
            return
            
        # Разрешить /start и /help для незарегистрированных
        if message.text and (message.text.startswith('/start') or message.text.startswith('/help')):
            return
            
        status = db.get_user_security_status(user_id)
        
        if status is None:
            # Пользователь не зарегистрирован
            await message.answer(
                "🔐 **Xush kelibsiz!**\n\n"
                "Botga kirish uchun ro'yxatdan o'tish kerak.\n"
                "Ro'yxatdan o'tishni boshlash uchun /start buyrug'ini yuboring."
            )
            raise CancelHandler()
            
        elif status == 'pending':
            # Пользователь ожидает одобрения
            await message.answer(
                "⏳ **Arizangiz ko'rib chiqilmoqda**\n\n"
                "Sizning ro'yxatdan o'tish arizangiz hali ko'rib chiqilmagan.\n"
                "Iltimos, administrator javobini kuting."
            )
            raise CancelHandler()
            
        elif status == 'denied':
            # Пользователь отклонен
            await message.answer(
                "❌ **Arizangiz rad etildi**\n\n"
                "Afsuski, sizning ro'yxatdan o'tish arizangiz rad etildi.\n"
                "Qo'shimcha ma'lumot uchun administratorga murojaat qiling."
            )
            raise CancelHandler()
        
        elif status == 'approved':
            # Пользователь одобрен - разрешить доступ
            return

    async def check_group_access(self, message: types.Message, chat_id: int):
        """Проверка доступа в группе"""
        # Добавляем отладочную информацию
        logger.info(f"Проверка доступа группы {chat_id}, команда: {message.text}")
        
        # Проверить находится ли группа в whitelist
        is_whitelisted = db.is_group_whitelisted(chat_id)
        logger.info(f"Группа {chat_id} в whitelist: {is_whitelisted}")
        
        if not is_whitelisted:
            # Группа не в whitelist - покинуть группу
            try:
                await message.bot.send_message(
                    chat_id,
                    "🚫 **Guruh avtorizatsiya qilinmagan**\n\n"
                    "Bu guruh bot ishlashi uchun ruxsat etilganlar ro'yxatida emas.\n"
                    "Bot avtomatik ravishda guruhni tark etadi.\n\n"
                    "Guruhni qo'shish uchun administratorga murojaat qiling."
                )
                await message.bot.leave_chat(chat_id)
                logger.warning(f"Бот покинул неавторизованную группу: {chat_id}")
            except Exception as e:
                logger.error(f"Ошибка при выходе из группы {chat_id}: {e}")
            
            raise CancelHandler()

    def is_super_admin(self, user_id: int) -> bool:
        """Проверить является ли пользователь супер-админом"""
        admin_ids = [SUPER_ADMIN_ID]
        for admin in ADMINS:
            try:
                if isinstance(admin, str):
                    admin_ids.append(int(admin.strip()))
                elif isinstance(admin, int):
                    admin_ids.append(admin)
            except (ValueError, AttributeError):
                continue
        return user_id == SUPER_ADMIN_ID or user_id in admin_ids

    async def on_process_callback_query(self, callback: types.CallbackQuery, data: dict):
        """Обработка callback запросов с проверкой безопасности"""
        user_id = callback.from_user.id
        chat_id = callback.message.chat.id
        chat_type = callback.message.chat.type

        # Супер-админы имеют полный доступ
        if self.is_super_admin(user_id):
            return

        # Обработка приватных чатов
        if chat_type == types.ChatType.PRIVATE:
            status = db.get_user_security_status(user_id)
            
            if status != 'approved':
                await callback.answer(
                    "❌ Sizga bu harakatni bajarish uchun ruxsat yo'q.",
                    show_alert=True
                )
                raise CancelHandler()

        # Обработка групп
        elif chat_type in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            if not db.is_group_whitelisted(chat_id):
                await callback.answer(
                    "❌ Bu guruh avtorizatsiya qilinmagan.",
                    show_alert=True
                )
                raise CancelHandler()

    async def on_process_inline_query(self, inline_query: types.InlineQuery, data: dict):
        """Обработка inline запросов с проверкой безопасности"""
        user_id = inline_query.from_user.id

        # Супер-админы имеют полный доступ
        if self.is_super_admin(user_id):
            return

        # Проверить статус пользователя
        status = db.get_user_security_status(user_id)
        
        if status != 'approved':
            # Блокировать inline запросы для неодобренных пользователей
            await inline_query.answer(
                [],
                cache_time=0,
                switch_pm_text="❌ Ruxsat yo'q",
                switch_pm_parameter="access_denied"
            )
            raise CancelHandler() 