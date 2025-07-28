"""
Автоматический выход из неавторизованных групп
"""

import logging
from aiogram import types
from aiogram.dispatcher.filters import ChatTypeFilter
from loader import dp
from db import db
from data.config import SUPER_ADMIN_ID, ADMINS

logger = logging.getLogger(__name__)

def is_super_admin(user_id: int) -> bool:
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

@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS, chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def on_new_chat_members(message: types.Message):
    """Обработка добавления новых участников в группу"""
    try:
        # Проверяем был ли добавлен наш бот
        bot_user = await message.bot.get_me()
        bot_added = False
        
        for new_member in message.new_chat_members:
            if new_member.id == bot_user.id:
                bot_added = True
                break
        
        if not bot_added:
            return
            
        chat_id = message.chat.id
        chat_title = message.chat.title or f"Группа {chat_id}"
        added_by_user = message.from_user
        
        logger.info(f"Бот добавлен в группу {chat_id} ({chat_title}) пользователем {added_by_user.id}")
        
        # Проверяем является ли добавивший супер-админом
        if is_super_admin(added_by_user.id):
            # Супер-админ может добавлять бота в любые группы
            # Автоматически добавляем группу в whitelist
            try:
                if not db.is_group_whitelisted(chat_id):
                    cursor = db.conn.cursor()
                    cursor.execute('''
                        INSERT INTO group_whitelist (chat_id, title, status, added_date, added_by)
                        VALUES (%s, %s, %s, NOW(), %s)
                    ''', (chat_id, chat_title, 'active', added_by_user.id))
                    db.conn.commit()
                    cursor.close()
                    
                    await message.reply(
                        f"✅ **Guruh avtomatik avtorizatsiya qilindi**\n\n"
                        f"📋 Guruh nomi: {chat_title}\n"
                        f"🆔 Guruh ID: `{chat_id}`\n"
                        f"👨‍💼 Administrator tomonidan qo'shildi: {added_by_user.full_name}\n\n"
                        f"🤖 Bot endi bu guruhda to'liq ishlay oladi!",
                        parse_mode="Markdown"
                    )
                    logger.info(f"Группа {chat_id} автоматически добавлена в whitelist супер-админом {added_by_user.id}")
                else:
                    await message.reply(
                        f"✅ **Guruh allaqachon avtorizatsiya qilingan**\n\n"
                        f"🤖 Bot bu guruhda ishlashga ruxsat berilgan."
                    )
            except Exception as e:
                logger.error(f"Ошибка при автодобавлении группы {chat_id} в whitelist: {e}")
                await message.reply(
                    "⚠️ **Guruhni avtomatik qo'shishda xatolik**\n\n"
                    "Qo'lda qo'shish uchun administratorga murojaat qiling."
                )
            return
        
        # Обычный пользователь добавил бота - проверяем whitelist
        if not db.is_group_whitelisted(chat_id):
            # Группа не авторизована - покидаем
            try:
                await message.reply(
                    "🚫 **Guruh avtorizatsiya qilinmagan**\n\n"
                    f"📋 Guruh: {chat_title}\n"
                    f"🆔 ID: `{chat_id}`\n\n"
                    "❌ Bu guruh bot ishlashi uchun ruxsat etilganlar ro'yxatida emas.\n"
                    "🤖 Bot avtomatik ravishda guruhni tark etadi.\n\n"
                    "✅ Guruhni qo'shish uchun administratorga murojaat qiling:\n"
                    "📞 Telegram: @admin_username",
                    parse_mode="Markdown"
                )
                
                # Ждем немного чтобы сообщение отправилось
                import asyncio
                await asyncio.sleep(2)
                
                await message.bot.leave_chat(chat_id)
                logger.warning(f"Бот покинул неавторизованную группу {chat_id} ({chat_title}), добавлен пользователем {added_by_user.id}")
                
            except Exception as e:
                logger.error(f"Ошибка при выходе из неавторизованной группы {chat_id}: {e}")
        else:
            # Группа авторизована - приветствуем
            await message.reply(
                f"👋 **Salom, {chat_title}!**\n\n"
                f"🤖 Men video darslar botiman.\n"
                f"✅ Bu guruh avtorizatsiya qilingan.\n\n"
                f"📹 Men sizga muntazam ravishda ta'lim videolarini yuboraman.\n"
                f"⚙️ Sozlamalar uchun administrator bilan bog'laning.",
                parse_mode="Markdown"
            )
            logger.info(f"Бот добавлен в авторизованную группу {chat_id} ({chat_title})")
            
    except Exception as e:
        logger.error(f"Ошибка в обработчике new_chat_members: {e}") 