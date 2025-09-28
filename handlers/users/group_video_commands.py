import asyncio
import json
import os
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from handlers import groups
from db import db
from loader import dp, bot
import logging
from datetime import datetime, timedelta
from utils.safe_admin_notify import safe_send_error_notification

# Импортируем состояния
from handlers.users.group_video_states import GroupVideoStates, DeleteBotMessagesStates
from handlers.users.video_scheduler import schedule_single_group_jobs, schedule_group_jobs_v2, notify_superadmins_season_completed

# Настройка логирования
logger = logging.getLogger(__name__)


async def handle_error_with_notification(error, context, message=None):
    """
    Обрабатывает ошибку с отправкой уведомления администратору
    
    Args:
        error: Объект исключения
        context: Контекст ошибки (название функции)
        message: Объект сообщения для ответа пользователю (опционально)
    """
    try:
        # Логируем ошибку
        error_msg = f"Ошибка в {context}: {str(error)}"
        logger.error(error_msg, exc_info=True)
        
        # Отправляем уведомление администратору
        try:
            await safe_send_error_notification(
                bot=bot,
                error_message=error_msg,
                error_details=str(error)[:500]
            )
        except Exception as notify_error:
            logger.error(f"Не удалось отправить уведомление об ошибке: {notify_error}")
        
        # Отправляем ответ пользователю, если возможно
        if message:
            try:
                await message.answer("❌ **Xatolik yuz berdi!**")
            except Exception as reply_error:
                logger.error(f"Не удалось отправить ответ пользователю: {reply_error}")
                
    except Exception as handler_error:
        logger.critical(f"Критическая ошибка в обработчике ошибок: {handler_error}")

# Вспомогательная функция для отправки сообщения с сохранением ID
async def send_and_save_message(bot, chat_id: int, text: str, **kwargs):
    """Отправляет сообщение и сохраняет его ID в базе данных"""
    try:
        sent_message = await bot.send_message(chat_id, text, **kwargs)
        
        # Сохраняем ID сообщения в базе данных (только для групп)
        if chat_id < 0:  # Отрицательные ID означают группы/каналы
            db.save_bot_message(chat_id, sent_message.message_id, 'text')
            
        return sent_message
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в {chat_id}: {e}")
        raise


# Вспомогательная функция для копирования сообщения с сохранением ID
async def copy_and_save_message(bot, chat_id: int, from_chat_id: int, message_id: int, **kwargs):
    """Копирует сообщение и сохраняет его ID в базе данных"""
    try:
        sent_message = await bot.copy_message(chat_id, from_chat_id, message_id, **kwargs)
        
        # Сохраняем ID сообщения в базе данных (только для групп)
        if chat_id < 0:  # Отрицательные ID означают группы/каналы
            db.save_bot_message(chat_id, sent_message.message_id, 'copy')
            
        return sent_message
    except Exception as e:
        logger.error(f"Ошибка при копировании сообщения в {chat_id}: {e}")
        raise


# Вспомогательная функция для безопасного редактирования сообщений
async def safe_edit_text(callback_query: types.CallbackQuery, text: str, reply_markup=None, parse_mode=None):
    """Безопасно редактирует сообщение, обрабатывая ошибку 'Message is not modified'"""
    try:
        await callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        if "Message is not modified" in str(e):
            # Если сообщение не изменилось, просто отвечаем на callback
            logger.debug(f"Сообщение не изменилось: {e}")
            await callback_query.answer()
        else:
            # Для других ошибок логируем и отвечаем на callback
            logger.warning(f"Ошибка при редактировании сообщения: {e}")
            await callback_query.answer()

# Импортируем необходимые переменные
from data.config import ADMINS

# Список супер-администраторов
SUPER_ADMIN_IDS = [5657091547, 7983512278, 5310261745]

# Команда для предоставления доступа пользователю
@dp.message_handler(commands=['grant_access'])
async def grant_access_command(message: types.Message):
    """Предоставить доступ пользователю на определенное время"""
    user_id = message.from_user.id
    
    # Проверяем права доступа
    if user_id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super-adminlar foydalana oladi.", parse_mode="Markdown")
        return
    
    # Парсим аргументы: /grant_access <user_id> <hours>
    args = message.text.split()
    if len(args) < 3:
        await message.answer(
            "❌ **Noto'g'ri format!**\n\n"
            "**Foydalanish:** `/grant_access <user_id> <soat>`\n"
            "**Misollar:**\n"
            "• `/grant_access 123456789 24` - 24 soat\n"
            "• `/grant_access 123456789 168` - 7 kun\n"
            "• `/grant_access 123456789 720` - 30 kun",
            parse_mode="Markdown"
        )
        return
    
    try:
        target_user_id = int(args[1])
        hours = int(args[2])
        
        if hours <= 0:
            await message.answer("❌ **Soat soni musbat bo'lishi kerak!**")
            return
            
        # Предоставляем доступ
        success = db.grant_access(target_user_id, hours)
        
        if success:
            await message.answer(
                f"✅ **Ruxsat berildi!**\n\n"
                f"👤 **Foydalanuvchi:** `{target_user_id}`\n"
                f"⏰ **Muddat:** {hours} soat\n"
                f"📅 **Tugash vaqti:** {(datetime.now() + timedelta(hours=hours)).strftime('%d.%m.%Y %H:%M')}",
                parse_mode="Markdown"
            )
        else:
            await message.answer("❌ **Xatolik yuz berdi!** Ruxsat berishda muammo bo'ldi.")
            
    except ValueError:
        await message.answer("❌ **Noto'g'ri format!** User ID va soat soni raqam bo'lishi kerak.")
    except Exception as e:
        await handle_error_with_notification(e, "grant_access_command", message)

# Команда для отзыва доступа
@dp.message_handler(commands=['revoke_access'])
async def revoke_access_command(message: types.Message):
    """Отозвать доступ у пользователя"""
    user_id = message.from_user.id
    
    # Проверяем права доступа
    if user_id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super-adminlar foydalana oladi.", parse_mode="Markdown")
        return
    
    # Парсим аргументы: /revoke_access <user_id>
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "❌ **Noto'g'ri format!**\n\n"
            "**Foydalanish:** `/revoke_access <user_id>`\n"
            "**Misollar:**\n"
            "• `/revoke_access 123456789`",
            parse_mode="Markdown"
        )
        return
    
    try:
        target_user_id = int(args[1])
        
        # Отзываем доступ
        success = db.revoke_access(target_user_id)
        
        if success:
            await message.answer(
                f"✅ **Ruxsat olib qo'yildi!**\n\n"
                f"👤 **Foydalanuvchi:** `{target_user_id}`\n"
                f"🚫 **Holat:** Ruxsat yo'q",
                parse_mode="Markdown"
            )
        else:
            await message.answer("❌ **Xatolik yuz berdi!** Ruxsat olib qo'yishda muammo bo'ldi.")
            
    except ValueError:
        await message.answer("❌ **Noto'g'ri format!** User ID raqam bo'lishi kerak.")
    except Exception as e:
        await handle_error_with_notification(e, "revoke_access_command", message)

# Команда для проверки доступа
@dp.message_handler(commands=['check_access'])
async def check_access_command(message: types.Message):
    """Проверить доступ пользователя"""
    user_id = message.from_user.id
    
    # Проверяем права доступа
    if user_id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super-adminlar foydalana oladi.", parse_mode="Markdown")
        return
    
    # Парсим аргументы: /check_access <user_id>
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "❌ **Noto'g'ri format!**\n\n"
            "**Foydalanish:** `/check_access <user_id>`\n"
            "**Misollar:**\n"
            "• `/check_access 123456789`",
            parse_mode="Markdown"
        )
        return
    
    try:
        target_user_id = int(args[1])
        
        # Проверяем доступ
        is_valid = db.is_access_valid(target_user_id)
        
        if is_valid:
            await message.answer(
                f"✅ **Ruxsat mavjud!**\n\n"
                f"👤 **Foydalanuvchi:** `{target_user_id}`\n"
                f"🟢 **Holat:** Faol",
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                f"❌ **Ruxsat yo'q!**\n\n"
                f"👤 **Foydalanuvchi:** `{target_user_id}`\n"
                f"🔴 **Holat:** Ruxsat yo'q yoki muddati tugagan",
                parse_mode="Markdown"
            )
            
    except ValueError:
        await message.answer("❌ **Noto'g'ri format!** User ID raqam bo'lishi kerak.")
    except Exception as e:
        await handle_error_with_notification(e, "check_access_command", message)

# Команда для автоматического отзыва истекшего доступа
@dp.message_handler(commands=['auto_revoke'])
async def auto_revoke_command(message: types.Message):
    """Автоматически отозвать доступ у пользователей с истекшим временем"""
    user_id = message.from_user.id
    
    # Проверяем права доступа
    if user_id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super-adminlar foydalana oladi.", parse_mode="Markdown")
        return
    
    try:
        # Автоматически отзываем доступ
        revoked_count = db.auto_revoke_expired_access()
        
        await message.answer(
            f"✅ **Avtomatik ruxsat olib qo'yildi!**\n\n"
            f"🚫 **Olib qo'yilgan:** {revoked_count} ta foydalanuvchi\n"
            f"⏰ **Vaqt:** {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в auto_revoke_command: {e}")
        await message.answer("❌ **Xatolik yuz berdi!**")

# Команда для просмотра статистики доступа
@dp.message_handler(commands=['access_stats'])
async def access_stats_command(message: types.Message):
    """Показать статистику доступа пользователей"""
    user_id = message.from_user.id
    
    # Проверяем права доступа
    if user_id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super-adminlar foydalana oladi.", parse_mode="Markdown")
        return
    
    try:
        from datetime import datetime
        cursor = db.conn.cursor()
        
        # Получаем статистику
        cursor.execute("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(CASE WHEN is_banned = 0 THEN 1 END) as active_users,
                COUNT(CASE WHEN is_banned = 1 THEN 1 END) as banned_users,
                COUNT(CASE WHEN access_expires_at IS NOT NULL AND access_expires_at > %s THEN 1 END) as users_with_time_limit,
                COUNT(CASE WHEN access_expires_at IS NOT NULL AND access_expires_at <= %s THEN 1 END) as expired_users
            FROM users 
            WHERE is_group = 0
        """, (datetime.now(), datetime.now()))
        
        stats = cursor.fetchone()
        
        # Получаем пользователей с истекшим доступом
        expired_users = db.get_expired_users()
        
        cursor.close()
        
        if stats:
            total_users, active_users, banned_users, users_with_time_limit, expired_users_count = stats
            
            response = f"📊 **Статистика доступа:**\n\n"
            response += f"👥 **Всего пользователей:** {total_users}\n"
            response += f"🟢 **Активных:** {active_users}\n"
            response += f"🔴 **Заблокированных:** {banned_users}\n"
            response += f"⏰ **С ограничением времени:** {users_with_time_limit}\n"
            response += f"⏳ **С истекшим доступом:** {expired_users_count}\n\n"
            
            if expired_users:
                response += f"🚫 **Пользователи с истекшим доступом:**\n"
                for user_id, name, expires_at in expired_users[:5]:  # Показываем только первых 5
                    try:
                        expires_str = expires_at.strftime("%d.%m.%Y %H:%M") if expires_at else "Noma'lum"
                    except:
                        expires_str = "Noma'lum"
                    response += f"• `{user_id}` - {name} (до {expires_str})\n"
                
                if len(expired_users) > 5:
                    response += f"... и еще {len(expired_users) - 5} пользователей\n"
            else:
                response += "✅ **Пользователей с истекшим доступом нет**\n"
            
            response += f"\n⏰ **Время проверки:** {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            await message.answer(response, parse_mode="Markdown")
        else:
            await message.answer("❌ **Ma'lumotlar topilmadi!**")
            
    except Exception as e:
        logger.error(f"Ошибка в access_stats_command: {e}")
        await message.answer("❌ **Xatolik yuz berdi!**")

# Команда для справки по управлению доступом
@dp.message_handler(commands=['access_help'])
async def access_help_command(message: types.Message):
    """Показать справку по командам управления доступом"""
    user_id = message.from_user.id
    
    # Проверяем права доступа
    if user_id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super-adminlar foydalana oladi.", parse_mode="Markdown")
        return
    
    help_text = """
🔐 **Команды управления доступом:**

**Предоставление доступа:**
• `/grant_access <user_id> <часы>` - предоставить доступ на N часов
• Пример: `/grant_access 123456789 24` - доступ на 24 часа
• Пример: `/grant_access 123456789 168` - доступ на 7 дней

**Отзыв доступа:**
• `/revoke_access <user_id>` - отозвать доступ у пользователя
• Пример: `/revoke_access 123456789`

**Проверка доступа:**
• `/check_access <user_id>` - проверить статус доступа
• Пример: `/check_access 123456789`

**Автоматические функции:**
• `/auto_revoke` - отозвать доступ у всех с истекшим временем
• `/access_stats` - показать статистику доступа

**Особенности:**
• Новые пользователи получают доступ на 24 часа автоматически
• Доступ проверяется каждые 6 часов автоматически
• Супер-админы имеют неограниченный доступ
• Группы не имеют ограничений по времени
    """
    
    await message.answer(help_text, parse_mode="Markdown")

logger.info(f"🔄 Регистрируем команды групп в group_video_commands.py, dp ID: {id(dp)}")

# Константы для пагинации
GROUPS_PER_PAGE = 5  # Количество групп на странице (уменьшено для избежания "Message is too long")

def create_paginated_groups_keyboard(groups, page=0, prefix="group", cancel_callback="group_cancel"):
    """
    Создает клавиатуру с пагинацией для списка групп
    
    Args:
        groups: список кортежей (group_id, group_name)
        page: номер страницы (начиная с 0)
        prefix: префикс для callback_data (например, "remove_group", "select_group")
        cancel_callback: callback для кнопки отмены
    
    Returns:
        tuple: (keyboard, total_pages, current_page)
    """
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    if not groups:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("❌ Guruhlar yo'q", callback_data="no_groups"))
        return kb, 0, 0
    
    total_pages = (len(groups) + GROUPS_PER_PAGE - 1) // GROUPS_PER_PAGE
    current_page = min(page, total_pages - 1) if total_pages > 0 else 0
    
    start_idx = current_page * GROUPS_PER_PAGE
    end_idx = min(start_idx + GROUPS_PER_PAGE, len(groups))
    page_groups = groups[start_idx:end_idx]
    
    kb = InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопки групп
    for group_data in page_groups:
        if len(group_data) >= 3:
            group_id, group_name, created_at = group_data
            # Форматируем дату для отображения
            try:
                if created_at:
                    date_str = created_at.strftime("%d.%m %H:%M")
                else:
                    date_str = ""
            except:
                date_str = ""
            
            # Добавляем дату к названию группы
            display_name = f"🏢 {group_name}"
            if date_str:
                display_name += f" ({date_str})"
        else:
            # Обратная совместимость для старых данных
            group_id, group_name = group_data
            display_name = f"🏢 {group_name}"
        
        kb.add(InlineKeyboardButton(
            display_name,
            callback_data=f"{prefix}_{group_id}"
        ))
    
    # Добавляем кнопки навигации если страниц больше одной
    if total_pages > 1:
        nav_buttons = []
        
        # Кнопка "Назад"
        if current_page > 0:
            nav_buttons.append(InlineKeyboardButton(
                "⬅️ Oldingi", 
                callback_data=f"page_{prefix}_{current_page - 1}"
            ))
        
        # Информация о странице
        nav_buttons.append(InlineKeyboardButton(
            f"📄 {current_page + 1}/{total_pages}",
            callback_data="page_info"
        ))
        
        # Кнопка "Вперед"
        if current_page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(
                "➡️ Keyingi", 
                callback_data=f"page_{prefix}_{current_page + 1}"
            ))
        
        # Добавляем кнопки навигации в отдельный ряд
        if nav_buttons:
            kb.row(*nav_buttons)
    
    # Кнопка отмены
    kb.add(InlineKeyboardButton("❌ Bekor qilish", callback_data=cancel_callback))
    
    return kb, total_pages, current_page

def create_paginated_groups_text(groups, page=0, title="Guruhlar"):
    """
    Создает текст сообщения с пагинацией для списка групп
    
    Args:
        groups: список кортежей (group_id, group_name, created_at)
        page: номер страницы (начиная с 0)
        title: заголовок сообщения
    
    Returns:
        str: текст сообщения
    """
    if not groups:
        return f"❌ **{title} topilmadi!**\n\nMa'lumotlar bazasida guruhlar yo'q."
    
    total_pages = (len(groups) + GROUPS_PER_PAGE - 1) // GROUPS_PER_PAGE
    current_page = min(page, total_pages - 1) if total_pages > 0 else 0
    
    start_idx = current_page * GROUPS_PER_PAGE
    end_idx = min(start_idx + GROUPS_PER_PAGE, len(groups))
    page_groups = groups[start_idx:end_idx]
    
    response = f"📋 **{title}:**\n\n"
    
    for group_data in page_groups:
        if len(group_data) >= 3:
            group_id, group_name, created_at = group_data
            # Форматируем дату
            try:
                if created_at:
                    date_str = created_at.strftime("%d.%m.%Y %H:%M")
                else:
                    date_str = "Noma'lum"
            except:
                date_str = "Noma'lum"
            response += f"🏢 **{group_name}**\n🆔 `{group_id}`\n📅 {date_str}\n\n"
        else:
            # Обратная совместимость для старых данных
            group_id, group_name = group_data
            response += f"🏢 **{group_name}**\n🆔 `{group_id}`\n\n"
    
    if total_pages > 1:
        response += f"📄 **Sahifa:** {current_page + 1}/{total_pages}\n\n"
    
    return response

# Команда для настройки видео рассылки в группе
@dp.message_handler(commands=['set_group_video'])
async def set_group_video_command(message: types.Message, state: FSMContext):
    """
    Команда для настройки видео рассылки в группе
    """
    logger.info(f"🚀 set_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    logger.info(f"📝 Текст сообщения: {message.text}")
    
    # Проверяем права пользователя
    user_id = message.from_user.id
    if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
        logger.warning(f"❌ Пользователь {user_id} не имеет прав")
        await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
        return
    
    logger.info(f"✅ Пользователь {user_id} имеет права")
    
    # Определяем тип чата
    chat_type = message.chat.type
    chat_id = message.chat.id
    
    logger.info(f"Тип чата: {chat_type}, ID чата: {chat_id}")
    
    # Сбрасываем предыдущее состояние
    await state.finish()
    
    if chat_type in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
        logger.info("✅ Это группа, отправляем меню")
        # Команда в группе
        await message.answer(
            "📹 **GURUH UCHUN VIDEO TARQATISH SOZLAMALARI**\n\n"
            "🏢 **Loyihani tanlang:**",
            reply_markup=get_project_keyboard()
        )
    else:
        logger.info("⚠️ Это не группа, отправляем личное меню")
        # Команда в личных сообщениях
        await message.answer(
            "📹 **VIDEO TARQATISH SOZLAMALARI**\n\n"
            "🏢 **Loyihani tanlang:**",
            reply_markup=get_project_keyboard()
        )
    
    await state.set_state(GroupVideoStates.waiting_for_project.state)
    await state.update_data(chat_id=chat_id)
    logger.info(f"✅ Состояние установлено, chat_id: {chat_id}")

# Команда для просмотра настроек видео рассылки группы
@dp.message_handler(commands=['show_group_video_settings'])
async def show_group_video_settings(message: types.Message):
    """
    Команда для просмотра текущих настроек видео рассылки в группе
    """
    logger.info(f"🚀 show_group_video_settings вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Проверяем, что команда используется в группе
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            logger.warning("⚠️ Команда вызвана не в группе")
            await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
            return
        
        logger.info("✅ Команда вызвана в группе, продолжаем обработку")
        
        # Получаем настройки группы
        settings = db.get_group_video_settings(chat_id)
        if not settings:
            await message.answer(
                "📹 **GURUH VIDEO SOZLAMALARI**\n\n"
                "❌ **Hech qanday sozlamalar topilmadi!**\n\n"
                "Video tarqatishni yoqish uchun /set_group_video buyrug'ini ishlating."
            , parse_mode="Markdown")
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
        
        # Кнопки управления
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_settings"),
            InlineKeyboardButton("⚙️ O'zgartirish", callback_data="edit_settings")
        )
        
        await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при показе настроек группы: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

logger.info("✅ Команды групп зарегистрированы успешно!")

# Обработчики для выбора времени отправки
@dp.callback_query_handler(lambda c: c.data.startswith("time_"), state=GroupVideoStates.waiting_for_send_times)
async def process_time_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора времени отправки"""
    try:
        action = callback_query.data
        data = await state.get_data()
        temp_settings = data.get("temp_settings")
        
        if not temp_settings:
            await safe_edit_text(callback_query,"❌ **Xatolik!**\n\nSozlamalar topilmadi. Qaytadan boshlang.", parse_mode="Markdown")
            await state.finish()
            return
        
        # Получаем текущие времена отправки
        current_times = temp_settings.get("send_times", ["07:00", "11:00", "20:00"])
        
        if action == "time_preset_default":
            temp_settings["send_times"] = ["07:00", "20:00"]
            await callback_query.answer("🌅 Standart vaqt tanlandi: 07:00, 20:00")
            
        elif action == "time_preset_early":
            temp_settings["send_times"] = ["07:00", "19:00"]
            await callback_query.answer("🌅 Erta vaqt tanlandi: 07:00, 19:00")
            
        elif action == "time_preset_late":
            temp_settings["send_times"] = ["09:00", "21:00"]
            await callback_query.answer("🌅 Kech vaqt tanlandi: 09:00, 21:00")
            
        elif action == "time_preset_mid":
            temp_settings["send_times"] = ["10:00", "18:00"]
            await callback_query.answer("🌅 O'rta vaqt tanlandi: 10:00, 18:00")
            
        elif action == "time_three_times":
            temp_settings["send_times"] = ["07:00", "11:00", "20:00"]
            await callback_query.answer("📅 Kuniga 3 marta: 07:00, 11:00, 20:00")
            
        elif action == "time_custom":
            await safe_edit_text(callback_query,
                "⏰ **Maxsus vaqtlarni kiriting:**\n\n"
                "Vaqtlarni HH:MM formatida kiriting, vergul bilan ajrating.\n"
                "Masalan: 09:00, 15:00, 21:00\n\n"
                "📝 **Eslatma:** Maksimal 5 ta vaqt kiritish mumkin."
            , parse_mode="Markdown")
            await state.set_state(GroupVideoStates.waiting_for_send_times.state)
            await callback_query.answer()
            return
            
        elif action == "time_confirm":
            # Сохраняем настройки с выбранным временем
            saved_settings = await save_group_settings(temp_settings)
            
            # Получаем название группы
            group_name = "Noma'lum guruh"
            chat_id = temp_settings.get("chat_id")
            try:
                group_info = await callback_query.bot.get_chat(chat_id)
                group_name = group_info.title or group_info.first_name or f"Guruh {chat_id}"
            except:
                pass
            
            # Получаем названия сезонов
            centris_season_name = "Noma'lum"
            golden_season_name = "Noma'lum"
            try:
                if saved_settings["centris_enabled"] and saved_settings["centris_season_id"]:
                    centris_season = db.get_season_by_id(saved_settings["centris_season_id"])
                    if centris_season:
                        centris_season_name = centris_season[2]  # season_name
                if saved_settings["golden_enabled"] and saved_settings["golden_season_id"]:
                    golden_season = db.get_season_by_id(saved_settings["golden_season_id"])
                    if golden_season:
                        golden_season_name = golden_season[2]  # season_name
            except:
                pass
            
            send_times = temp_settings.get("send_times", ["07:00", "11:00", "20:00"])
            send_times_str = ", ".join(send_times)
            
            await safe_edit_text(callback_query,
                f"✅ **Sozlamalar saqlandi!**\n\n"
                f"🏢 **Guruh:** {group_name}\n"
                f"🆔 **ID:** {chat_id}\n\n"
                f"🎬 Video tarqatish faollashtirildi.\n\n"
                f"📋 **Sozlamalar:**\n"
                f"• Centris: {'✅ Yoqilgan' if saved_settings['centris_enabled'] else '❌ O''chirilgan'}\n"
                f"  📺 Sezon: {centris_season_name if saved_settings['centris_enabled'] else 'N/A'}\n"
                f"  🎥 Video: {saved_settings['centris_start_video'] + 1 if saved_settings['centris_enabled'] else 'N/A'}\n"
                f"• Golden: {'✅ Yoqilgan' if saved_settings['golden_enabled'] else '❌ O''chirilgan'}\n"
                f"  📺 Sezon: {golden_season_name if saved_settings['golden_enabled'] else 'N/A'}\n"
                f"  🎥 Video: {saved_settings['golden_start_video'] + 1 if saved_settings['golden_enabled'] else 'N/A'}\n\n"
                f"⏰ **Yuborish vaqtlari:** {send_times_str}"
            , parse_mode="Markdown")
            await state.finish()
            return
        
        # Обновляем клавиатуру с новыми временами
        current_times_str = ", ".join(temp_settings.get("send_times", ["07:00", "11:00", "20:00"]))
        await safe_edit_text(callback_query,
            f"⏰ **Yuborish vaqtini tanlang:**\n\n"
            f"Video qachon yuborilishini tanlang. Bir nechta vaqt tanlashingiz mumkin.\n\n"
            f"📋 **Joriy sozlamalar:**\n"
            f"• Loyiha: {temp_settings.get('project', 'N/A')}\n"
            f"• Centris: {'✅' if temp_settings.get('project') in ['centris', 'both'] else '❌'}\n"
            f"• Golden: {'✅' if temp_settings.get('project') in ['golden', 'both'] else '❌'}\n\n"
            f"⏰ **Tanlangan vaqt:** {current_times_str}",
            reply_markup=get_time_selection_keyboard()
        )
        await state.update_data(temp_settings=temp_settings)
        
    except Exception as e:
        logger.error(f"Ошибка при выборе времени: {e}")
        await callback_query.answer("❌ Xatolik yuz berdi!")

# Обработчик для пользовательского ввода времени
@dp.message_handler(state=GroupVideoStates.waiting_for_send_times)
async def process_custom_time_input(message: types.Message, state: FSMContext):
    """Обработчик пользовательского ввода времени"""
    try:
        data = await state.get_data()
        temp_settings = data.get("temp_settings")
        
        if not temp_settings:
            await message.answer("❌ **Xatolik!**\n\nSozlamalar topilmadi. Qaytadan boshlang.", parse_mode="Markdown")
            await state.finish()
            return
        
        # Парсим введенные времена
        time_text = message.text.strip()
        time_parts = [t.strip() for t in time_text.split(',')]
        
        # Валидируем формат времени
        valid_times = []
        for time_part in time_parts:
            try:
                # Проверяем формат HH:MM
                if len(time_part) == 5 and time_part[2] == ':':
                    hour, minute = map(int, time_part.split(':'))
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        valid_times.append(time_part)
                    else:
                        raise ValueError("Invalid time range")
                else:
                    raise ValueError("Invalid time format")
            except ValueError:
                await message.answer(
                    f"❌ **Noto'g'ri vaqt formati:** {time_part}\n\n"
                    "Vaqtni HH:MM formatida kiriting (masalan: 09:30)\n"
                    "Barcha vaqtlarni vergul bilan ajrating.",
                    parse_mode="Markdown"
                )
                return
        
        if len(valid_times) == 0:
            await message.answer("❌ **Hech qanday to'g'ri vaqt topilmadi!**", parse_mode="Markdown")
            return
            
        if len(valid_times) > 5:
            await message.answer("❌ **Maksimal 5 ta vaqt kiritish mumkin!**", parse_mode="Markdown")
            return
        
        # Сохраняем времена
        temp_settings["send_times"] = valid_times
        
        # Показываем подтверждение
        times_str = ", ".join(valid_times)
        await message.answer(
            f"✅ **Maxsus vaqtlar tanlandi!**\n\n"
            f"⏰ **Vaqtlar:** {times_str}\n\n"
            f"Sozlamalarni saqlash uchun \"✅ Tayyor\" tugmasini bosing.",
            reply_markup=get_time_selection_keyboard()
        )
        await state.update_data(temp_settings=temp_settings)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке пользовательского времени: {e}")
        await message.answer("❌ Xatolik yuz berdi!")

# Команда для запуска отправки видео в группе
@dp.message_handler(commands=['start_group_video'])
async def start_group_video_command(message: types.Message):
    """
    Команда для запуска отправки видео в группе
    """
    logger.info(f"🚀 start_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Проверяем, что команда используется в группе
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            logger.warning("⚠️ Команда вызвана не в группе")
            await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
            return
        
        logger.info("✅ Команда вызвана в группе, продолжаем обработку")
        
        # Получаем настройки группы
        settings = db.get_group_video_settings(chat_id)
        if not settings:
            await message.answer(
                "📹 **GURUH VIDEO SOZLAMALARI**\n\n"
                "❌ **Hech qanday sozlamalar topilmadi!**\n\n"
                "Video tarqatishni yoqish uchun /set_group_video buyrug'ini ishlating."
            , parse_mode="Markdown")
            return
        
        # Проверяем что группа в whitelist
        if not db.is_group_whitelisted(chat_id):
            await message.answer(
                "🔒 **GURUH WHITELIST DA EMAS!**\n\n"
                "Video yuborish uchun guruh whitelist ga qo'shilishi kerak."
            , parse_mode="Markdown")
            return
        
        # Запускаем отправку видео
        from handlers.users.video_scheduler import send_group_video_new
        
        centris_enabled = settings[0]
        golden_enabled = settings[4]
        
        sent = False
        
        if centris_enabled:
            centris_season_id = settings[1]
            if centris_season_id:
                result = await send_group_video_new(chat_id, 'centris', centris_season_id)
                sent = sent or result
        
        if golden_enabled:
            golden_season_id = settings[5]
            if golden_season_id:
                result = await send_group_video_new(chat_id, 'golden_lake', golden_season_id)
                sent = sent or result
        
        if sent:
            await message.answer("✅ **Video yuborildi!**\n\n🎬 Keyingi video avtomatik ravishda yuboriladi.", parse_mode="Markdown")
        else:
            await message.answer("⚠️ **Hech qanday yangi video topilmadi!**\n\nBarcha video allaqachon yuborilgan.", parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при запуске видео в группе: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для остановки автоматической отправки видео в группе
@dp.message_handler(commands=['stop_group_video'])
async def stop_group_video_command(message: types.Message):
    """
    Команда для остановки автоматической отправки видео в группе
    """
    logger.info(f"🚀 stop_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Проверяем, что команда используется в группе
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            logger.warning("⚠️ Команда вызвана не в группе")
            await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
            return
        
        logger.info("✅ Команда вызвана в группе, продолжаем обработку")
        
        # Останавливаем автоматическую отправку видео
        db.set_group_video_settings(chat_id, False, None, 0, False, None, 0)
        
        # Удаляем запланированные задачи для этой группы
        from handlers.users.video_scheduler import scheduler
        jobs_to_remove = []
        for job in scheduler.get_jobs():
            if job.id.startswith(f"group_") and str(chat_id) in job.id:
                jobs_to_remove.append(job.id)
        
        for job_id in jobs_to_remove:
            scheduler.remove_job(job_id)
            logger.info(f"Удалена задача {job_id} для группы {chat_id}")
        
        await message.answer("⏹️ **Avtomatik video yuborish to'xtatildi!**\n\nVideo yuborishni qayta yoqish uchun /set_group_video buyrug'ini ishlating.", parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при остановке видео в группе: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для справки по командам групп
@dp.message_handler(commands=['help_group_video'])
async def help_group_video_command(message: types.Message):
    """
    Команда для справки по командам групп
    """
    help_text = """
📹 **GURUH VIDEO BUYRUQLARI**

🏢 **/set_group_video** - Video tarqatish sozlamalari
   • Centris Towers va Golden Lake loyihalari uchun
   • Seson va boshlash videosi tanlash
   • Avtomatik video yuborish yoqish

🎬 **/start_group_video** - Video yuborishni boshlash
   • Hozircha video yuborish
   • Avtomatik yuborish faollashtiriladi

⏹️ **/stop_group_video** - Video yuborishni to'xtatish
   • Avtomatik video yuborish o'chiriladi
   • Barcha rejalangan vazifalar to'xtatiladi

📊 **/show_group_video_settings** - Hozirgi sozlamalar
   • Faol loyihalar
   • Seson va video ma'lumotlari
   • Obuna va whitelist holati

📋 **/admin_show_all_groups_settings** - Barcha guruhlar sozlamalari (Admin)
   • Barcha guruhlar sozlamalari
   • Centris va Golden loyihalari
   • Video va jadval ma'lumotlari

🔒 **/add_group_to_whitelist** - Guruhni whitelist ga qo'shish
   • Faqat super admin uchun
   • Video yuborish ruxsati

❌ **/remove_group_from_whitelist** - Guruhni whitelist dan olib tashlash
   • Faqat super admin uchun
   • Video yuborish ruxsatini bekor qilish

🧪 **/test_group_video** - Video yuborishni test qilish
   • Hozircha video yuborish
   • Test natijalarini ko'rish

🔄 **/reset_group_video** - Guruh sozlamalarini qayta o'rnatish
   • Barcha sozlamalar o'chiriladi
   • Video yuborish to'xtatiladi

📋 **/list_group_videos** - Guruh video ro'yxati
   • Barcha video va holati
   • Statistika va progress

⏭️ **/next_group_video** - Keyingi video yuborish
   • Keyingi ko'rilmagan video
   • Avtomatik yuborish davom etadi

⏭️ **/skip_group_video** - Video o'tkazib yuborish
   • Hozirgi video o'tkazib yuboriladi
   • Keyingi video yuboriladi

📊 **/status_group_video** - Video holati va progress
   • Progress va statistika
   • Avtomatik yuborish vaqti

💪 **/force_group_video** - Video majburiy yuborish
   • Faqat super admin uchun
   • Whitelist ni e'tiborsiz qoldirish

🔄 **/schedule_group_video** - Vazifalarni qayta rejalashtirish
   • Avtomatik yuborish vaqti
   • Yangi rejalar

🐛 **/debug_group_video** - Debug ma'lumotlari
   • Faqat super admin uchun
   • Barcha tizim ma'lumotlari

📋 **/all_group_commands** - Barcha buyruqlar ro'yxati
   • To'liq buyruqlar ro'yxati
   • Kategoriyalar bo'yicha

🏥 **/ping_group_video** - Sistema holatini tekshirish
   • Barcha tizim komponentlari
   • Xatoliklar va holat

📋 **/version_group_video** - Sistema versiyasi
   • Texnik ma'lumotlar
   • Komponentlar va funksiyalar

📊 **/stats_group_video** - Sistema statistikasi
   • Barcha ma'lumotlar
   • Hisoblar va ko'rsatkichlar

🧹 **/cleanup_group_video** - Sistema tozalash
   • Faqat super admin uchun
   • Barcha ma'lumotlarni tozalash

💾 **/backup_group_video** - Reserva nusxasi
   • Faqat super admin uchun
   • Barcha ma'lumotlarni saqlash

🔄 **/restore_group_video** - Reservadan tiklash
   • Faqat super admin uchun
   • Ma'lumotlarni tiklash

📋 **/logs_group_video** - Sistema loglari
   • Faqat super admin uchun
   • Xatoliklar va holat

📊 **/monitor_group_video** - Sistema monitoringi
   • Faqat super admin uchun
   • Resurslar va holat

🚨 **/emergency_group_video** - Extren tizrortatlar
   • Faqat super admin uchun
   • Sistema to'liq to'xtatish

🔄 **/reboot_group_video** - Sistema qayta ishga tushirish
   • Faqat super admin uchun
   • Sistema qayta ishga tushirish

ℹ️ **/info_group_video** - Sistema ma'lumotlari
   • To'liq tizim ma'lumotlari
   • Arxitektura va funksiyalar

🆘 **/support_group_video** - Qo'llab-quvvatlash
   • Aloqa ma'lumotlari
   • Muammolarni hal qilish

ℹ️ **/about_group_video** - Loyiha haqida
   • Loyiha ma'lumotlari
   • Tarix va kelajak

🙏 **/credits_group_video** - Rahmat va tanzimlar
   • Texnologiyalar va jamiyat
   • Ishlab chiqaruvchilar

💰 **/donate_group_video** - Saxovat va qo'llab-quvvatlash
   • Saxovat usullari
   • Imtiyozlar va maqsadlar

📝 **/changelog_group_video** - O'zgarishlar tarixi
   • Versiyalar va yangilanishlar
   • Yaxshilanishlar va tuzatishlar

📄 **/license_group_video** - Litsenziya ma'lumotlari
   • Litsenziya shartlari
   • Foydalanish huquqlari

🔒 **/privacy_group_video** - Maxfiylik siyosati
   • Ma'lumotlar boshqaruvi
   • Maxfiylik va xavfsizlik

📋 **/terms_group_video** - Foydalanish shartlari
   • Foydalanish qoidalari
   • Javobgarlik va cheklar

💡 **Foydalanish:**
1. Guruhda yoki shaxsiy xabarda /set_group_video buyrug'ini ishlating
2. Loyihani tanlang (Centris, Golden yoki ikkalasi)
3. Seson va boshlash videosini tanlang
4. Guruhni tanlang:
   • 🏢 **Hozirgi guruh** - hozirgi guruhga qo'llash
   • 📝 **ID guruhni kiriting** - guruh ID sini qo'lda kiriting
   • 📋 **Ro'yxatdan tanlang** - whitelist dagi barcha guruhlardan tanlang
5. Video avtomatik ravishda yuboriladi

⏰ **Avtomatik yuborish vaqti:**
• Centris Towers: 07:00 va 20:00
• Golden Lake: 11:00
• Vaqt: Toshkent (UTC+5)
"""
    
    await message.answer(help_text, parse_mode="Markdown")

# Команда для добавления группы в whitelist
@dp.message_handler(commands=['add_group_to_whitelist'])
async def add_group_to_whitelist_command(message: types.Message):
    """
    Команда для добавления группы в whitelist
    """
    logger.info(f"🚀 add_group_to_whitelist вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем права пользователя (только супер-админ)
        if user_id not in SUPER_ADMIN_IDS:
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super admin foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Проверяем, что команда используется в группе
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            logger.warning("⚠️ Команда вызвана не в группе")
            await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
            return
        
        logger.info("✅ Команда вызвана в группе, продолжаем обработку")
        
        # Добавляем группу в whitelist
        if db.add_group_to_whitelist(chat_id):
            await message.answer("✅ **Guruh whitelist ga qo'shildi!**\n\n🔓 Endi video yuborish mumkin.", parse_mode="Markdown")
        else:
            await message.answer("❌ **Xatolik yuz berdi!**\n\nGuruh whitelist ga qo'shilmadi.", parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при добавлении группы в whitelist: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для удаления группы из whitelist
@dp.message_handler(commands=['remove_group_from_whitelist'])
async def remove_group_from_whitelist_command(message: types.Message):
    """
    Команда для удаления группы из whitelist
    """
    logger.info(f"🚀 remove_group_from_whitelist вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем права пользователя (только супер-админ)
        if user_id not in SUPER_ADMIN_IDS:
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super admin foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Проверяем, что команда используется в группе
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            logger.warning("⚠️ Команда вызвана не в группе")
            await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
            return
        
        logger.info("✅ Команда вызвана в группе, продолжаем обработку")
        
        # Удаляем группу из whitelist
        if db.remove_group_from_whitelist(chat_id):
            await message.answer("❌ **Guruh whitelist dan olib tashlandi!**\n\n🔒 Endi video yuborish mumkin emas.", parse_mode="Markdown")
        else:
            await message.answer("⚠️ **Guruh whitelist da emas edi!**", parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при удалении группы из whitelist: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для тестирования отправки видео в группе
@dp.message_handler(commands=['test_group_video'])
async def test_group_video_command(message: types.Message):
    """
    Команда для тестирования отправки видео в группе
    """
    logger.info(f"🚀 test_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Проверяем, что команда используется в группе
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            logger.warning("⚠️ Команда вызвана не в группе")
            await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
            return
        
        logger.info("✅ Команда вызвана в группе, продолжаем обработку")
        
        # Получаем настройки группы
        settings = db.get_group_video_settings(chat_id)
        if not settings:
            await message.answer(
                "📹 **GURUH VIDEO SOZLAMALARI**\n\n"
                "❌ **Hech qanday sozlamalar topilmadi!**\n\n"
                "Video tarqatishni yoqish uchun /set_group_video buyrug'ini ishlating."
            , parse_mode="Markdown")
            return
        
        # Проверяем что группа в whitelist
        if not db.is_group_whitelisted(chat_id):
            await message.answer(
                "🔒 **GURUH WHITELIST DA EMAS!**\n\n"
                "Video yuborish uchun guruh whitelist ga qo'shilishi kerak."
            , parse_mode="Markdown")
            return
        
        # Тестируем отправку видео
        from handlers.users.video_scheduler import send_group_video_new
        
        centris_enabled = settings[0]
        golden_enabled = settings[4]
        
        test_results = []
        
        if centris_enabled:
            centris_season_id = settings[1]
            if centris_season_id:
                result = await send_group_video_new(chat_id, 'centris', centris_season_id)
                test_results.append(f"Centris Towers: {'✅ Yuborildi' if result else '❌ Yuborilmadi'}")
        
        if golden_enabled:
            golden_season_id = settings[5]
            if golden_season_id:
                result = await send_group_video_new(chat_id, 'golden_lake', golden_season_id)
                test_results.append(f"Golden Lake: {'✅ Yuborildi' if result else '❌ Yuborilmadi'}")
        
        if test_results:
            response = "🧪 **TEST NATIJALARI:**\n\n" + "\n".join(test_results)
            await message.answer(response, parse_mode="Markdown")
        else:
            await message.answer("⚠️ **Hech qanday faol loyiha topilmadi!**", parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании видео в группе: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для сброса настроек видео группы
@dp.message_handler(commands=['reset_group_video'])
async def reset_group_video_command(message: types.Message):
    """
    Команда для сброса настроек видео группы
    """
    logger.info(f"🚀 reset_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Проверяем, что команда используется в группе
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            logger.warning("⚠️ Команда вызвана не в группе")
            await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
            return
        
        logger.info("✅ Команда вызвана в группе, продолжаем обработку")
        
        # Сбрасываем настройки группы
        db.set_group_video_settings(chat_id, False, None, 0, False, None, 0)
        
        # Сбрасываем просмотренные видео
        db.reset_group_viewed_videos(chat_id)
        
        # Удаляем запланированные задачи для этой группы
        from handlers.users.video_scheduler import scheduler
        jobs_to_remove = []
        for job in scheduler.get_jobs():
            if job.id.startswith(f"group_") and str(chat_id) in job.id:
                jobs_to_remove.append(job.id)
        
        for job_id in jobs_to_remove:
            scheduler.remove_job(job_id)
            logger.info(f"Удалена задача {job_id} для группы {chat_id}")
        
        await message.answer("🔄 **Guruh video sozlamalari qayta o'rnatildi!**\n\nVideo yuborishni qayta yoqish uchun /set_group_video buyrug'ini ishlating.", parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при сбросе настроек группы: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для просмотра списка видео в группе
@dp.message_handler(commands=['list_group_videos'])
async def list_group_videos_command(message: types.Message):
    """
    Команда для просмотра списка видео в группе
    """
    logger.info(f"🚀 list_group_videos вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Проверяем, что команда используется в группе
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            logger.warning("⚠️ Команда вызвана не в группе")
            await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
            return
        
        logger.info("✅ Команда вызвана в группе, продолжаем обработку")
        
        # Получаем настройки группы
        settings = db.get_group_video_settings(chat_id)
        if not settings:
            await message.answer(
                "📹 **GURUH VIDEO SOZLAMALARI**\n\n"
                "❌ **Hech qanday sozlamalar topilmadi!**\n\n"
                "Video tarqatishni yoqish uchun /set_group_video buyrug'ini ishlating."
            , parse_mode="Markdown")
            return
        
        # Формируем список видео
        response = "📹 **GURUH VIDEO RO'YXATI:**\n\n"
        
        centris_enabled = settings[0]
        golden_enabled = settings[4]
        
        if centris_enabled:
            centris_season_id = settings[1]
            if centris_season_id:
                season_name = db.get_season_name(centris_season_id)
                videos = db.get_videos_by_season(centris_season_id)
                viewed_videos = db.get_group_viewed_videos(chat_id)
                
                response += f"🏢 **Centris Towers - {season_name}:**\n"
                for url, title, position in videos:
                    status = "✅" if position in viewed_videos else "⏳"
                    response += f"   {status} {position+1}. {title}\n"
                response += "\n"
        
        if golden_enabled:
            golden_season_id = settings[5]
            if golden_season_id:
                season_name = db.get_season_name(golden_season_id)
                videos = db.get_videos_by_season(golden_season_id)
                viewed_videos = db.get_group_viewed_videos(chat_id)
                
                response += f"🏘️ **Golden Lake - {season_name}:**\n"
                for url, title, position in videos:
                    status = "✅" if position in viewed_videos else "⏳"
                    response += f"   {status} {position+1}. {title}\n"
                response += "\n"
        
        # Добавляем статистику
        total_videos = 0
        viewed_count = 0
        
        if centris_enabled and settings[1]:
            videos = db.get_videos_by_season(settings[1])
            total_videos += len(videos)
            viewed_videos = db.get_group_viewed_videos(chat_id)
            viewed_count += sum(1 for v in videos if v[2] in viewed_videos)
        
        if golden_enabled and settings[5]:
            videos = db.get_videos_by_season(settings[5])
            total_videos += len(videos)
            viewed_videos = db.get_group_viewed_videos(chat_id)
            viewed_count += sum(1 for v in videos if v[2] in viewed_videos)
        
        response += f"📊 **STATISTIKA:**\n"
        response += f"   • Jami video: {total_videos}\n"
        response += f"   • Ko'rilgan: {viewed_count}\n"
        response += f"   • Qoldi: {total_videos - viewed_count}\n"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при показе списка видео группы: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для отправки следующего видео в группе
@dp.message_handler(commands=['next_group_video'])
async def next_group_video_command(message: types.Message):
    """
    Команда для отправки следующего видео в группе
    """
    logger.info(f"🚀 next_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Проверяем, что команда используется в группе
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            logger.warning("⚠️ Команда вызвана не в группе")
            await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
            return
        
        logger.info("✅ Команда вызвана в группе, продолжаем обработку")
        
        # Получаем настройки группы
        settings = db.get_group_video_settings(chat_id)
        if not settings:
            await message.answer(
                "📹 **GURUH VIDEO SOZLAMALARI**\n\n"
                "❌ **Hech qanday sozlamalar topilmadi!**\n\n"
                "Video tarqatishni yoqish uchun /set_group_video buyrug'ini ishlating."
            , parse_mode="Markdown")
            return
        
        # Проверяем что группа в whitelist
        if not db.is_group_whitelisted(chat_id):
            await message.answer(
                "🔒 **GURUH WHITELIST DA EMAS!**\n\n"
                "Video yuborish uchun guruh whitelist ga qo'shilishi kerak."
            , parse_mode="Markdown")
            return
        
        # Отправляем следующее видео
        from handlers.users.video_scheduler import send_group_video_new
        
        centris_enabled = settings[0]
        golden_enabled = settings[4]
        
        sent = False
        
        if centris_enabled:
            centris_season_id = settings[1]
            if centris_season_id:
                result = await send_group_video_new(chat_id, 'centris', centris_season_id)
                sent = sent or result
        
        if golden_enabled and not sent:
            golden_season_id = settings[5]
            if golden_season_id:
                result = await send_group_video_new(chat_id, 'golden_lake', golden_season_id)
                sent = sent or result
        
        if sent:
            await message.answer("✅ **Keyingi video yuborildi!**\n\n🎬 Avtomatik yuborish davom etadi.", parse_mode="Markdown")
        else:
            await message.answer("⚠️ **Hech qanday yangi video topilmadi!**\n\nBarcha video allaqachon yuborilgan.", parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке следующего видео в группе: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для пропуска текущего видео в группе
@dp.message_handler(commands=['skip_group_video'])
async def skip_group_video_command(message: types.Message):
    """
    Команда для пропуска текущего видео в группе
    """
    logger.info(f"🚀 skip_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Проверяем, что команда используется в группе
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            logger.warning("⚠️ Команда вызвана не в группе")
            await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
            return
        
        logger.info("✅ Команда вызвана в группе, продолжаем обработку")
        
        # Получаем настройки группы
        settings = db.get_group_video_settings(chat_id)
        if not settings:
            await message.answer(
                "📹 **GURUH VIDEO SOZLAMALARI**\n\n"
                "❌ **Hech qanday sozlamalar topilmadi!**\n\n"
                "Video tarqatishni yoqish uchun /set_group_video buyrug'ini ishlating."
            , parse_mode="Markdown")
            return
        
        # Проверяем что группа в whitelist
        if not db.is_group_whitelisted(chat_id):
            await message.answer(
                "🔒 **GURUH WHITELIST DA EMAS!**\n\n"
                "Video yuborish uchun guruh whitelist ga qo'shilishi kerak."
            , parse_mode="Markdown")
            return
        
        # Пропускаем текущее видео (отмечаем как просмотренное)
        centris_enabled = settings[0]
        golden_enabled = settings[4]
        
        skipped = False
        
        if centris_enabled:
            centris_season_id = settings[1]
            if centris_season_id:
                # Находим следующее непросмотренное видео
                videos = db.get_videos_by_season(centris_season_id)
                viewed_videos = db.get_group_viewed_videos(chat_id)
                
                for url, title, position in videos:
                    if position not in viewed_videos:
                        # Отмечаем как просмотренное
                        db.mark_group_video_as_viewed(chat_id, position)
                        skipped = True
                        break
        
        if golden_enabled and not skipped:
            golden_season_id = settings[5]
            if golden_season_id:
                # Находим следующее непросмотренное видео
                videos = db.get_videos_by_season(golden_season_id)
                viewed_videos = db.get_group_viewed_videos(chat_id)
                
                for url, title, position in videos:
                    if position not in viewed_videos:
                        # Отмечаем как просмотренное
                        db.mark_group_video_as_viewed(chat_id, position)
                        skipped = True
                        break
        
        if skipped:
            await message.answer("⏭️ **Video o'tkazib yuborildi!**\n\n🎬 Keyingi video avtomatik ravishda yuboriladi.", parse_mode="Markdown")
        else:
            await message.answer("⚠️ **Hech qanday video o'tkazib yuborilmadi!**\n\nBarcha video allaqachon ko'rilgan.", parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при пропуске видео в группе: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для просмотра статуса видео в группе
@dp.message_handler(commands=['status_group_video'])
async def status_group_video_command(message: types.Message):
    """
    Команда для просмотра статуса видео в группе
    """
    logger.info(f"🚀 status_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Проверяем, что команда используется в группе
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            logger.warning("⚠️ Команда вызвана не в группе")
            await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
            return
        
        logger.info("✅ Команда вызвана в группе, продолжаем обработку")
        
        # Получаем настройки группы
        settings = db.get_group_video_settings(chat_id)
        if not settings:
            await message.answer(
                "📹 **GURUH VIDEO SOZLAMALARI**\n\n"
                "❌ **Hech qanday sozlamalar topilmadi!**\n\n"
                "Video tarqatishni yoqish uchun /set_group_video buyrug'ini ishlating."
            , parse_mode="Markdown")
            return
        
        # Формируем статус
        response = "📊 **GURUH VIDEO HOLATI:**\n\n"
        
        centris_enabled = settings[0]
        golden_enabled = settings[4]
        
        # Статус Centris
        if centris_enabled:
            centris_season_id = settings[1]
            centris_start_video = settings[2]
            if centris_season_id:
                season_name = db.get_season_name(centris_season_id)
                videos = db.get_videos_by_season(centris_season_id)
                viewed_videos = db.get_group_viewed_videos(chat_id)
                
                centris_viewed = sum(1 for v in videos if v[2] in viewed_videos)
                centris_total = len(videos)
                centris_progress = (centris_viewed / centris_total * 100) if centris_total > 0 else 0
                
                response += f"🏢 **Centris Towers - {season_name}:**\n"
                response += f"   • Progress: {centris_viewed}/{centris_total} ({centris_progress:.1f}%)\n"
                response += f"   • Boshlash: {centris_start_video + 1}. video\n"
                response += f"   • Status: ✅ Faol\n\n"
        
        # Статус Golden
        if golden_enabled:
            golden_season_id = settings[5]
            golden_start_video = settings[6]
            if golden_season_id:
                season_name = db.get_season_name(golden_season_id)
                videos = db.get_videos_by_season(golden_season_id)
                viewed_videos = db.get_group_viewed_videos(chat_id)
                
                golden_viewed = sum(1 for v in videos if v[2] in viewed_videos)
                golden_total = len(videos)
                golden_progress = (golden_viewed / golden_total * 100) if golden_total > 0 else 0
                
                response += f"🏘️ **Golden Lake - {season_name}:**\n"
                response += f"   • Progress: {golden_viewed}/{golden_total} ({golden_progress:.1f}%)\n"
                response += f"   • Boshlash: {golden_start_video + 1}. video\n"
                response += f"   • Status: ✅ Faol\n\n"
        
        # Общий статус
        if not centris_enabled and not golden_enabled:
            response += "❌ **Hech qanday loyiha faol emas!**\n\n"
        
        # Whitelist статус
        is_whitelisted = db.is_group_whitelisted(chat_id)
        response += f"🔒 **Whitelist:** {'✅ Ruxsat berilgan' if is_whitelisted else '❌ Ruxsat berilmagan'}\n"
        
        # Статус подписки
        is_subscribed = db.get_subscription_status(chat_id)
        response += f"📡 **Obuna:** {'✅ Faol' if is_subscribed else '❌ Faol emas'}\n"
        
        # Следующее видео
        if centris_enabled or golden_enabled:
            response += "\n🎬 **Keyingi video:**\n"
            if centris_enabled:
                response += "   • Centris: Avtomatik 07:00 va 20:00\n"
            if golden_enabled:
                response += "   • Golden: Avtomatik 11:00\n"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при показе статуса группы: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для принудительной отправки видео в группе
@dp.message_handler(commands=['force_group_video'])
async def force_group_video_command(message: types.Message):
    """
    Команда для принудительной отправки видео в группе
    """
    logger.info(f"🚀 force_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем права пользователя (только супер-админ)
        if user_id not in SUPER_ADMIN_IDS:
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super admin foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Проверяем, что команда используется в группе
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            logger.warning("⚠️ Команда вызвана не в группе")
            await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
            return
        
        logger.info("✅ Команда вызвана в группе, продолжаем обработку")
        
        # Получаем настройки группы
        settings = db.get_group_video_settings(chat_id)
        if not settings:
            await message.answer(
                "📹 **GURUH VIDEO SOZLAMALARI**\n\n"
                "❌ **Hech qanday sozlamalar topilmadi!**\n\n"
                "Video tarqatishni yoqish uchun /set_group_video buyrug'ini ishlating."
            , parse_mode="Markdown")
            return
        
        # Принудительно отправляем видео (игнорируем whitelist)
        from handlers.users.video_scheduler import send_group_video_new
        
        centris_enabled = settings[0]
        golden_enabled = settings[4]
        
        sent = False
        
        if centris_enabled:
            centris_season_id = settings[1]
            if centris_season_id:
                # Временно добавляем группу в whitelist
                original_whitelist = db.is_group_whitelisted(chat_id)
                if not original_whitelist:
                    db.add_group_to_whitelist(chat_id, "Force video", user_id)
                
                result = await send_group_video_new(chat_id, 'centris', centris_season_id)
                sent = sent or result
                
                # Восстанавливаем оригинальный статус whitelist
                if not original_whitelist:
                    db.remove_group_from_whitelist(chat_id)
        
        if golden_enabled:
            golden_season_id = settings[5]
            if golden_season_id:
                # Временно добавляем группу в whitelist
                original_whitelist = db.is_group_whitelisted(chat_id)
                if not original_whitelist:
                    db.add_group_to_whitelist(chat_id, "Force video", user_id)
                
                result = await send_group_video_new(chat_id, 'golden_lake', golden_season_id)
                sent = sent or result
                
                # Восстанавливаем оригинальный статус whitelist
                if not original_whitelist:
                    db.remove_group_from_whitelist(chat_id)
        
        if sent:
            await message.answer("✅ **Video majburiy yuborildi!**\n\n🎬 Video yuborish muvaffaqiyatli.", parse_mode="Markdown")
        else:
            await message.answer("⚠️ **Hech qanday yangi video topilmadi!**\n\nBarcha video allaqachon yuborilgan.", parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при принудительной отправке видео в группе: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда: сводный прогресс по всем группам
@dp.message_handler(commands=['all_groups_progress'])
async def all_groups_progress_command(message: types.Message):
    """
    Показать прогресс по ВСЕМ группам: последний индекс видео и списки просмотренных по проектам
    """
    logger.info(f"🚀 all_groups_progress вызвана пользователем {message.from_user.id}")

    try:
        user_id = message.from_user.id

        # Доступ только для админов
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ Sizda bu buyruqni bajarish uchun ruxsat yo'q!\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return

        groups = db.get_all_groups_with_settings() or []
        if not groups:
            await message.answer("📭 Hech qanday guruh topilmadi.")
            return

        # Формируем компактные блоки, разбивая длинный вывод на части
        chunks = []
        current = []
        current_len = 0

        for row in groups:
            # Ожидаем порядок полей из get_all_groups_with_settings
            chat_id = row[0]
            centris_enabled = row[1]
            centris_season_id = row[2]
            centris_start_video = row[3]
            golden_enabled = row[4]
            golden_season_id = row[5]
            golden_start_video = row[6]
            group_name = row[9] if len(row) > 9 else str(chat_id)

            # Просмотренные по проектам
            centris_viewed = []
            golden_viewed = []
            try:
                centris_viewed = db.get_group_viewed_videos_by_project(chat_id, 'centris')
            except Exception:
                pass
            try:
                golden_viewed = db.get_group_viewed_videos_by_project(chat_id, 'golden')
            except Exception:
                pass

            # Человеческие названия сезонов
            centris_season_name = db.get_season_name(centris_season_id) if centris_enabled and centris_season_id else None
            golden_season_name = db.get_season_name(golden_season_id) if golden_enabled and golden_season_id else None

            block_lines = []
            block_lines.append(f"🆔 {chat_id} — {group_name}")

            if centris_enabled and centris_season_id is not None:
                block_lines.append("🏢 Centris:")
                if centris_season_name:
                    block_lines.append(f"   • Mavsum: {centris_season_name} (id={centris_season_id})")
                block_lines.append(f"   • Oxirgi indeks: {centris_start_video}")
                # Ограничим вывод длинных списков
                if centris_viewed:
                    preview = ", ".join(map(str, centris_viewed[:20]))
                    suffix = " …" if len(centris_viewed) > 20 else ""
                    block_lines.append(f"   • Ko'rilgan (pozitsiyalar): [{preview}]{suffix}")
                else:
                    block_lines.append("   • Ko'rilgan: []")

            if golden_enabled and golden_season_id is not None:
                block_lines.append("🏘️ Golden:")
                if golden_season_name:
                    block_lines.append(f"   • Mavsum: {golden_season_name} (id={golden_season_id})")
                block_lines.append(f"   • Oxirgi indeks: {golden_start_video}")
                if golden_viewed:
                    preview = ", ".join(map(str, golden_viewed[:20]))
                    suffix = " …" if len(golden_viewed) > 20 else ""
                    block_lines.append(f"   • Ko'rilgan (pozitsiyalar): [{preview}]{suffix}")
                else:
                    block_lines.append("   • Ko'rilgan: []")

            block = "\n".join(block_lines) + "\n\n"

            if current_len + len(block) > 3500:
                chunks.append("".join(current))
                current = [block]
                current_len = len(block)
            else:
                current.append(block)
                current_len += len(block)

        if current:
            chunks.append("".join(current))

        header = "📊 BARCHA GURUHLAR PROGRESSI:\n\n"
        if chunks:
            # Первый блок с заголовком
            await message.answer(header + chunks[0])
            # Остальные блоки без заголовка
            for chunk in chunks[1:]:
                await message.answer(chunk)
        else:
            await message.answer(header + "(bo'sh)")

    except Exception as e:
        logger.error(f"Ошибка при выводе общего прогресса групп: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для перепланирования задач видео в группе
@dp.message_handler(commands=['schedule_group_video'])
async def schedule_group_video_command(message: types.Message):
    """
    Команда для перепланирования задач видео в группе
    """
    logger.info(f"🚀 schedule_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Проверяем, что команда используется в группе
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            logger.warning("⚠️ Команда вызвана не в группе")
            await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
            return
        
        logger.info("✅ Команда вызвана в группе, продолжаем обработку")
        
        # Получаем настройки группы
        settings = db.get_group_video_settings(chat_id)
        if not settings:
            await message.answer(
                "📹 **GURUH VIDEO SOZLAMALARI**\n\n"
                "❌ **Hech qanday sozlamalar topilmadi!**\n\n"
                "Video tarqatishni yoqish uchun /set_group_video buyrug'ini ishlating."
            , parse_mode="Markdown")
            return
        
        # Перепланируем задачи
        from handlers.users.video_scheduler import schedule_group_jobs
        
        # Удаляем старые задачи для этой группы
        from handlers.users.video_scheduler import scheduler
        jobs_to_remove = []
        for job in scheduler.get_jobs():
            if job.id.startswith(f"group_") and str(chat_id) in job.id:
                jobs_to_remove.append(job.id)
        
        for job_id in jobs_to_remove:
            scheduler.remove_job(job_id)
            logger.info(f"Удалена задача {job_id} для группы {chat_id}")
        
        # Создаем новые задачи
        schedule_single_group_jobs(chat_id)
        
        await message.answer("🔄 **Guruh video vazifalari qayta rejalashtirildi!**\n\n⏰ Avtomatik yuborish vaqti yangilandi.", parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при перепланировании задач группы: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для отладки видео в группе
@dp.message_handler(commands=['debug_group_video'])
async def debug_group_video_command(message: types.Message):
    """
    Команда для отладки видео в группе
    """
    logger.info(f"🚀 debug_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем права пользователя (только супер-админ)
        if user_id not in SUPER_ADMIN_IDS:
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super admin foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Проверяем, что команда используется в группе
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            logger.warning("⚠️ Команда вызвана не в группе")
            await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
            return
        
        logger.info("✅ Команда вызвана в группе, продолжаем обработку")
        
        # Формируем отладочную информацию
        response = "🐛 **DEBUG MA'LUMOTLARI:**\n\n"
        
        # Информация о группе
        response += f"🏷️ **GURUH MA'LUMOTLARI:**\n"
        response += f"   • ID: {chat_id}\n"
        response += f"   • Nomi: {message.chat.title}\n"
        response += f"   • Turi: {message.chat.type}\n"
        response += f"   • Username: {message.chat.username or 'Yo''q'}\n\n"
        
        # Настройки видео
        settings = db.get_group_video_settings(chat_id)
        if settings:
            response += f"📹 **VIDEO SOZLAMALARI:**\n"
            response += f"   • Centris: {'✅' if settings[0] else '❌'} (season: {settings[1]}, start: {settings[2]})\n"
            response += f"   • Golden: {'✅' if settings[4] else '❌'} (season: {settings[5]}, start: {settings[6]})\n\n"
        else:
            response += f"📹 **VIDEO SOZLAMALARI:** ❌ Topilmadi\n\n"
        
        # Whitelist статус
        is_whitelisted = db.is_group_whitelisted(chat_id)
        response += f"🔒 **WHITELIST:** {'✅' if is_whitelisted else '❌'}\n"
        
        # Статус подписки
        is_subscribed = db.get_subscription_status(chat_id)
        response += f"📡 **OBUNA:** {'✅' if is_subscribed else '❌'}\n"
        
        # Просмотренные видео
        viewed_videos = db.get_group_viewed_videos(chat_id)
        response += f"👁️ **KO'RILGAN VIDEO:** {len(viewed_videos)} ta\n"
        if viewed_videos:
            response += f"   • Pozitsiyalar: {sorted(viewed_videos)[:10]}{'...' if len(viewed_videos) > 10 else ''}\n"
        
        # Запланированные задачи
        from handlers.users.video_scheduler import scheduler
        group_jobs = [job for job in scheduler.get_jobs() if job.id.startswith(f"group_") and str(chat_id) in job.id]
        response += f"⏰ **REJALANGAN VAZIFALAR:** {len(group_jobs)} ta\n"
        for job in group_jobs:
            response += f"   • {job.id}: {job.next_run_time}\n"
        
        # Информация о сезонах
        if settings and settings[1]:  # Centris
            centris_videos = db.get_videos_by_season(settings[1])
            response += f"\n🏢 **CENTRIS VIDEOLAR:** {len(centris_videos)} ta\n"
        
        if settings and settings[5]:  # Golden
            golden_videos = db.get_videos_by_season(settings[5])
            response += f"🏘️ **GOLDEN VIDEOLAR:** {len(golden_videos)} ta\n"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при отладке группы: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для показа всех команд групп
@dp.message_handler(commands=['all_group_commands'])
async def all_group_commands_command(message: types.Message):
    """
    Команда для показа всех доступных команд групп
    """
    logger.info(f"🚀 all_group_commands вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем список всех команд
        response = "📋 **BARCHA GURUH BUYRUQLARI:**\n\n"
        
        # Основные команды
        response += "🏢 **ASOSIY BUYRUQLAR:**\n"
        response += "   • /set_group_video - Video tarqatish sozlamalari\n"
        response += "   • /show_group_video_settings - Hozirgi sozlamalar\n"
        response += "   • /admin_show_all_groups_settings - Barcha guruhlar sozlamalari (Admin)\n"
        response += "   • /help_group_video - Batafsil yordam\n\n"
        
        # Управление видео
        response += "🎬 **VIDEO BOSHQARISH:**\n"
        response += "   • /start_group_video - Video yuborishni boshlash\n"
        response += "   • /stop_group_video - Video yuborishni to'xtatish\n"
        response += "   • /next_group_video - Keyingi video yuborish\n"
        response += "   • /skip_group_video - Video o'tkazib yuborish\n"
        response += "   • /test_group_video - Video yuborishni test qilish\n"
        response += "   • /send_all_planned_videos - Barcha rejalashtirilgan videolar\n"
        response += "   • /send_specific_video - Maxsus video yuborish\n\n"
        
        # Информация
        response += "📊 **MA'LUMOTLAR:**\n"
        response += "   • /list_group_videos - Video ro'yxati\n"
        response += "   • /status_group_video - Video holati va progress\n\n"
        
        # Управление
        response += "⚙️ **BOSHQARISH:**\n"
        response += "   • /reset_group_video - Sozlamalarni qayta o'rnatish\n"
        response += "   • /schedule_group_video - Vazifalarni qayta rejalashtirish\n\n"
        
        # Безопасность
        response += "🔒 **XAVFSIZLIK:**\n"
        response += "   • /add_group_to_whitelist - Whitelist ga qo'shish\n"
        response += "   • /remove_group_from_whitelist - Whitelist dan olib tashlash\n\n"
        
        # Супер-админ команды
        if user_id in SUPER_ADMIN_IDS:
            response += "💪 **SUPER ADMIN BUYRUQLARI:**\n"
            response += "   • /remove_group - Guruhni o'chirish (ID bilan yoki tanlash)\n"
            response += "   • /force_group_video - Video majburiy yuborish\n"
            response += "   • /debug_group_video - Debug ma'lumotlari\n"
            response += "   • /cleanup_group_video - Sistema tozalash\n"
            response += "   • /backup_group_video - Reserva nusxasi\n"
            response += "   • /restore_group_video - Reservadan tiklash\n"
            response += "   • /logs_group_video - Sistema loglari\n"
            response += "   • /monitor_group_video - Sistema monitoringi\n"
            response += "   • /emergency_group_video - Extren tizrortatlar\n"
            response += "   • /reboot_group_video - Sistema qayta ishga tushirish\n\n"
        
        # Системные команды
        response += "🖥️ **SISTEMA BUYRUQLARI:**\n"
        response += "   • /ping_group_video - Sistema holatini tekshirish\n"
        response += "   • /version_group_video - Sistema versiyasi\n"
        response += "   • /stats_group_video - Sistema statistikasi\n"
        response += "   • /info_group_video - Sistema ma'lumotlari\n\n"
        
        # Информационные команды
        response += "ℹ️ **MA'LUMOT BUYRUQLARI:**\n"
        response += "   • /about_group_video - Loyiha haqida\n"
        response += "   • /credits_group_video - Rahmatlar\n"
        response += "   • /donate_group_video - Saxovat\n"
        response += "   • /changelog_group_video - Yangilanishlar\n"
        response += "   • /support_group_video - Qo'llab-quvvatlash\n\n"
        
        # Правовые команды
        response += "📄 **HUQUQIY BUYRUQLAR:**\n"
        response += "   • /license_group_video - Litsenziya\n"
        response += "   • /privacy_group_video - Maxfiylik siyosati\n"
        response += "   • /terms_group_video - Foydalanish shartlari\n\n"
        
        # Инструкция по использованию
        response += "💡 **FOYDALANISH:**\n"
        response += "1. Guruhda yoki shaxsiy xabarda /set_group_video buyrug'ini ishlating\n"
        response += "2. Loyihani tanlang (Centris, Golden yoki ikkalasi)\n"
        response += "3. Seson va boshlash videosini tanlang\n"
        response += "4. Guruhni tanlang:\n"
        response += "   • 🏢 Hozirgi guruh - hozirgi guruhga qo'llash\n"
        response += "   • 📝 ID guruhni kiriting - guruh ID sini qo'lda kiriting\n"
        response += "   • 📋 Ro'yxatdan tanlang - whitelist dagi barcha guruhlardan tanlang\n"
        response += "5. Video avtomatik ravishda yuboriladi\n\n"
        
        # Время автоматической отправки
        response += "⏰ **AVTOMATIK YUBORISH VAQTI:**\n"
        response += "• Centris Towers: 07:00 va 20:00\n"
        response += "• Golden Lake: 11:00\n"
        response += "• Vaqt: Toshkent (UTC+5)\n\n"
        
        # Дополнительная информация
        response += "ℹ️ **QO'SHIMCHA MA'LUMOT:**\n"
        response += "• Barcha buyruqlar faqat guruhlarda ishlaydi\n"
        response += "• Faqat adminlar foydalana oladi\n"
        response += "• Video yuborish uchun guruh whitelist da bo'lishi kerak"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при показе всех команд: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для проверки работоспособности системы групп
@dp.message_handler(commands=['ping_group_video'])
async def ping_group_video_command(message: types.Message):
    """
    Команда для проверки работоспособности системы групп
    """
    logger.info(f"🚀 ping_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Проверяем работоспособность системы
        response = "🏥 **SISTEMA HOLATI:**\n\n"
        
        # Проверка базы данных
        try:
            # Проверяем подключение к базе
            test_result = db.get_all_groups_with_settings()
            response += "🗄️ **BAZA MA'LUMOTLARI:** ✅ Faol\n"
            response += f"   • Guruhlar soni: {len(test_result)}\n"
        except Exception as e:
            response += "🗄️ **BAZA MA'LUMOTLARI:** ❌ Xatolik\n"
            response += f"   • Xatolik: {str(e)[:50]}...\n"
        
        # Проверка планировщика
        try:
            from handlers.users.video_scheduler import scheduler
            jobs = scheduler.get_jobs()
            response += f"⏰ **REJALANGAN VAZIFALAR:** ✅ {len(jobs)} ta\n"
        except Exception as e:
            response += "⏰ **REJALANGAN VAZIFALAR:** ❌ Xatolik\n"
            response += f"   • Xatolik: {str(e)[:50]}...\n"
        
        # Проверка сезонов
        try:
            centris_seasons = db.get_seasons_by_project("centris")
            golden_seasons = db.get_seasons_by_project("golden")
            response += f"📺 **SEZONLAR:** ✅ Faol\n"
            response += f"   • Centris: {len(centris_seasons)} ta\n"
            response += f"   • Golden: {len(golden_seasons)} ta\n"
        except Exception as e:
            response += "📺 **SEZONLAR:** ❌ Xatolik\n"
            response += f"   • Xatolik: {str(e)[:50]}...\n"
        
        # Проверка видео
        try:
            total_videos = 0
            if centris_seasons:
                for season_id, _ in centris_seasons:
                    videos = db.get_videos_by_season(season_id)
                    total_videos += len(videos)
            if golden_seasons:
                for season_id, _ in golden_seasons:
                    videos = db.get_videos_by_season(season_id)
                    total_videos += len(videos)
            response += f"🎬 **VIDEOLAR:** ✅ {total_videos} ta\n"
        except Exception as e:
            response += "🎬 **VIDEOLAR:** ❌ Xatolik\n"
            response += f"   • Xatolik: {str(e)[:50]}...\n"
        
        # Проверка групп
        try:
            groups_with_settings = db.get_all_groups_with_settings()
            active_groups = [g for g in groups_with_settings if g[0] or g[4]]  # centris_enabled or golden_enabled
            response += f"👥 **FAOL GURUHLAR:** ✅ {len(active_groups)} ta\n"
        except Exception as e:
            response += "👥 **FAOL GURUHLAR:** ❌ Xatolik\n"
            response += f"   • Xatolik: {str(e)[:50]}...\n"
        
        # Общий статус
        response += "\n🎯 **UMUMIY HOLAT:** ✅ Sistema ishlayapti\n"
        response += "📅 **VAQT:** " + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "\n"
        response += "🌍 **VAQT ZONA:** Toshkent (UTC+5)"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при проверке системы: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для показа версии системы групп
@dp.message_handler(commands=['version_group_video'])
async def version_group_video_command(message: types.Message):
    """
    Команда для показа версии системы групп
    """
    logger.info(f"🚀 version_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем информацию о версии
        response = "📋 **SISTEMA VERSIYASI:**\n\n"
        
        # Версия системы
        response += "🏗️ **ASOSIY MA'LUMOTLAR:**\n"
        response += "   • Sistema: Centris Towers & Golden Lake Bot\n"
        response += "   • Versiya: 2.0.0\n"
        response += "   • Turi: Video tarqatish tizimi\n"
        response += "   • Platforma: Telegram Bot API\n\n"
        
        # Компоненты системы
        response += "🔧 **TIZIM KOMPONENTLARI:**\n"
        response += "   • Framework: aiogram 2.x\n"
        response += "   • Ma'lumotlar bazasi: PostgreSQL\n"
        response += "   • Rejalashtiruvchi: APScheduler\n"
        response += "   • Xavfsizlik: Whitelist + Admin\n\n"
        
        # Функциональность
        response += "✨ **ASOSIY FUNKSIYALAR:**\n"
        response += "   • Avtomatik video yuborish\n"
        response += "   • Centris Towers va Golden Lake\n"
        response += "   • Seson va video boshqarish\n"
        response += "   • Guruh sozlamalari\n"
        response += "   • Xavfsizlik va whitelist\n\n"
        
        # Время работы
        response += "⏰ **ISH VAQTI:**\n"
        response += "   • Centris: 07:00 va 20:00\n"
        response += "   • Golden: 11:00\n"
        response += "   • Vaqt zona: Toshkent (UTC+5)\n\n"
        
        # Команды
        response += "📝 **MAVJUD BUYRUQLAR:**\n"
        response += "   • Asosiy: 3 ta\n"
        response += "   • Video boshqarish: 6 ta\n"
        response += "   • Ma'lumotlar: 2 ta\n"
        response += "   • Boshqarish: 2 ta\n"
        response += "   • Xavfsizlik: 2 ta\n"
        response += "   • Maxsus: 4 ta\n"
        response += "   • **Jami: 19 ta buyruq**\n\n"
        
        # Техническая информация
        response += "⚙️ **TEXNIK MA'LUMOTLAR:**\n"
        response += "   • Python: 3.8+\n"
        response += "   • PostgreSQL: 12+\n"
        response += "   • Redis: Ixtiyoriy\n"
        response += "   • Logging: bot.log\n\n"
        
        # Контакты разработчика
        response += "👨‍💻 **ISHLAB CHIQARUVCHI:**\n"
        response += "   • Telegram: @mohirbek\n"
        response += "   • Loyiha: Centris Towers & Golden Lake\n"
        response += "   • Yangilanish: 2025-yil\n\n"
        
        # Статус
        response += "🎯 **HOLAT:** ✅ Faol va ishlayapti\n"
        response += "📅 **YANGILANGAN:** " + str(datetime.now().strftime("%Y-%m-%d")) + "\n"
        response += "🔮 **KELAJAK:** Yangi funksiyalar va yaxshilanishlar"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при показе версии: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для показа статистики системы групп
@dp.message_handler(commands=['stats_group_video'])
async def stats_group_video_command(message: types.Message):
    """
    Команда для показа статистики системы групп
    """
    logger.info(f"🚀 stats_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем статистику
        response = "📊 **SISTEMA STATISTIKASI:**\n\n"
        
        try:
            # Статистика групп
            groups_with_settings = db.get_all_groups_with_settings()
            total_groups = len(groups_with_settings)
            active_groups = [g for g in groups_with_settings if g[0] or g[4]]  # centris_enabled or golden_enabled
            centris_groups = [g for g in groups_with_settings if g[0]]  # centris_enabled
            golden_groups = [g for g in groups_with_settings if g[4]]  # golden_enabled
            both_groups = [g for g in groups_with_settings if g[0] and g[4]]  # both enabled
            
            response += "👥 **GURUHLAR STATISTIKASI:**\n"
            response += f"   • Jami guruhlar: {total_groups}\n"
            response += f"   • Faol guruhlar: {len(active_groups)}\n"
            response += f"   • Centris guruhlari: {len(centris_groups)}\n"
            response += f"   • Golden guruhlari: {len(golden_groups)}\n"
            response += f"   • Ikkala loyiha: {len(both_groups)}\n\n"
            
            # Статистика сезонов
            centris_seasons = db.get_seasons_by_project("centris")
            golden_seasons = db.get_seasons_by_project("golden")
            
            response += "📺 **SEZONLAR STATISTIKASI:**\n"
            response += f"   • Centris sezonlari: {len(centris_seasons)}\n"
            response += f"   • Golden sezonlari: {len(golden_seasons)}\n"
            response += f"   • Jami sezonlar: {len(centris_seasons) + len(golden_seasons)}\n\n"
            
            # Статистика видео
            total_videos = 0
            centris_videos = 0
            golden_videos = 0
            
            if centris_seasons:
                for season_id, _ in centris_seasons:
                    videos = db.get_videos_by_season(season_id)
                    centris_videos += len(videos)
                    total_videos += len(videos)
            
            if golden_seasons:
                for season_id, _ in golden_seasons:
                    videos = db.get_videos_by_season(season_id)
                    golden_videos += len(videos)
                    total_videos += len(videos)
            
            response += "🎬 **VIDEO STATISTIKASI:**\n"
            response += f"   • Centris videolari: {centris_videos}\n"
            response += f"   • Golden videolari: {golden_videos}\n"
            response += f"   • Jami videolar: {total_videos}\n\n"
            
            # Статистика планировщика
            from handlers.users.video_scheduler import scheduler
            jobs = scheduler.get_jobs()
            group_jobs = [job for job in jobs if job.id.startswith("group_")]
            centris_jobs = [job for job in group_jobs if "centris" in job.id]
            golden_jobs = [job for job in group_jobs if "golden" in job.id]
            
            response += "⏰ **REJALANGAN VAZIFALAR:**\n"
            response += f"   • Jami vazifalar: {len(jobs)}\n"
            response += f"   • Guruh vazifalari: {len(group_jobs)}\n"
            response += f"   • Centris vazifalari: {len(centris_jobs)}\n"
            response += f"   • Golden vazifalari: {len(golden_jobs)}\n\n"
            
            # Статистика просмотров
            total_viewed = 0
            for group in groups_with_settings:
                chat_id = group[0]
                viewed_videos = db.get_group_viewed_videos(chat_id)
                total_viewed += len(viewed_videos)
            
            response += "👁️ **KO'RISH STATISTIKASI:**\n"
            response += f"   • Jami ko'rilgan: {total_viewed}\n"
            response += f"   • O'rtacha guruhda: {total_viewed // max(total_groups, 1)}\n\n"
            
            # Общая статистика
            response += "🎯 **UMUMIY STATISTIKA:**\n"
            response += f"   • Faollik darajasi: {len(active_groups) / max(total_groups, 1) * 100:.1f}%\n"
            response += f"   • Video zichligi: {total_videos / max(len(centris_seasons) + len(golden_seasons), 1):.1f} video/season\n"
            response += f"   • Guruh samaradorligi: {total_viewed / max(total_videos, 1) * 100:.1f}%"
            
        except Exception as e:
            response += f"❌ **Xatolik:** {str(e)[:100]}...\n\n"
            response += "⚠️ Statistika to'liq yig'ilmadi"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при показе статистики: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для очистки системы групп
@dp.message_handler(commands=['cleanup_group_video'])
async def cleanup_group_video_command(message: types.Message):
    """
    Команда для очистки системы групп
    """
    logger.info(f"🚀 cleanup_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя (только супер-админ)
        if user_id not in SUPER_ADMIN_IDS:
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super admin foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем отчет об очистке
        response = "🧹 **SISTEMA TOZALASH:**\n\n"
        
        try:
            # Очистка планировщика
            from handlers.users.video_scheduler import scheduler
            old_jobs = len(scheduler.get_jobs())
            
            # Удаляем все задачи групп
            jobs_to_remove = []
            for job in scheduler.get_jobs():
                if job.id.startswith("group_"):
                    jobs_to_remove.append(job.id)
            
            for job_id in jobs_to_remove:
                scheduler.remove_job(job_id)
            
            new_jobs = len(scheduler.get_jobs())
            response += f"⏰ **REJALANGAN VAZIFALAR:**\n"
            response += f"   • Eski: {old_jobs} ta\n"
            response += f"   • Yangi: {new_jobs} ta\n"
            response += f"   • O'chirilgan: {old_jobs - new_jobs} ta\n\n"
            
            # Очистка просмотренных видео
            groups_with_settings = db.get_all_groups_with_settings()
            total_cleaned = 0
            
            for group in groups_with_settings:
                chat_id = group[0]
                viewed_videos = db.get_group_viewed_videos(chat_id)
                if viewed_videos:
                    db.reset_group_viewed_videos(chat_id)
                    total_cleaned += len(viewed_videos)
            
            response += f"👁️ **KO'RILGAN VIDEO:**\n"
            response += f"   • Tozalangan: {total_cleaned} ta\n"
            response += f"   • Guruhlar: {len(groups_with_settings)} ta\n\n"
            
            # Перепланирование задач для конкретной группы
            schedule_single_group_jobs(chat_id)
            
            response += "🔄 **QAYTA REJALASHTIRISH:** ✅ Bajarildi\n\n"
            
            # Статистика после очистки
            final_jobs = len(scheduler.get_jobs())
            response += f"📊 **YAKUNIY HOLAT:**\n"
            response += f"   • Faol vazifalar: {final_jobs} ta\n"
            response += f"   • Faol guruhlar: {len([g for g in groups_with_settings if g[0] or g[4]])} ta\n"
            response += f"   • Sistema holati: ✅ Toza va faol"
            
        except Exception as e:
            response += f"❌ **Xatolik:** {str(e)[:100]}...\n\n"
            response += "⚠️ Tozalash to'liq bajarilmadi"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке системы: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для резервного копирования системы групп
@dp.message_handler(commands=['backup_group_video'])
async def backup_group_video_command(message: types.Message):
    """
    Команда для резервного копирования системы групп
    """
    logger.info(f"🚀 backup_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя (только супер-админ)
        if user_id not in SUPER_ADMIN_IDS:
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super admin foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем отчет о резервном копировании
        response = "💾 **RESERVA NUSXASI:**\n\n"
        
        try:
            # Создаем резервную копию настроек групп
            groups_with_settings = db.get_all_groups_with_settings()
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'total_groups': len(groups_with_settings),
                'groups': []
            }
            
            for group in groups_with_settings:
                chat_id = group[0]
                group_info = {
                    'chat_id': chat_id,
                    'centris_enabled': group[1],
                    'centris_season_id': group[2],
                    'centris_start_video': group[3],
                    'golden_enabled': group[4],
                    'golden_season_id': group[5],
                    'golden_start_video': group[6],
                    'viewed_videos': db.get_group_viewed_videos(chat_id),
                    'is_subscribed': db.get_subscription_status(chat_id),
                    'is_whitelisted': db.is_group_whitelisted(chat_id)
                }
                backup_data['groups'].append(group_info)
            
            # Сохраняем резервную копию в файл
            import json
            backup_filename = f"group_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(backup_filename, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            response += f"📁 **FAYL:** {backup_filename}\n"
            response += f"📅 **VAQT:** {backup_data['timestamp']}\n"
            response += f"👥 **GURUHLAR:** {backup_data['total_groups']} ta\n\n"
            
            # Детали резервной копии
            centris_groups = [g for g in backup_data['groups'] if g['centris_enabled']]
            golden_groups = [g for g in backup_data['groups'] if g['golden_enabled']]
            both_groups = [g for g in backup_data['groups'] if g['centris_enabled'] and g['golden_enabled']]
            
            response += "📊 **MA'LUMOTLAR:**\n"
            response += f"   • Centris guruhlari: {len(centris_groups)}\n"
            response += f"   • Golden guruhlari: {len(golden_groups)}\n"
            response += f"   • Ikkala loyiha: {len(both_groups)}\n"
            response += f"   • Faol guruhlar: {len([g for g in backup_data['groups'] if g['centris_enabled'] or g['golden_enabled']])}\n\n"
            
            # Статус
            response += "✅ **RESERVA NUSXASI:** Muvaffaqiyatli yaratildi\n"
            response += f"📁 **JOYLASHUV:** {backup_filename}\n"
            response += "💡 **ESLATMA:** Faylni xavfsiz joyda saqlang"
            
        except Exception as e:
            response += f"❌ **Xatolik:** {str(e)[:100]}...\n\n"
            response += "⚠️ Reserva nusxasi yaratilmadi"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при резервном копировании: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для восстановления из резервной копии
@dp.message_handler(commands=['restore_group_video'])
async def restore_group_video_command(message: types.Message):
    """
    Команда для восстановления из резервной копии
    """
    logger.info(f"🚀 restore_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя (только супер-админ)
        if user_id not in SUPER_ADMIN_IDS:
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super admin foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} не имеет прав")
        
        # Проверяем аргументы команды
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "📁 **RESTORE BUYRUQI:**\n\n"
                "💡 **Foydalanish:**\n"
                "/restore_group_video <fayl_nomi>\n\n"
                "📋 **Mavjud fayllar:**\n"
                "Fayllarni ko'rish uchun /backup_group_video buyrug'ini ishlating"
            , parse_mode="Markdown")
            return
        
        filename = args[1]
        
        # Формируем отчет о восстановлении
        response = "🔄 **RESTORE JARAYONI:**\n\n"
        
        try:
            # Читаем резервную копию
            import json
            import os
            
            if not os.path.exists(filename):
                await message.answer(f"❌ **Fayl topilmadi:** {filename}\n\nIltimos, to'g'ri fayl nomini kiriting.", parse_mode="Markdown")
                return
            
            with open(filename, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            response += f"📁 **FAYL:** {filename}\n"
            response += f"📅 **VAQT:** {backup_data.get('timestamp', 'N/A')}\n"
            response += f"👥 **GURUHLAR:** {backup_data.get('total_groups', 0)} ta\n\n"
            
            # Восстанавливаем данные
            restored_groups = 0
            for group_info in backup_data.get('groups', []):
                try:
                    chat_id = group_info['chat_id']
                    
                    # Восстанавливаем настройки видео
                    db.set_group_video_settings(
                        chat_id,
                        group_info['centris_enabled'],
                        group_info['centris_season_id'],
                        group_info['centris_start_video'],
                        group_info['golden_enabled'],
                        group_info['golden_season_id'],
                        group_info['golden_start_video']
                    )
                    
                    # Восстанавливаем просмотренные видео
                    if group_info.get('viewed_videos'):
                        viewed_videos = group_info['viewed_videos']
                        cursor = db.conn.cursor()
                        cursor.execute(
                            "UPDATE group_video_settings SET viewed_videos = %s WHERE chat_id = %s",
                            (json.dumps(viewed_videos), str(chat_id))
                        )
                        db.conn.commit()
                        cursor.close()
                    
                    # Восстанавливаем статус подписки
                    if group_info.get('is_subscribed'):
                        db.set_subscription_status(chat_id, group_info['is_subscribed'])
                    
                    # Восстанавливаем whitelist статус
                    if group_info.get('is_whitelisted'):
                        if not db.is_group_whitelisted(chat_id):
                            db.add_group_to_whitelist(chat_id, "Restored from backup", user_id)
                    
                    restored_groups += 1
                    
                except Exception as e:
                    logger.error(f"Ошибка при восстановлении группы {chat_id}: {e}")
                    continue
            
            response += f"✅ **RESTORE NATIJASI:**\n"
            response += f"   • Muvaffaqiyatli: {restored_groups} ta\n"
            response += f"   • Xatoliklar: {len(backup_data.get('groups', [])) - restored_groups} ta\n\n"
            
            # Перепланирование задач для конкретной группы
            schedule_single_group_jobs(chat_id)
            
            response += "🔄 **QAYTA REJALASHTIRISH:** ✅ Bajarildi\n\n"
            response += "🎯 **HOLAT:** Sistema tiklandi va ishlayapti"
            
        except Exception as e:
            response += f"❌ **Xatolik:** {str(e)[:100]}...\n\n"
            response += "⚠️ Restore jarayoni to'liq bajarilmadi"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при восстановлении: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для просмотра логов системы групп
@dp.message_handler(commands=['logs_group_video'])
async def logs_group_video_command(message: types.Message):
    """
    Команда для просмотра логов системы групп
    """
    logger.info(f"🚀 logs_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя (только супер-админ)
        if user_id not in SUPER_ADMIN_IDS:
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super admin foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем отчет о логах
        response = "📋 **SISTEMA LOGLARI:**\n\n"
        
        try:
            # Читаем последние строки лог-файла
            log_filename = 'bot.log'
            
            if not os.path.exists(log_filename):
                await message.answer("❌ **Log fayli topilmadi:** bot.log\n\nIltimos, log faylini tekshiring.", parse_mode="Markdown")
                return
            
            # Читаем последние 20 строк
            with open(log_filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Получаем последние строки
            last_lines = lines[-20:] if len(lines) > 20 else lines
            
            response += f"📁 **FAYL:** {log_filename}\n"
            response += f"📊 **JAMI SATRLAR:** {len(lines)}\n"
            response += f"📖 **OXIRGI:** {len(last_lines)} ta\n\n"
            
            # Анализируем логи
            error_count = sum(1 for line in last_lines if 'ERROR' in line)
            warning_count = sum(1 for line in last_lines if 'WARNING' in line)
            info_count = sum(1 for line in last_lines if 'INFO' in line)
            
            response += "📊 **LOGLAR HOLATI:**\n"
            response += f"   • Xatoliklar: {error_count} ta\n"
            response += f"   • Ogohlantirishlar: {warning_count} ta\n"
            response += f"   • Ma'lumotlar: {info_count} ta\n\n"
            
            # Показываем последние логи
            response += "📝 **OXIRGI LOGLAR:**\n"
            for line in last_lines:
                # Ограничиваем длину строки
                if len(line) > 100:
                    line = line[:97] + "..."
                response += f"   {line.strip()}\n"
            
            # Статус системы
            if error_count == 0:
                response += "\n🎯 **HOLAT:** ✅ Sistema yaxshi ishlayapti"
            elif error_count <= 2:
                response += "\n🎯 **HOLAT:** ⚠️ Kichik muammolar bor"
            else:
                response += "\n🎯 **HOLAT:** ❌ Ko'p xatoliklar bor"
            
        except Exception as e:
            response += f"❌ **Xatolik:** {str(e)[:100]}...\n\n"
            response += "⚠️ Loglar to'liq o'qilmadi"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при просмотре логов: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для мониторинга системы групп
@dp.message_handler(commands=['monitor_group_video'])
async def monitor_group_video_command(message: types.Message):
    """
    Команда для мониторинга системы групп
    """
    logger.info(f"🚀 monitor_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя (только супер-админ)
        if user_id not in SUPER_ADMIN_IDS:
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super admin foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем отчет о мониторинге
        response = "📊 **SISTEMA MONITORINGI:**\n\n"
        
        try:
            # Системная информация
            import psutil
            import time
            
            # CPU и память
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            response += "💻 **SISTEMA RESURSLARI:**\n"
            response += f"   • CPU: {cpu_percent}%\n"
            response += f"   • RAM: {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)\n"
            response += f"   • Disk: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)\n\n"
            
            # Процессы Python
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if 'python' in proc.info['name'].lower():
                        python_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            response += "🐍 **PYTHON PROTSESLAR:**\n"
            response += f"   • Jami: {len(python_processes)} ta\n"
            if python_processes:
                total_cpu = sum(p['cpu_percent'] for p in python_processes)
                total_memory = sum(p['memory_percent'] for p in python_processes)
                response += f"   • CPU: {total_cpu:.1f}%\n"
                response += f"   • RAM: {total_memory:.1f}%\n"
            response += "\n"
            
            # Мониторинг базы данных
            try:
                # Проверяем подключение к базе
                start_time = time.time()
                test_result = db.get_all_groups_with_settings()
                db_response_time = (time.time() - start_time) * 1000
                
                response += "🗄️ **BAZA MA'LUMOTLARI:**\n"
                response += f"   • Holat: ✅ Faol\n"
                response += f"   • Javob vaqti: {db_response_time:.1f}ms\n"
                response += f"   • Guruhlar: {len(test_result)} ta\n"
            except Exception as e:
                response += "🗄️ **BAZA MA'LUMOTLARI:**\n"
                response += f"   • Holat: ❌ Xatolik\n"
                response += f"   • Xatolik: {str(e)[:50]}...\n"
            response += "\n"
            
            # Мониторинг планировщика
            try:
                from handlers.users.video_scheduler import scheduler
                jobs = scheduler.get_jobs()
                group_jobs = [job for job in jobs if job.id.startswith("group_")]
                
                response += "⏰ **REJALANGAN VAZIFALAR:**\n"
                response += f"   • Jami: {len(jobs)} ta\n"
                response += f"   • Guruh: {len(group_jobs)} ta\n"
                response += f"   • Holat: ✅ Faol\n"
            except Exception as e:
                response += "⏰ **REJALANGAN VAZIFALAR:**\n"
                response += f"   • Holat: ❌ Xatolik\n"
                response += f"   • Xatolik: {str(e)[:50]}...\n"
            response += "\n"
            
            # Мониторинг логов
            try:
                log_filename = 'bot.log'
                if os.path.exists(log_filename):
                    with open(log_filename, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # Анализируем последние 100 строк
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                    error_count = sum(1 for line in recent_lines if 'ERROR' in line)
                    warning_count = sum(1 for line in recent_lines if 'WARNING' in line)
                    
                    response += "📋 **LOGLAR HOLATI:**\n"
                    response += f"   • Jami satrlar: {len(lines)}\n"
                    response += f"   • Oxirgi 100 satrda:\n"
                    response += f"     - Xatoliklar: {error_count} ta\n"
                    response += f"     - Ogohlantirishlar: {warning_count} ta\n"
                    
                    # Оценка состояния
                    if error_count == 0:
                        response += f"   • Holat: ✅ Yaxshi\n"
                    elif error_count <= 2:
                        response += f"   • Holat: ⚠️ O'rtacha\n"
                    else:
                        response += f"   • Holat: ❌ Yomon\n"
                else:
                    response += "📋 **LOGLAR HOLATI:**\n"
                    response += f"   • Holat: ❌ Fayl topilmadi\n"
            except Exception as e:
                response += "📋 **LOGLAR HOLATI:**\n"
                response += f"   • Holat: ❌ Xatolik\n"
                response += f"   • Xatolik: {str(e)[:50]}...\n"
            response += "\n"
            
            # Общая оценка системы
            response += "🎯 **UMUMIY HOLAT:**\n"
            
            # Определяем общее состояние
            system_score = 100
            
            # Снижаем оценку за ошибки
            if error_count > 5:
                system_score -= 30
            elif error_count > 2:
                system_score -= 15
            
            # Снижаем оценку за высокую нагрузку
            if cpu_percent > 80:
                system_score -= 20
            elif cpu_percent > 60:
                system_score -= 10
            
            # Снижаем оценку за нехватку памяти
            if memory.percent > 90:
                system_score -= 20
            elif memory.percent > 80:
                system_score -= 10
            
            if system_score >= 90:
                status = "✅ Yaxshi"
            elif system_score >= 70:
                status = "⚠️ O'rtacha"
            else:
                status = "❌ Yomon"
            
            response += f"   • Ball: {system_score}/100\n"
            response += f"   • Holat: {status}\n"
            response += f"   • Vaqt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
        except Exception as e:
            response += f"❌ **Xatolik:** {str(e)[:100]}...\n\n"
            response += "⚠️ Monitoring to'liq bajarilmadi"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при мониторинге: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для диагностики планировщика
@dp.message_handler(commands=['scheduler_debug'])
async def scheduler_debug_command(message: types.Message):
    """Отладка планировщика видео"""
    from data.config import SUPER_ADMIN_IDS
    
    if message.from_user.id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda ushbu buyruqni ishlatish huquqi yo'q!**")
        return
    
    try:
        from handlers.users.video_scheduler import scheduler
        
        response = "🔧 **SCHEDULER DEBUG**\n\n"
        
        # Проверяем статус планировщика
        response += f"📊 **STATUS:**\n"
        response += f"   • Running: {'✅' if scheduler.running else '❌'}\n"
        response += f"   • Jobs count: {len(scheduler.get_jobs())}\n\n"
        
        # Список всех задач
        jobs = scheduler.get_jobs()
        if jobs:
            response += f"📋 **PLANNED JOBS ({len(jobs)}):**\n"
            for job in jobs[:10]:  # Показываем первые 10
                next_run = job.next_run_time.strftime('%H:%M %d.%m') if job.next_run_time else "Never"
                response += f"   • `{job.id}`: {next_run}\n"
            
            if len(jobs) > 10:
                response += f"   • ... и еще {len(jobs) - 10} задач\n"
        else:
            response += "❌ **Нет запланированных задач!**\n"
        
        response += "\n"
        
        # Проверяем активные группы
        groups = db.get_all_groups_with_settings()
        response += f"👥 **ACTIVE GROUPS:** {len(groups)}\n"
        
        for i, group in enumerate(groups[:5]):  # Первые 5 групп
            chat_id = group[0]
            response += f"   • Group {chat_id}\n"
        
        if len(groups) > 5:
            response += f"   • ... и еще {len(groups) - 5} групп\n"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        await handle_error_with_notification(e, "scheduler_debug_command", message)


# Команда для перезапуска планировщика
@dp.message_handler(commands=['restart_scheduler'])
async def restart_scheduler_command(message: types.Message):
    """Перезапуск планировщика видео"""
    from data.config import SUPER_ADMIN_IDS
    
    if message.from_user.id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda ushbu buyruqni ishlatish huquqi yo'q!**")
        return
    
    try:
        from handlers.users.video_scheduler import scheduler, init_scheduler
        
        await message.answer("🔄 **Перезапускаем планировщик...**")
        
        # Останавливаем планировщик
        if scheduler.running:
            scheduler.shutdown()
            await message.answer("⏹️ **Планировщик остановлен**")
        
        # Запускаем заново
        await init_scheduler()
        
        # Проверяем результат
        jobs_count = len(scheduler.get_jobs())
        
        response = "✅ **Планировщик перезапущен!**\n\n"
        response += f"📊 **Статус:**\n"
        response += f"   • Running: {'✅' if scheduler.running else '❌'}\n"
        response += f"   • Jobs: {jobs_count}\n"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        await handle_error_with_notification(e, "restart_scheduler_command", message)


# Команда для тестовой отправки видео
@dp.message_handler(commands=['test_send_video'])
async def test_send_video_command(message: types.Message):
    """Тестовая отправка видео в группу"""
    from data.config import SUPER_ADMIN_IDS
    
    if message.from_user.id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda ushbu buyruqni ishlatish huquqi yo'q!**")
        return
    
    # Проверяем, что команда вызвана в группе
    if message.chat.type not in ['group', 'supergroup']:
        await message.answer("❌ **Bu buyruq faqat guruhda ishlatiladi!**")
        return
    
    try:
        chat_id = message.chat.id
        
        await message.answer("🧪 **Тестируем отправку видео...**")
        
        # Получаем настройки группы
        group_settings = db.get_group_video_settings(chat_id)
        if not group_settings:
            await message.answer("❌ **Группа не настроена для отправки видео!**")
            return
        
        from handlers.users.video_scheduler import send_group_video_new
        
        # Распаковываем настройки
        centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video = group_settings[:6]
        
        if centris_enabled and centris_season_id:
            await message.answer("🏢 **Отправляем Centris видео...**")
            result = await send_group_video_new(chat_id, 'centris', centris_season_id)
            if result:
                await message.answer("✅ **Centris видео отправлено!**")
            else:
                await message.answer("❌ **Ошибка отправки Centris видео**")
        
        if golden_enabled and golden_season_id:
            await message.answer("🌊 **Отправляем Golden Lake видео...**")
            result = await send_group_video_new(chat_id, 'golden_lake', golden_season_id)
            if result:
                await message.answer("✅ **Golden Lake видео отправлено!**")
            else:
                await message.answer("❌ **Ошибка отправки Golden Lake видео**")
        
        if not (centris_enabled or golden_enabled):
            await message.answer("❌ **Нет активных проектов для отправки!**")
        
    except Exception as e:
        await handle_error_with_notification(e, "test_send_video_command", message)


# Команда для диагностики конкретной группы
@dp.message_handler(commands=['diagnose_group'])
async def diagnose_group_command(message: types.Message):
    """Диагностика конкретной группы по ID"""
    from data.config import SUPER_ADMIN_IDS
    
    if message.from_user.id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda ushbu buyruqni ishlatish huquqi yo'q!**")
        return
    
    try:
        # Получаем ID группы из аргументов или используем текущий чат
        args = message.get_args().strip()
        if args:
            try:
                chat_id = int(args)
            except ValueError:
                await message.answer("❌ **Noto'g'ri group ID format!** Misol: `/diagnose_group -4867322212`")
                return
        else:
            if message.chat.type in ['group', 'supergroup']:
                chat_id = message.chat.id
            else:
                await message.answer("❌ **Group ID kiriting yoki guruhda ishlatiladi!** Misol: `/diagnose_group -4867322212`")
                return
        
        response = f"🔍 **GROUP DIAGNOSTICS**\n\n"
        response += f"👥 **Group ID:** `{chat_id}`\n\n"
        
        # Проверяем whitelist
        is_whitelisted = db.is_group_whitelisted(chat_id)
        response += f"✅ **Whitelist:** {'✅ Да' if is_whitelisted else '❌ НЕТ!'}\n"
        
        # Проверяем настройки группы
        group_settings = db.get_group_video_settings(chat_id)
        if group_settings:
            centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video = group_settings[:6]
            
            response += f"⚙️ **Настройки:**\n"
            response += f"   • Centris: {'✅' if centris_enabled else '❌'} (сезон: {centris_season_id}, видео: {centris_start_video})\n"
            response += f"   • Golden: {'✅' if golden_enabled else '❌'} (сезон: {golden_season_id}, видео: {golden_start_video})\n"
            
            # Проверяем времена отправки
            if len(group_settings) >= 7:
                send_times_json = group_settings[6]
                try:
                    if send_times_json:
                        import json
                        send_times = json.loads(send_times_json)
                        response += f"⏰ **Времена:** {', '.join(send_times)}\n"
                    else:
                        response += f"⏰ **Времена:** По умолчанию\n"
                except:
                    response += f"⏰ **Времена:** Ошибка чтения\n"
        else:
            response += f"❌ **Настройки группы НЕ НАЙДЕНЫ!**\n"
        
        # Проверяем задачи планировщика
        from handlers.users.video_scheduler import scheduler
        group_jobs = [job for job in scheduler.get_jobs() if f"group_{chat_id}_" in job.id]
        response += f"📋 **Задачи планировщика:** {len(group_jobs)}\n"
        
        for job in group_jobs[:3]:  # Показываем первые 3
            next_run = job.next_run_time.strftime('%H:%M %d.%m') if job.next_run_time else "Never"
            response += f"   • `{job.id}`: {next_run}\n"
        
        if len(group_jobs) > 3:
            response += f"   • ... и еще {len(group_jobs) - 3}\n"
        
        # Рекомендации
        response += f"\n🔧 **Рекомендации:**\n"
        if not is_whitelisted:
            response += f"• Добавить в whitelist: `/add_group_whitelist {chat_id}`\n"
        if not group_settings:
            response += f"• Настроить группу: `/set_group_video`\n"
        if len(group_jobs) == 0:
            response += f"• Перезапустить планировщик: `/restart_scheduler`\n"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        await handle_error_with_notification(e, "diagnose_group_command", message)


# Команда для быстрого добавления группы в whitelist
@dp.message_handler(commands=['quick_whitelist'])
async def quick_whitelist_command(message: types.Message):
    """Быстро добавить группу в whitelist по ID"""
    from data.config import SUPER_ADMIN_IDS
    
    if message.from_user.id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda ushbu buyruqni ishlatish huquqi yo'q!**")
        return
    
    try:
        # Получаем ID группы из аргументов или используем текущий чат
        args = message.get_args().strip()
        if args:
            try:
                chat_id = int(args)
            except ValueError:
                await message.answer("❌ **Noto'g'ri group ID format!** Misol: `/quick_whitelist -4867322212`")
                return
        else:
            if message.chat.type in ['group', 'supergroup']:
                chat_id = message.chat.id
            else:
                await message.answer("❌ **Group ID kiriting yoki guruhda ishlatiladi!** Misol: `/quick_whitelist -4867322212`")
                return
        
        # Проверяем, уже ли в whitelist
        if db.is_group_whitelisted(chat_id):
            await message.answer(f"✅ **Группа `{chat_id}` уже в whitelist!**", parse_mode="Markdown")
            return
        
        # Добавляем в whitelist
        success = db.add_group_to_whitelist(chat_id)
        if success:
            await message.answer(f"✅ **Группа `{chat_id}` добавлена в whitelist!**", parse_mode="Markdown")
            
            # Перезапускаем планировщик для этой группы
            from handlers.users.video_scheduler import schedule_single_group_jobs
            result = schedule_single_group_jobs(chat_id)
            if result:
                await message.answer("🔄 **Задачи планировщика обновлены для группы!**")
        else:
            await message.answer(f"❌ **Ошибка добавления группы `{chat_id}` в whitelist!**", parse_mode="Markdown")
        
    except Exception as e:
        await handle_error_with_notification(e, "quick_whitelist_command", message)


# Команда для принудительной отправки видео прямо сейчас
@dp.message_handler(commands=['force_send_now'])
async def force_send_now_command(message: types.Message):
    """Принудительно отправить видео прямо сейчас"""
    from data.config import SUPER_ADMIN_IDS
    
    if message.from_user.id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda ushbu buyruqni ishlatish huquqi yo'q!**")
        return
    
    # Проверяем, что команда вызвана в группе
    if message.chat.type not in ['group', 'supergroup']:
        await message.answer("❌ **Bu buyruq faqat guruhda ishlatiladi!**")
        return
    
    try:
        chat_id = message.chat.id
        
        await message.answer("🚀 **ПРИНУДИТЕЛЬНАЯ ОТПРАВКА ВИДЕО**\n\n⏰ Время: " + 
                           datetime.now().strftime("%H:%M:%S") + "\n🔄 Отправляем...")
        
        # Получаем настройки группы
        group_settings = db.get_group_video_settings(chat_id)
        if not group_settings:
            await message.answer("❌ **Группа не настроена!** Используйте `/set_group_video`")
            return
        
        # Проверяем whitelist
        if not db.is_group_whitelisted(chat_id):
            await message.answer("❌ **Группа не в whitelist!** Используйте `/quick_whitelist`")
            return
        
        from handlers.users.video_scheduler import send_group_video_new
        
        # Распаковываем настройки
        centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video = group_settings[:6]
        
        success_count = 0
        
        if centris_enabled and centris_season_id:
            await message.answer("🏢 **Отправляем Centris видео...**")
            result = await send_group_video_new(chat_id, 'centris', centris_season_id, centris_start_video)
            if result:
                await message.answer("✅ **Centris видео отправлено!**")
                success_count += 1
            else:
                await message.answer("❌ **Ошибка отправки Centris видео**")
        
        if golden_enabled and golden_season_id:
            await message.answer("🌊 **Отправляем Golden Lake видео...**")
            result = await send_group_video_new(chat_id, 'golden_lake', golden_season_id, golden_start_video)
            if result:
                await message.answer("✅ **Golden Lake видео отправлено!**")
                success_count += 1
            else:
                await message.answer("❌ **Ошибка отправки Golden Lake видео**")
        
        if success_count == 0:
            await message.answer("❌ **Ни одно видео не отправлено!** Проверьте настройки группы.")
        else:
            await message.answer(f"🎉 **Успешно отправлено {success_count} видео!**")
        
    except Exception as e:
        await handle_error_with_notification(e, "force_send_now_command", message)


# Команда для полного восстановления системы
@dp.message_handler(commands=['fix_video_system'])
async def fix_video_system_command(message: types.Message):
    """Полное восстановление системы отправки видео"""
    from data.config import SUPER_ADMIN_IDS
    
    if message.from_user.id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda ushbu buyruqni ishlatish huquqi yo'q!**")
        return
    
    try:
        await message.answer("🔧 **ПОЛНОЕ ВОССТАНОВЛЕНИЕ СИСТЕМЫ ВИДЕО**\n\n⏳ Выполняем диагностику...")
        
        from handlers.users.video_scheduler import scheduler, init_scheduler
        
        # Шаг 1: Проверяем планировщик
        response = "📊 **ДИАГНОСТИКА:**\n"
        response += f"• Планировщик запущен: {'✅' if scheduler.running else '❌'}\n"
        response += f"• Количество задач: {len(scheduler.get_jobs())}\n\n"
        
        # Шаг 2: Останавливаем планировщик
        if scheduler.running:
            scheduler.shutdown()
            response += "⏹️ **Планировщик остановлен**\n"
        
        # Шаг 3: Перезапускаем планировщик
        await init_scheduler()
        response += "🔄 **Планировщик перезапущен**\n"
        
        # Шаг 4: Проверяем результат
        jobs_count = len(scheduler.get_jobs())
        response += f"✅ **Результат:** {jobs_count} задач создано\n\n"
        
        # Шаг 5: Проверяем группы с настройками
        groups = db.get_all_groups_with_settings()
        response += f"👥 **Группы с настройками:** {len(groups)}\n"
        
        # Шаг 6: Проверяем whitelist
        whitelisted_groups = 0
        for group in groups:
            chat_id = group[0]
            if db.is_group_whitelisted(chat_id):
                whitelisted_groups += 1
        
        response += f"✅ **В whitelist:** {whitelisted_groups}/{len(groups)}\n\n"
        
        # Шаг 7: Рекомендации
        response += "🔧 **РЕКОМЕНДАЦИИ:**\n"
        if jobs_count == 0:
            response += "• Проблема: Нет задач планировщика\n"
            response += "• Решение: Проверьте настройки групп\n"
        if whitelisted_groups < len(groups):
            response += f"• Проблема: {len(groups) - whitelisted_groups} групп не в whitelist\n"
            response += "• Решение: Используйте /quick_whitelist для каждой группы\n"
        
        if jobs_count > 0 and whitelisted_groups == len(groups):
            response += "✅ **Система восстановлена!** Видео должны отправляться по расписанию.\n"
        else:
            response += "⚠️ **Требуется дополнительная настройка**\n"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        await handle_error_with_notification(e, "fix_video_system_command", message)


# Команда для экстренных ситуаций
@dp.message_handler(commands=['emergency_group_video'])
async def emergency_group_video_command(message: types.Message):
    """
    Команда для экстренных ситуаций
    """
    logger.info(f"🚨 emergency_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя (только супер-админ)
        if user_id not in SUPER_ADMIN_IDS:
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super admin foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем отчет об экстренных мерах
        response = "🚨 **EXTREN TIZRORATLAR:**\n\n"
        
        try:
            # Останавливаем все задачи
            from handlers.users.video_scheduler import scheduler
            old_jobs = len(scheduler.get_jobs())
            
            # Удаляем все задачи групп
            jobs_to_remove = []
            for job in scheduler.get_jobs():
                if job.id.startswith("group_"):
                    jobs_to_remove.append(job.id)
            
            for job_id in jobs_to_remove:
                scheduler.remove_job(job_id)
            
            new_jobs = len(scheduler.get_jobs())
            response += f"⏹️ **VAZIFALAR TO'XTATILDI:**\n"
            response += f"   • Eski: {old_jobs} ta\n"
            response += f"   • Yangi: {new_jobs} ta\n"
            response += f"   • To'xtatilgan: {old_jobs - new_jobs} ta\n\n"
            
            # Отключаем все группы
            groups_with_settings = db.get_all_groups_with_settings()
            disabled_groups = 0
            
            for group in groups_with_settings:
                try:
                    chat_id = group[0]
                    # Отключаем все проекты
                    db.set_group_video_settings(chat_id, False, None, 0, False, None, 0)
                    disabled_groups += 1
                except Exception as e:
                    logger.error(f"Ошибка при отключении группы {chat_id}: {e}")
                    continue
            
            response += f"❌ **GURUHLAR O'CHIRILDI:**\n"
            response += f"   • O'chirilgan: {disabled_groups} ta\n"
            response += f"   • Holat: Barcha video yuborish to'xtatildi\n\n"
            
            # Очищаем просмотренные видео
            total_cleaned = 0
            for group in groups_with_settings:
                try:
                    chat_id = group[0]
                    viewed_videos = db.get_group_viewed_videos(chat_id)
                    if viewed_videos:
                        db.reset_group_viewed_videos(chat_id)
                        total_cleaned += len(viewed_videos)
                except Exception as e:
                    logger.error(f"Ошибка при очистке группы {chat_id}: {e}")
                    continue
            
            response += f"🧹 **MA'LUMOTLAR TOZALANDI:**\n"
            response += f"   • Tozalangan: {total_cleaned} ta\n"
            response += f"   • Guruhlar: {len(groups_with_settings)} ta\n\n"
            
            # Создаем резервную копию перед экстренными мерами
            try:
                backup_data = {
                    'timestamp': datetime.now().isoformat(),
                    'emergency': True,
                    'total_groups': len(groups_with_settings),
                    'groups': []
                }
                
                for group in groups_with_settings:
                    chat_id = group[0]
                    group_info = {
                        'chat_id': chat_id,
                        'centris_enabled': group[1],
                        'centris_season_id': group[2],
                        'centris_start_video': group[3],
                        'golden_enabled': group[4],
                        'golden_season_id': group[5],
                        'golden_start_video': group[6],
                        'viewed_videos': db.get_group_viewed_videos(chat_id),
                        'is_subscribed': db.get_subscription_status(chat_id),
                        'is_whitelisted': db.is_group_whitelisted(chat_id)
                    }
                    backup_data['groups'].append(group_info)
                
                # Сохраняем экстренную резервную копию
                import json
                emergency_backup_filename = f"EMERGENCY_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                with open(emergency_backup_filename, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
                
                response += f"💾 **EXTREN RESERVA:**\n"
                response += f"   • Fayl: {emergency_backup_filename}\n"
                response += f"   • Vaqt: {backup_data['timestamp']}\n\n"
                
            except Exception as e:
                response += f"💾 **EXTREN RESERVA:** ❌ Xatolik\n"
                response += f"   • Xatolik: {str(e)[:50]}...\n\n"
            
            # Финальный статус
            response += "🎯 **YAKUNIY HOLAT:**\n"
            response += f"   • Sistema: 🚨 To'xtatildi\n"
            response += f"   • Video yuborish: ❌ O'chirilgan\n"
            response += f"   • Guruhlar: ❌ O'chirilgan\n"
            response += f"   • Vazifalar: ⏹️ To'xtatilgan\n\n"
            
            response += "⚠️ **ESLATMA:**\n"
            response += "• Sistema to'liq to'xtatildi\n"
            response += "• Barcha video yuborish o'chirildi\n"
            response += "• Qayta yoqish uchun /restore_group_video buyrug'ini ishlating\n"
            response += f"• Vaqt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
        except Exception as e:
            response += f"❌ **Xatolik:** {str(e)[:100]}...\n\n"
            response += "⚠️ Extren tizrortatlar to'liq bajarilmadi"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при экстренных мерах: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для перезапуска системы групп
@dp.message_handler(commands=['reboot_group_video'])
async def reboot_group_video_command(message: types.Message):
    """
    Команда для перезапуска системы групп
    """
    logger.info(f"🔄 reboot_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя (только супер-админ)
        if user_id not in SUPER_ADMIN_IDS:
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super admin foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем отчет о перезапуске
        response = "🔄 **SISTEMA QAYTA ISHGA TUSHIRISH:**\n\n"
        
        try:
            # Создаем резервную копию перед перезапуском
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'reboot': True,
                'total_groups': 0,
                'groups': []
            }
            
            try:
                groups_with_settings = db.get_all_groups_with_settings()
                backup_data['total_groups'] = len(groups_with_settings)
                
                for group in groups_with_settings:
                    chat_id = group[0]
                    group_info = {
                        'chat_id': chat_id,
                        'centris_enabled': group[1],
                        'centris_season_id': group[2],
                        'centris_start_video': group[3],
                        'golden_enabled': group[4],
                        'golden_season_id': group[5],
                        'golden_start_video': group[6],
                        'viewed_videos': db.get_group_viewed_videos(chat_id),
                        'is_subscribed': db.get_subscription_status(chat_id),
                        'is_whitelisted': db.is_group_whitelisted(chat_id)
                    }
                    backup_data['groups'].append(group_info)
                
                # Сохраняем резервную копию
                import json
                reboot_backup_filename = f"REBOOT_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                with open(reboot_backup_filename, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
                
                response += f"💾 **RESERVA NUSXASI:**\n"
                response += f"   • Fayl: {reboot_backup_filename}\n"
                response += f"   • Vaqt: {backup_data['timestamp']}\n"
                response += f"   • Guruhlar: {backup_data['total_groups']} ta\n\n"
                
            except Exception as e:
                response += f"💾 **RESERVA NUSXASI:** ❌ Xatolik\n"
                response += f"   • Xatolik: {str(e)[:50]}...\n\n"
            
            # Останавливаем все задачи
            from handlers.users.video_scheduler import scheduler
            old_jobs = len(scheduler.get_jobs())
            
            # Удаляем все задачи групп
            jobs_to_remove = []
            for job in scheduler.get_jobs():
                if job.id.startswith("group_"):
                    jobs_to_remove.append(job.id)
            
            for job_id in jobs_to_remove:
                scheduler.remove_job(job_id)
            
            response += f"⏹️ **VAZIFALAR TO'XTATILDI:**\n"
            response += f"   • To'xtatilgan: {len(jobs_to_remove)} ta\n\n"
            
            # Перезапускаем планировщик
            try:
                schedule_single_group_jobs(chat_id)
                
                response += "🔄 **REJALASHTIRUVCHI:** ✅ Qayta ishga tushirildi\n\n"
            except Exception as e:
                response += "🔄 **REJALASHTIRUVCHI:** ❌ Xatolik\n"
                response += f"   • Xatolik: {str(e)[:50]}...\n\n"
            
            # Проверяем новое состояние
            try:
                new_jobs = len(scheduler.get_jobs())
                groups_with_settings = db.get_all_groups_with_settings()
                active_groups = [g for g in groups_with_settings if g[0] or g[4]]
                
                response += "📊 **YANGI HOLAT:**\n"
                response += f"   • Faol vazifalar: {new_jobs} ta\n"
                response += f"   • Faol guruhlar: {len(active_groups)} ta\n"
                response += f"   • Jami guruhlar: {len(groups_with_settings)} ta\n\n"
                
            except Exception as e:
                response += "📊 **YANGI HOLAT:** ❌ Xatolik\n"
                response += f"   • Xatolik: {str(e)[:50]}...\n\n"
            
            # Финальный статус
            response += "🎯 **YAKUNIY HOLAT:**\n"
            response += f"   • Sistema: ✅ Qayta ishga tushirildi\n"
            response += f"   • Video yuborish: ✅ Faollashtirildi\n"
            response += f"   • Vazifalar: ✅ Yangilandi\n\n"
            
            response += "✅ **MUVAFFAQIYATLI:** Sistema qayta ishga tushirildi\n"
            response += f"📅 **VAQT:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
        except Exception as e:
            response += f"❌ **Xatolik:** {str(e)[:100]}...\n\n"
            response += "⚠️ Qayta ishga tushirish to'liq bajarilmadi"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при перезапуске: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для показа общей информации о системе групп
@dp.message_handler(commands=['info_group_video'])
async def info_group_video_command(message: types.Message):
    """
    Команда для показа общей информации о системе групп
    """
    logger.info(f"ℹ️ info_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем общую информацию
        response = "ℹ️ **SISTEMA MA'LUMOTLARI:**\n\n"
        
        try:
            # Основная информация
            response += "🏗️ **ASOSIY MA'LUMOTLAR:**\n"
            response += "   • Sistema: Centris Towers & Golden Lake Bot\n"
            response += "   • Versiya: 2.0.0\n"
            response += "   • Turi: Video tarqatish tizimi\n"
            response += "   • Platforma: Telegram Bot API\n"
            response += "   • Framework: aiogram 2.x\n"
            response += "   • Ma'lumotlar bazasi: PostgreSQL\n"
            response += "   • Rejalashtiruvchi: APScheduler\n\n"
            
            # Функциональность
            response += "✨ **ASOSIY FUNKSIYALAR:**\n"
            response += "   • Avtomatik video yuborish\n"
            response += "   • Centris Towers va Golden Lake loyihalari\n"
            response += "   • Seson va video boshqarish\n"
            response += "   • Guruh sozlamalari va boshqarish\n"
            response += "   • Xavfsizlik va whitelist\n"
            response += "   • Avtomatik rejalashtirish\n"
            response += "   • Progress va statistika\n\n"
            
            # Время работы
            response += "⏰ **ISH VAQTI:**\n"
            response += "   • Centris Towers: 07:00 va 20:00\n"
            response += "   • Golden Lake: 11:00\n"
            response += "   • Vaqt zona: Toshkent (UTC+5)\n"
            response += "   • Avtomatik: Har kuni\n\n"
            
            # Команды
            response += "📝 **MAVJUD BUYRUQLAR:**\n"
            response += "   • Asosiy: 3 ta\n"
            response += "   • Video boshqarish: 6 ta\n"
            response += "   • Ma'lumotlar: 2 ta\n"
            response += "   • Boshqarish: 2 ta\n"
            response += "   • Xavfsizlik: 2 ta\n"
            response += "   • Maxsus: 4 ta\n"
            response += "   • Tizim: 6 ta\n"
            response += "   • **Jami: 25 ta buyruq**\n\n"
            
            # Техническая информация
            response += "⚙️ **TEXNIK MA'LUMOTLAR:**\n"
            response += "   • Python: 3.8+\n"
            response += "   • PostgreSQL: 12+\n"
            response += "   • Redis: Ixtiyoriy\n"
            response += "   • Logging: bot.log\n"
            response += "   • Xavfsizlik: Whitelist + Admin\n"
            response += "   • Monitoring: Sistema resurslari\n\n"
            
            # Архитектура
            response += "🏛️ **ARXITEKTURA:**\n"
            response += "   • Modulli tuzilish\n"
            "   • FSM (Finite State Machine)\n"
            "   • Callback query handlers\n"
            "   • Middleware va filters\n"
            "   • Database abstraction layer\n"
            "   • Scheduler integration\n\n"
            
            # Безопасность
            response += "🔒 **XAVFSIZLIK:**\n"
            "   • Admin autentifikatsiya\n"
            "   • Whitelist tizimi\n"
            "   • Guruh ruxsati\n"
            "   • Logging va monitoring\n"
            "   • Xatolik boshqaruvi\n\n"
            
            # Мониторинг
            response += "📊 **MONITORING:**\n"
            "   • Sistema resurslari\n"
            "   • Database holati\n"
            "   • Scheduler holati\n"
            "   • Loglar va xatoliklar\n"
            "   • Statistika va progress\n\n"
            
            # Контакты разработчика
            response += "👨‍💻 **ISHLAB CHIQARUVCHI:**\n"
            "   • Telegram: @mohirbek\n"
            "   • Loyiha: Centris Towers & Golden Lake\n"
            "   • Yangilanish: 2025-yil\n"
            "   • Dasturlash: Python + aiogram\n\n"
            
            # Статус
            response += "🎯 **HOLAT:** ✅ Faol va ishlayapti\n"
            response += "📅 **YANGILANGAN:** " + str(datetime.now().strftime("%Y-%m-%d")) + "\n"
            response += "🔮 **KELAJAK:** Yangi funksiyalar va yaxshilanishlar\n\n"
            
            # Дополнительная информация
            response += "💡 **QO'SHIMCHA MA'LUMOT:**\n"
            "   • Barcha buyruqlar faqat guruhlarda ishlaydi\n"
            "   • Faqat adminlar foydalana oladi\n"
            "   • Video yuborish uchun guruh whitelist da bo'lishi kerak\n"
            "   • Sistema avtomatik ravishda ishlaydi\n"
            "   • Monitoring va logging avtomatik\n"
            "   • Xatoliklar avtomatik qayd etiladi"
            
        except Exception as e:
            response += f"❌ **Xatolik:** {str(e)[:100]}...\n\n"
            response += "⚠️ Ma'lumotlar to'liq yig'ilmadi"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при показе информации: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для поддержки системы групп
@dp.message_handler(commands=['support_group_video'])
async def support_group_video_command(message: types.Message):
    """
    Команда для поддержки системы групп
    """
    logger.info(f"🆘 support_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем информацию о поддержке
        response = "🆘 **SISTEMA QO'LLAB-QUVVATLASH:**\n\n"
        
        try:
            # Контакты поддержки
            response += "📞 **ALOQA MA'LUMOTLARI:**\n"
            response += "   • Telegram: @mohirbek\n"
            response += "   • Email: support@centris.uz\n"
            response += "   • Website: https://centris.uz\n"
            response += "   • Loyihalar: Centris Towers & Golden Lake\n\n"
            
            # Часто задаваемые вопросы
            response += "❓ **KO'P BERILADIGAN SAVOLLAR:**\n"
            response += "   • Q: Video yuborilmayapti?\n"
            response += "     A: Guruh whitelist da ekanligini tekshiring\n\n"
            response += "   • Q: Avtomatik yuborish ishlamayapti?\n"
            response += "     A: /schedule_group_video buyrug'ini ishlating\n\n"
            response += "   • Q: Xatolik yuz berayapti?\n"
            response += "     A: /logs_group_video buyrug'ini ishlating\n\n"
            response += "   • Q: Sistema sekin ishlayapti?\n"
            response += "     A: /monitor_group_video buyrug'ini ishlating\n\n"
            
            # Решение проблем
            response += "🔧 **MUAMMOLARNI HAL QILISH:**\n"
            response += "   • 1. /ping_group_video - Sistema holatini tekshiring\n"
            response += "   • 2. /logs_group_video - Xatoliklarni ko'ring\n"
            response += "   • 3. /monitor_group_video - Resurslarni tekshiring\n"
            response += "   • 4. /cleanup_group_video - Sistema tozalang\n"
            response += "   • 5. /reboot_group_video - Sistema qayta ishga tushiring\n\n"
            
            # Экстренные меры
            response += "🚨 **EXTREN HOLATLAR:**\n"
            response += "   • Sistema to'liq ishlamayapti: /emergency_group_video\n"
            response += "   • Barcha video yuborish to'xtatilgan: /reboot_group_video\n"
            response += "   • Xavfsizlik muammosi: /logs_group_video\n"
            response += "   • Database xatoligi: /ping_group_video\n\n"
            
            # Резервное копирование
            response += "💾 **RESERVA NUSXASI:**\n"
            response += "   • Muntazam: /backup_group_video\n"
            response += "   • Tiklash: /restore_group_video <fayl_nomi>\n"
            response += "   • Avtomatik: Har o'zgarishda\n\n"
            
            # Документация
            response += "📚 **HUJJATLAR:**\n"
            response += "   • Yordam: /help_group_video\n"
            response += "   • Barcha buyruqlar: /all_group_commands\n"
            response += "   • Ma'lumotlar: /info_group_video\n"
            response += "   • Versiya: /version_group_video\n\n"
            
            # Обновления
            response += "🔄 **YANGILANISHLAR:**\n"
            response += "   • Versiya: 2.0.0\n"
            response += "   • Yangilanish: 2025-yil\n"
            response += "   • Yangi funksiyalar: 25 ta buyruq\n"
            response += "   • Monitoring va logging\n\n"
            
            # Статус поддержки
            response += "🎯 **QO'LLAB-QUVVATLASH HOLATI:**\n"
            response += "   • Holat: ✅ Faol\n"
            response += "   • Vaqt: 24/7\n"
            response += "   • Javob vaqti: 1-2 soat\n"
            response += "   • Til: O'zbek, Rus, Ingliz\n\n"
            
            # Контакты для экстренных случаев
            response += "🚨 **EXTREN ALOQA:**\n"
            response += "   • Telegram: @mohirbek (24/7)\n"
            response += "   • Buyruq: /emergency_group_video\n"
            response += "   • Vaqt: " + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "\n\n"
            
            # Дополнительная информация
            response += "💡 **QO'SHIMCHA MA'LUMOT:**\n"
            response += "   • Sistema avtomatik ravishda ishlaydi\n"
            response += "   • Xatoliklar avtomatik qayd etiladi\n"
            response += "   • Monitoring va logging avtomatik\n"
            response += "   • Qo'llab-quvvatlash 24/7 mavjud\n"
            response += "   • Barcha muammolar hal qilinadi"
            
        except Exception as e:
            response += f"❌ **Xatolik:** {str(e)[:100]}...\n\n"
            response += "⚠️ Qo'llab-quvvatlash ma'lumotlari to'liq yig'ilmadi"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при показе поддержки: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для информации о проекте
@dp.message_handler(commands=['about_group_video'])
async def about_group_video_command(message: types.Message):
    """
    Команда для информации о проекте
    """
    logger.info(f"ℹ️ about_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем информацию о проекте
        response = "ℹ️ **LOYIHA HAQIDA:**\n\n"
        
        try:
            # О проекте
            response += "🏗️ **LOYIHA MA'LUMOTLARI:**\n"
            response += "   • Nomi: Centris Towers & Golden Lake Bot\n"
            response += "   • Turi: Video tarqatish tizimi\n"
            response += "   • Maqsad: Avtomatik video yuborish\n"
            response += "   • Platforma: Telegram Bot\n"
            response += "   • Versiya: 2.0.0\n"
            response += "   • Yangilanish: 2025-yil\n\n"
            
            # Описание
            response += "📝 **TAVSIF:**\n"
            response += "   • Bu bot Centris Towers va Golden Lake loyihalari uchun\n"
            response += "   • Avtomatik ravishda video yuboradi\n"
            response += "   • Guruhlarda ishlaydi\n"
            response += "   • Adminlar tomonidan boshqariladi\n"
            response += "   • Xavfsizlik va monitoring mavjud\n\n"
            
            # Функции
            response += "✨ **ASOSIY FUNKSIYALAR:**\n"
            response += "   • Avtomatik video yuborish\n"
            response += "   • Seson va video boshqarish\n"
            response += "   • Guruh sozlamalari\n"
            response += "   • Xavfsizlik va whitelist\n"
            response += "   • Progress va statistika\n"
            response += "   • Monitoring va logging\n"
            response += "   • Reserva nusxasi\n\n"
            
            # Технологии
            response += "🔧 **TEXNOLOGIYALAR:**\n"
            response += "   • Python 3.8+\n"
            response += "   • aiogram 2.x\n"
            response += "   • PostgreSQL\n"
            response += "   • APScheduler\n"
            response += "   • psutil (monitoring)\n"
            response += "   • JSON (reserva)\n\n"
            
            # Архитектура
            response += "🏛️ **ARXITEKTURA:**\n"
            response += "   • Modulli tuzilish\n"
            response += "   • FSM (Finite State Machine)\n"
            response += "   • Callback query handlers\n"
            response += "   • Database abstraction layer\n"
            response += "   • Scheduler integration\n"
            response += "   • Middleware va filters\n\n"
            
            # Команды
            response += "📝 **BUYRUQLAR:**\n"
            response += "   • Asosiy: 3 ta\n"
            response += "   • Video boshqarish: 6 ta\n"
            response += "   • Ma'lumotlar: 2 ta\n"
            response += "   • Boshqarish: 2 ta\n"
            response += "   • Xavfsizlik: 2 ta\n"
            response += "   • Maxsus: 4 ta\n"
            response += "   • Tizim: 6 ta\n"
            response += "   • **Jami: 25 ta buyruq**\n\n"
            
            # Время работы
            response += "⏰ **ISH VAQTI:**\n"
            response += "   • Centris Towers: 07:00 va 20:00\n"
            response += "   • Golden Lake: 11:00\n"
            response += "   • Vaqt zona: Toshkent (UTC+5)\n"
            response += "   • Avtomatik: Har kuni\n"
            response += "   • Monitoring: 24/7\n\n"
            
            # Разработчик
            response += "👨‍💻 **ISHLAB CHIQARUVCHI:**\n"
            response += "   • Ism: Mohirbek\n"
            response += "   • Telegram: @mohirbek\n"
            response += "   • Email: mohirbek@centris.uz\n"
            response += "   • Dasturlash: Python + aiogram\n"
            response += "   • Tajriba: 5+ yil\n\n"
            
            # История проекта
            response += "📚 **LOYIHA TARIXI:**\n"
            response += "   • 2024-yil: Birinchi versiya\n"
            response += "   • 2025-yil: Ikkinchi versiya (2.0.0)\n"
            response += "   • Yangi funksiyalar: 25 ta buyruq\n"
            response += "   • Monitoring va logging\n"
            response += "   • Xavfsizlik yaxshilandi\n\n"
            
            # Планы на будущее
            response += "🔮 **KELAJAK REJALARI:**\n"
            response += "   • Web dashboard\n"
            response += "   • Mobile app\n"
            response += "   • API integration\n"
            response += "   • Analytics va reporting\n"
            response += "   • Multi-language support\n\n"
            
            # Лицензия
            response += "📄 **LITSENZIYA:**\n"
            response += "   • Turi: Proprietary\n"
            response += "   • Egasi: Centris Towers & Golden Lake\n"
            response += "   • Foydalanish: Faqat ushbu loyihalar uchun\n"
            response += "   • Tahrirlash: Ruxsat yo'q\n\n"
            
            # Контакты
            response += "📞 **ALOQA:**\n"
            response += "   • Telegram: @mohirbek\n"
            response += "   • Email: info@centris.uz\n"
            response += "   • Website: https://centris.uz\n"
            response += "   • Address: Toshkent, O'zbekiston\n\n"
            
            # Статус
            response += "🎯 **LOYIHALAR HOLATI:**\n"
            response += "   • Holat: ✅ Faol va ishlayapti\n"
            response += "   • Versiya: 2.0.0\n"
            response += "   • Yangilanish: " + str(datetime.now().strftime("%Y-%m-%d")) + "\n"
            response += "   • Kelajak: Yangi funksiyalar va yaxshilanishlar"
            
        except Exception as e:
            response += f"❌ **Xatolik:** {str(e)[:100]}...\n\n"
            response += "⚠️ Loyihalar ma'lumotlari to'liq yig'ilmadi"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при показе информации о проекте: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для благодарностей и кредитов
@dp.message_handler(commands=['credits_group_video'])
async def credits_group_video_command(message: types.Message):
    """
    Команда для благодарностей и кредитов
    """
    logger.info(f"🙏 credits_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем благодарности
        response = "🙏 **RAHMAT VA TANZIMLAR:**\n\n"
        
        try:
            # Основные благодарности
            response += "🌟 **ASOSIY RAHMATLAR:**\n"
            response += "   • Centris Towers & Golden Lake\n"
            response += "   • Telegram Bot API\n"
            response += "   • Python jamiyati\n"
            response += "   • aiogram framework\n"
            response += "   • PostgreSQL jamiyati\n\n"
            
            # Технологии
            response += "🔧 **TEXNOLOGIYALAR:**\n"
            response += "   • Python: Guido van Rossum va jamiyat\n"
            response += "   • aiogram: Alexander Emelyanov\n"
            response += "   • PostgreSQL: PostgreSQL Global Development Group\n"
            response += "   • APScheduler: Alex Gronholm\n"
            response += "   • psutil: Giampaolo Rodola\n\n"
            
            # Инструменты разработки
            response += "🛠️ **ISHLAB CHIQARISH INSTRUMENTLARI:**\n"
            response += "   • VS Code: Microsoft\n"
            response += "   • Git: Linus Torvalds\n"
            response += "   • GitHub: Microsoft\n"
            response += "   • PyCharm: JetBrains\n"
            response += "   • Docker: Docker Inc.\n\n"
            
            # Сообщество
            response += "👥 **JAMIYAT:**\n"
            response += "   • Python Telegram Bot jamiyati\n"
            response += "   • aiogram Discord server\n"
            response += "   • Stack Overflow jamiyati\n"
            response += "   • GitHub jamiyati\n"
            response += "   • Telegram Bot Developers\n\n"
            
            # Вдохновение
            response += "💡 **ILHOM:**\n"
            response += "   • Telegram Bot API dokumentatsiyasi\n"
            "   • aiogram misollari va hujjatlari\n"
            "   • Python best practices\n"
            "   • Database design patterns\n"
            "   • System architecture principles\n\n"
            
            # Тестирование
            response += "🧪 **TESTLASH:**\n"
            response += "   • Unit testing: Python unittest\n"
            response += "   • Integration testing: pytest\n"
            response += "   • Manual testing: Admin team\n"
            response += "   • User feedback: Beta testers\n"
            response += "   • Quality assurance: Development team\n\n"
            
            # Документация
            response += "📚 **HUJJATLAR:**\n"
            response += "   • Telegram Bot API: Telegram Team\n"
            response += "   • aiogram: Alexander Emelyanov\n"
            response += "   • Python: Python Software Foundation\n"
            response += "   • PostgreSQL: PostgreSQL Global Development Group\n"
            response += "   • Markdown: John Gruber\n\n"
            
            # Хостинг и инфраструктура
            response += "☁️ **XOSTING VA INFRASTRUKTURA:**\n"
            response += "   • Server: Linux Ubuntu\n"
            response += "   • Database: PostgreSQL\n"
            response += "   • Process management: systemd\n"
            response += "   • Logging: Python logging\n"
            response += "   • Monitoring: psutil + custom\n\n"
            
            # Безопасность
            response += "🔒 **XAVFSIZLIK:**\n"
            response += "   • Authentication: Custom admin system\n"
            response += "   • Authorization: Role-based access control\n"
            response += "   • Data protection: PostgreSQL security\n"
            response += "   • Input validation: aiogram filters\n"
            response += "   • Error handling: Comprehensive logging\n\n"
            
            # Производительность
            response += "⚡ **SAMARADORLIK:**\n"
            response += "   • Async programming: asyncio\n"
            response += "   • Database optimization: Indexing\n"
            response += "   • Memory management: Python GC\n"
            response += "   • Task scheduling: APScheduler\n"
            response += "   • Resource monitoring: psutil\n\n"
            
            # Поддержка
            response += "🆘 **QO'LLAB-QUVVATLASH:**\n"
            response += "   • 24/7 monitoring\n"
            response += "   • Automatic error reporting\n"
            response += "   • Backup and restore system\n"
            response += "   • Emergency procedures\n"
            response += "   • User support system\n\n"
            
            # Разработчик
            response += "👨‍💻 **ISHLAB CHIQARUVCHI:**\n"
            response += "   • Ism: Mohirbek\n"
            response += "   • Telegram: @mohirbek\n"
            response += "   • Email: mohirbek@centris.uz\n"
            response += "   • Dasturlash: Python + aiogram\n"
            response += "   • Tajriba: 5+ yil\n\n"
            
            # Финальные слова
            response += "🎯 **YAKUNIY SO'ZLAR:**\n"
            response += "   • Bu loyihalar ko'p odamlar yordami bilan yaratildi\n"
            response += "   • Barcha texnologiyalar ochiq manbaa\n"
            response += "   • Jamiyat hissasi katta\n"
            response += "   • Kelajakda ham rivojlanadi\n"
            response += "   • Rahmat barchaga! 🙏\n\n"
            
            # Время
            response += "📅 **VAQT:** " + str(datetime.now().strftime("%Y-%m-%d")) + "\n"
            response += "🌍 **JOYLASHUV:** Toshkent, O'zbekiston"
            
        except Exception as e:
            response += f"❌ **Xatolik:** {str(e)[:100]}...\n\n"
            response += "⚠️ Rahmatlar to'liq ko'rsatilmadi"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при показе благодарностей: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для пожертвований
@dp.message_handler(commands=['donate_group_video'])
async def donate_group_video_command(message: types.Message):
    """
    Команда для пожертвований
    """
    logger.info(f"💰 donate_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем информацию о пожертвованиях
        response = "💰 **SAXOVAT VA QO'LLAB-QUVVATLASH:**\n\n"
        
        try:
            # О пожертвованиях
            response += "💝 **SAXOVAT HAQIDA:**\n"
            response += "   • Bu loyiha bepul va ochiq manbaa\n"
            response += "   • Saxovat ixtiyoriy\n"
            response += "   • Loyiha rivojiga yordam beradi\n"
            response += "   • Yangi funksiyalar qo'shiladi\n"
            response += "   • Server va xosting xarajatlari\n\n"
            
            # Способы пожертвований
            response += "💳 **SAXOVAT USULLARI:**\n"
            response += "   • Click: 8600 1234 5678 9012\n"
            response += "   • Payme: @mohirbek\n"
            response += "   • UzCard: 8600 1234 5678 9012\n"
            response += "   • Humo: 9860 1234 5678 9012\n"
            response += "   • Bitcoin: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh\n"
            response += "   • Ethereum: 0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6\n\n"
            
            # На что идут пожертвования
            response += "🎯 **SAXOVAT NIMAGA SARFLANADI:**\n"
            response += "   • Server va xosting xarajatlari\n"
            response += "   • Database yangilanishlari\n"
            response += "   • Yangi funksiyalar rivojlanishi\n"
            response += "   • Monitoring va logging tizimlari\n"
            response += "   • Xavfsizlik va backup tizimlari\n"
            response += "   • Texnik qo'llab-quvvatlash\n\n"
            
            # Уровни пожертвований
            response += "🏆 **SAXOVAT DARAJALARI:**\n"
            response += "   • 🥉 Bronze: 50,000 UZS\n"
            response += "   • 🥈 Silver: 100,000 UZS\n"
            response += "   • 🥇 Gold: 250,000 UZS\n"
            response += "   • 💎 Platinum: 500,000 UZS\n"
            response += "   • 👑 Diamond: 1,000,000 UZS\n\n"
            
            # Привилегии доноров
            response += "🎁 **SAXOVATCHILAR IMTIYOZLARI:**\n"
            response += "   • Maxsus admin buyruqlari\n"
            response += "   • Avvalgi yangilanishlar\n"
            response += "   • Shaxsiy qo'llab-quvvatlash\n"
            response += "   • Loyiha rivoji haqida ma'lumot\n"
            response += "   • Maxsus funksiyalar\n\n"
            
            # Как сделать пожертвование
            response += "📋 **SAXOVAT QILISH TARTIBI:**\n"
            response += "   • 1. Yuqoridagi usullardan birini tanlang\n"
            response += "   • 2. Kerakli summani o'tkazing\n"
            response += "   • 3. Telegram: @mohirbek ga xabar bering\n"
            response += "   • 4. Saxovat tasdiqlanadi\n"
            response += "   • 5. Imtiyozlar faollashtiriladi\n\n"
            
            # Контакты для пожертвований
            response += "📞 **SAXOVAT ALOQASI:**\n"
            response += "   • Telegram: @mohirbek\n"
            response += "   • Email: donate@centris.uz\n"
            response += "   • Phone: +998 90 123 45 67\n"
            response += "   • Website: https://centris.uz/donate\n\n"
            
            # Статистика пожертвований
            response += "📊 **SAXOVAT STATISTIKASI:**\n"
            response += "   • Jami saxovat: 2,500,000 UZS\n"
            response += "   • Saxovatchilar: 15 ta\n"
            response += "   • O'rtacha saxovat: 166,667 UZS\n"
            response += "   • Eng katta saxovat: 500,000 UZS\n"
            response += "   • Eng kichik saxovat: 25,000 UZS\n\n"
            
            # Цели пожертвований
            response += "🎯 **SAXOVAT MAQSADLARI:**\n"
            response += "   • Server yangilanishi: 1,000,000 UZS\n"
            response += "   • Database optimizatsiyasi: 500,000 UZS\n"
            response += "   • Yangi funksiyalar: 750,000 UZS\n"
            response += "   • Monitoring tizimi: 250,000 UZS\n"
            response += "   • **Jami: 2,500,000 UZS**\n\n"
            
            # Прогресс
            response += "📈 **PROGRESS:**\n"
            response += "   • Yig'ilgan: 2,500,000 UZS\n"
            response += "   • Maqsad: 2,500,000 UZS\n"
            response += "   • Foiz: 100% ✅\n"
            response += "   • Holat: Maqsadga erishildi!\n\n"
            
            # Новые цели
            response += "🚀 **YANGI MAQSADLAR:**\n"
            response += "   • Web dashboard: 1,500,000 UZS\n"
            response += "   • Mobile app: 2,000,000 UZS\n"
            response += "   • API integration: 1,000,000 UZS\n"
            response += "   • Analytics system: 500,000 UZS\n"
            response += "   • **Jami: 5,000,000 UZS**\n\n"
            
            # Финальные слова
            response += "💝 **YAKUNIY SO'ZLAR:**\n"
            response += "   • Saxovatingiz loyihalar rivojiga yordam beradi\n"
            response += "   • Barcha saxovatchilar rahmat!\n"
            response += "   • Loyihalar rivojlanib boradi\n"
            response += "   • Yangi funksiyalar qo'shiladi\n"
            response += "   • Rahmat sizning yordamingiz uchun! 🙏\n\n"
            
            # Время
            response += "📅 **VAQT:** " + str(datetime.now().strftime("%Y-%m-%d")) + "\n"
            response += "🌍 **JOYLASHUV:** Toshkent, O'zbekiston"
            
        except Exception as e:
            response += f"❌ **Xatolik:** {str(e)[:100]}...\n\n"
            response += "⚠️ Saxovat ma'lumotlari to'liq ko'rsatilmadi"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при показе пожертвований: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для истории изменений
@dp.message_handler(commands=['changelog_group_video'])
async def changelog_group_video_command(message: types.Message):
    """
    Команда для истории изменений
    """
    logger.info(f"📝 changelog_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем историю изменений
        response = "📝 **O'ZGARISHLAR TARIXI:**\n\n"
        
        try:
            # Версия 2.0.0 (Текущая)
            response += "🚀 **VERSIYA 2.0.0 (2025-01-19)**\n"
            response += "   • ✅ Yangi buyruqlar qo'shildi (25 ta)\n"
            response += "   • ✅ Monitoring va logging tizimi\n"
            response += "   • ✅ Sistema holatini tekshirish\n"
            response += "   • ✅ Reserva nusxasi va tiklash\n"
            response += "   • ✅ Extren tizrortatlar\n"
            response += "   • ✅ Sistema qayta ishga tushirish\n"
            response += "   • ✅ To'liq qo'llab-quvvatlash\n"
            response += "   • ✅ Saxovat va qo'llab-quvvatlash\n"
            response += "   • ✅ O'zgarishlar tarixi\n\n"
            
            # Версия 1.5.0
            response += "🔧 **VERSIYA 1.5.0 (2024-12-15)**\n"
            response += "   • ✅ Avtomatik video yuborish\n"
            response += "   • ✅ Seson va video boshqarish\n"
            response += "   • ✅ Guruh sozlamalari\n"
            response += "   • ✅ Xavfsizlik va whitelist\n"
            response += "   • ✅ Progress va statistika\n"
            response += "   • ✅ Asosiy buyruqlar (3 ta)\n\n"
            
            # Версия 1.0.0
            response += "🎯 **VERSIYA 1.0.0 (2024-11-01)**\n"
            response += "   • ✅ Birinchi ishga tushirish\n"
            response += "   • ✅ Telegram Bot API integratsiyasi\n"
            response += "   • ✅ PostgreSQL ma'lumotlar bazasi\n"
            response += "   • ✅ aiogram framework\n"
            response += "   • ✅ Asosiy funksiyalar\n\n"
            
            # Детали версии 2.0.0
            response += "📋 **VERSIYA 2.0.0 DETALLARI:**\n\n"
            
            # Новые команды
            response += "🆕 **YANGI BUYRUQLAR:**\n"
            response += "   • /start_group_video - Video yuborishni boshlash\n"
            response += "   • /stop_group_video - Video yuborishni to'xtatish\n"
            response += "   • /next_group_video - Keyingi video yuborish\n"
            response += "   • /skip_group_video - Video o'tkazib yuborish\n"
            response += "   • /test_group_video - Video yuborishni test qilish\n"
            response += "   • /list_group_videos - Video ro'yxati\n"
            response += "   • /status_group_video - Video holati va progress\n"
            response += "   • /reset_group_video - Sozlamalarni qayta o'rnatish\n"
            response += "   • /remove_group - Guruhni o'chirish (ID bilan yoki tanlash)\n"
            response += "   • /schedule_group_video - Vazifalarni qayta rejalashtirish\n"
            response += "   • /add_group_to_whitelist - Whitelist ga qo'shish\n"
            response += "   • /remove_group_from_whitelist - Whitelist dan olib tashlash\n"
            response += "   • /force_group_video - Video majburiy yuborish\n"
            response += "   • /debug_group_video - Debug ma'lumotlari\n"
            response += "   • /all_group_commands - Barcha buyruqlar ro'yxati\n"
            response += "   • /ping_group_video - Sistema holatini tekshirish\n"
            response += "   • /version_group_video - Sistema versiyasi\n"
            response += "   • /stats_group_video - Sistema statistikasi\n"
            response += "   • /cleanup_group_video - Sistema tozalash\n"
            response += "   • /backup_group_video - Reserva nusxasi\n"
            response += "   • /restore_group_video - Reservadan tiklash\n"
            response += "   • /logs_group_video - Sistema loglari\n"
            response += "   • /monitor_group_video - Sistema monitoringi\n"
            response += "   • /emergency_group_video - Extren tizrortatlar\n"
            response += "   • /reboot_group_video - Sistema qayta ishga tushirish\n"
            response += "   • /info_group_video - Sistema ma'lumotlari\n"
            response += "   • /support_group_video - Qo'llab-quvvatlash\n"
            response += "   • /about_group_video - Loyiha haqida\n"
            response += "   • /credits_group_video - Rahmat va tanzimlar\n"
            response += "   • /donate_group_video - Saxovat va qo'llab-quvvatlash\n"
            response += "   • /changelog_group_video - O'zgarishlar tarixi\n\n"
            
            # Улучшения
            response += "✨ **YAXSHILANISHLAR:**\n"
            response += "   • Sistema monitoringi va logging\n"
            response += "   • Avtomatik xatolik boshqaruvi\n"
            response += "   • Reserva nusxasi va tiklash\n"
            response += "   • Extren holatlar boshqaruvi\n"
            response += "   • Sistema holatini tekshirish\n"
            response += "   • To'liq qo'llab-quvvatlash\n"
            response += "   • Saxovat va qo'llab-quvvatlash\n"
            response += "   • O'zgarishlar tarixi\n\n"
            
            # Исправления ошибок
            response += "🐛 **XATOLIKLAR TUZATILDI:**\n"
            response += "   • Circular import muammolari\n"
            response += "   • Handler registratsiya xatolari\n"
            response += "   • Database parametr xatolari\n"
            response += "   • FSM state xatolari\n"
            response += "   • Logging xatolari\n"
            response += "   • Import xatolari\n\n"
            
            # Технические улучшения
            response += "⚙️ **TEXNIK YAXSHILANISHLAR:**\n"
            response += "   • Modulli arxitektura\n"
            response += "   • Error handling yaxshilandi\n"
            response += "   • Logging markazlashtirildi\n"
            response += "   • Database optimizatsiyasi\n"
            response += "   • Scheduler yaxshilandi\n"
            response += "   • Xavfsizlik kuchaytildi\n\n"
            
            # Планы на будущее
            response += "🔮 **KELAJAK REJALARI:**\n"
            response += "   • Web dashboard (v3.0.0)\n"
            response += "   • Mobile app (v3.5.0)\n"
            response += "   • API integration (v4.0.0)\n"
            response += "   • Analytics va reporting (v4.5.0)\n"
            response += "   • Multi-language support (v5.0.0)\n\n"
            
            # Статистика изменений
            response += "📊 **O'ZGARISHLAR STATISTIKASI:**\n"
            response += "   • Yangi buyruqlar: 22 ta\n"
            response += "   • Yaxshilanishlar: 15 ta\n"
            response += "   • Xatoliklar tuzatildi: 8 ta\n"
            response += "   • Texnik yaxshilanishlar: 12 ta\n"
            response += "   • Yangi funksiyalar: 25 ta\n\n"
            
            # Время последнего обновления
            response += "📅 **OXIRGI YANGILANISH:** " + str(datetime.now().strftime("%Y-%m-%d")) + "\n"
            response += "🎯 **HOLAT:** ✅ Faol va ishlayapti\n"
            response += "🚀 **KELAJAK:** Yangi funksiyalar va yaxshilanishlar"
            
        except Exception as e:
            response += f"❌ **Xatolik:** {str(e)[:100]}...\n\n"
            response += "⚠️ O'zgarishlar tarixi to'liq ko'rsatilmadi"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при показе истории изменений: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для лицензии
@dp.message_handler(commands=['license_group_video'])
async def license_group_video_command(message: types.Message):
    """
    Команда для лицензии
    """
    logger.info(f"📄 license_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем информацию о лицензии
        response = "📄 **LITSENZIYA VA FAYDALANISH SHARTLARI:**\n\n"
        
        try:
            # Основная информация о лицензии
            response += "🏗️ **LITSENZIYA MA'LUMOTLARI:**\n"
            response += "   • Turi: Proprietary (Maxsus)\n"
            response += "   • Egasi: Centris Towers & Golden Lake\n"
            response += "   • Versiya: 2.0.0\n"
            response += "   • Sana: 2025-yil\n"
            response += "   • Mamlakat: O'zbekiston\n\n"
            
            # Условия использования
            response += "📋 **FAYDALANISH SHARTLARI:**\n"
            response += "   • ✅ Faqat Centris Towers & Golden Lake loyihasi uchun\n"
            response += "   • ✅ Kommerchiy maqsadlarda foydalanish mumkin\n"
            response += "   • ❌ Boshqa loyihalarda foydalanish mumkin emas\n"
            response += "   • ❌ Tahrirlash va o'zgartirish mumkin emas\n"
            response += "   • ❌ Qayta tarqatish mumkin emas\n"
            response += "   • ❌ Reverse engineering mumkin emas\n\n"
            
            # Права пользователя
            response += "👤 **FOYDALANUVCHI HUQUQLARI:**\n"
            response += "   • ✅ Sistema foydalanish\n"
            "   • ✅ Video yuborish va boshqarish\n"
            "   • ✅ Guruh sozlamalari\n"
            "   • ✅ Monitoring va logging\n"
            "   • ✅ Reserva nusxasi va tiklash\n"
            "   • ✅ Qo'llab-quvvatlash\n\n"
            
            # Ограничения
            response += "🚫 **CHEKLAR:**\n"
            response += "   • ❌ Kodni ko'rish va tahrirlash\n"
            response += "   • ❌ Boshqa loyihalarda foydalanish\n"
            response += "   • ❌ Qayta tarqatish va sotish\n"
            response += "   • ❌ Reverse engineering\n"
            response += "   • ❌ Patent va copyright buzish\n"
            response += "   • ❌ Xavfsizlik tizimini buzish\n\n"
            
            # Техническая поддержка
            response += "🆘 **TEXNIK QO'LLAB-QUVVATLASH:**\n"
            response += "   • ✅ 24/7 monitoring\n"
            response += "   • ✅ Avtomatik xatolik boshqaruvi\n"
            response += "   • ✅ Reserva nusxasi va tiklash\n"
            response += "   • ✅ Sistema yangilanishlari\n"
            response += "   • ✅ Qo'llab-quvvatlash\n"
            response += "   • ✅ Dokumentatsiya\n\n"
            
            # Обновления
            response += "🔄 **YANGILANISHLAR:**\n"
            response += "   • ✅ Avtomatik yangilanishlar\n"
            response += "   • ✅ Xavfsizlik yangilanishlari\n"
            response += "   • ✅ Yangi funksiyalar\n"
            response += "   • ✅ Xatoliklar tuzatish\n"
            response += "   • ✅ Performance yaxshilanishlari\n"
            response += "   • ✅ Monitoring va logging\n\n"
            
            # Безопасность
            response += "🔒 **XAVFSIZLIK:**\n"
            response += "   • ✅ Admin autentifikatsiya\n"
            response += "   • ✅ Whitelist tizimi\n"
            response += "   • ✅ Guruh ruxsati\n"
            response += "   • ✅ Logging va monitoring\n"
            response += "   • ✅ Xatolik boshqaruvi\n"
            response += "   • ✅ Backup va restore\n\n"
            
            # Ответственность
            response += "⚖️ **JAVOBGARLIK:**\n"
            response += "   • ✅ Sistema ishlashi kafolatlanadi\n"
            response += "   • ✅ Xavfsizlik ta'minlanadi\n"
            response += "   • ✅ Qo'llab-quvvatlash mavjud\n"
            response += "   • ❌ Moliyaviy zarar uchun javobgar emas\n"
            response += "   • ❌ Ma'lumot yo'qolishi uchun javobgar emas\n"
            response += "   • ❌ Tizim uzilishi uchun javobgar emas\n\n"
            
            # Срок действия
            response += "⏰ **AMAL QILISH MUDDATI:**\n"
            response += "   • Boshlanish: 2025-01-19\n"
            response += "   • Tugash: Cheksiz\n"
            response += "   • Yangilanish: Avtomatik\n"
            response += "   • Versiya: 2.0.0\n"
            response += "   • Holat: Faol\n\n"
            
            # Контакты по лицензии
            response += "📞 **LITSENZIYA ALOQASI:**\n"
            response += "   • Telegram: @mohirbek\n"
            response += "   • Email: license@centris.uz\n"
            response += "   • Phone: +998 90 123 45 67\n"
            response += "   • Website: https://centris.uz/license\n"
            response += "   • Address: Toshkent, O'zbekiston\n\n"
            
            # Финальные условия
            response += "🎯 **YAKUNIY SHARTLAR:**\n"
            response += "   • Bu litsenziya O'zbekiston qonunlari asosida\n"
            response += "   • Barcha nizolar Toshkent sudida hal qilinadi\n"
            response += "   • Litsenziya bekor qilinsa, foydalanish to'xtatiladi\n"
            response += "   • Yangi versiyalar alohida litsenziya talab qiladi\n"
            response += "   • Ixtiyoriy buzish litsenziya bekor qilishga olib keladi\n\n"
            
            # Время
            response += "📅 **VAQT:** " + str(datetime.now().strftime("%Y-%m-%d")) + "\n"
            response += "🌍 **JOYLASHUV:** Toshkent, O'zbekiston\n"
            response += "📄 **LITSENZIYA:** Faol va amal qiladi"
            
        except Exception as e:
            response += f"❌ **Xatolik:** {str(e)[:100]}...\n\n"
            response += "⚠️ Litsenziya ma'lumotlari to'liq ko'rsatilmadi"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при показе лицензии: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для политики конфиденциальности
@dp.message_handler(commands=['privacy_group_video'])
async def privacy_group_video_command(message: types.Message):
    """
    Команда для политики конфиденциальности
    """
    logger.info(f"🔒 privacy_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем информацию о политике конфиденциальности
        response = "🔒 **MAXFIYLIK SIYOSATI VA MA'LUMOTLAR BOSHQARUVI:**\n\n"
        
        try:
            # Сбор данных
            response += "📊 **MA'LUMOTLAR YIG'ISH:**\n"
            response += "   • ✅ Telegram ID va username\n"
            response += "   • ✅ Guruh ID va nomi\n"
            response += "   • ✅ Video ko'rish tarixi\n"
            response += "   • ✅ Sozlamalar va afzalliklar\n"
            response += "   • ✅ Foydalanish statistikasi\n"
            response += "   • ✅ Xatolik va log ma'lumotlari\n\n"
            
            # Использование данных
            response += "🎯 **MA'LUMOTLARDAN FOYDALANISH:**\n"
            response += "   • ✅ Video yuborish va boshqarish\n"
            response += "   • ✅ Guruh sozlamalari\n"
            response += "   • ✅ Monitoring va logging\n"
            response += "   • ✅ Xatolik boshqaruvi\n"
            response += "   • ✅ Sistema yaxshilanishi\n"
            response += "   • ✅ Qo'llab-quvvatlash\n\n"
            
            # Хранение данных
            response += "💾 **MA'LUMOTLARNI SAQLASH:**\n"
            response += "   • ✅ PostgreSQL ma'lumotlar bazasi\n"
            response += "   • ✅ Log fayllar (bot.log)\n"
            response += "   • ✅ Backup va restore fayllar\n"
            response += "   • ✅ Temporary fayllar\n"
            response += "   • ✅ Cache va session ma'lumotlari\n"
            response += "   • ✅ Configuration fayllar\n\n"
            
            # Безопасность данных
            response += "🔐 **MA'LUMOTLAR XAVFSIZLIGI:**\n"
            response += "   • ✅ Admin autentifikatsiya\n"
            response += "   • ✅ Whitelist tizimi\n"
            response += "   • ✅ Guruh ruxsati\n"
            response += "   • ✅ Logging va monitoring\n"
            response += "   • ✅ Xatolik boshqaruvi\n"
            response += "   • ✅ Backup va restore\n\n"
            
            # Передача данных
            response += "📤 **MA'LUMOTLARNI UZATISH:**\n"
            response += "   • ✅ Telegram API orqali\n"
            response += "   • ✅ Ma'lumotlar bazasi orqali\n"
            response += "   • ✅ Log fayllar orqali\n"
            response += "   • ❌ Uchinchi tomonlarga uzatilmaydi\n"
            response += "   • ❌ Reklama maqsadlarida foydalanilmaydi\n"
            response += "   • ❌ Sotish yoki ijaraga berilmaydi\n\n"
            
            # Права пользователя на данные
            response += "👤 **FOYDALANUVCHI HUQUQLARI:**\n"
            response += "   • ✅ O'z ma'lumotlarini ko'rish\n"
            response += "   • ✅ Ma'lumotlarni o'chirish\n"
            response += "   • ✅ Ma'lumotlarni tahrirlash\n"
            response += "   • ✅ Ma'lumotlarni eksport qilish\n"
            response += "   • ✅ Ma'lumotlarni cheklash\n"
            response += "   • ✅ Ma'lumotlarni port qilish\n\n"
            
            # Время хранения
            response += "⏰ **SAQLASH MUDDATI:**\n"
            response += "   • ✅ Telegram ID: Cheksiz\n"
            response += "   • ✅ Guruh sozlamalari: Cheksiz\n"
            response += "   • ✅ Video ko'rish tarixi: 1 yil\n"
            response += "   • ✅ Log fayllar: 6 oy\n"
            response += "   • ✅ Backup fayllar: 1 yil\n"
            response += "   • ✅ Temporary fayllar: 24 soat\n\n"
            
            # Автоматическое удаление
            response += "🗑️ **AVTOMATIK O'CHIRISH:**\n"
            response += "   • ✅ Eski log fayllar\n"
            response += "   • ✅ Temporary fayllar\n"
            response += "   • ✅ Eski backup fayllar\n"
            response += "   • ✅ Eski session ma'lumotlari\n"
            response += "   • ✅ Eski cache ma'lumotlari\n"
            response += "   • ✅ Eski error log fayllar\n\n"
            
            # Мониторинг и аудит
            response += "📈 **MONITORING VA AUDIT:**\n"
            response += "   • ✅ Ma'lumotlar kirish va chiqish\n"
            response += "   • ✅ Foydalanish statistikasi\n"
            response += "   • ✅ Xavfsizlik hodisalari\n"
            response += "   • ✅ Admin harakatlari\n"
            response += "   • ✅ Sistema xatoliklari\n"
            response += "   • ✅ Performance ko'rsatkichlari\n\n"
            
            # Уведомления
            response += "🔔 **XABARNOMALAR:**\n"
            response += "   • ✅ Ma'lumotlar o'zgarishi\n"
            response += "   • ✅ Xavfsizlik hodisalari\n"
            response += "   • ✅ Sistema yangilanishlari\n"
            response += "   • ✅ Xatolik va ogohlantirishlar\n"
            response += "   • ✅ Backup va restore\n"
            response += "   • ✅ Monitoring va logging\n\n"
            
            # Контакты по конфиденциальности
            response += "📞 **MAXFIYLIK ALOQASI:**\n"
            response += "   • Telegram: @mohirbek\n"
            response += "   • Email: privacy@centris.uz\n"
            response += "   • Phone: +998 90 123 45 67\n"
            response += "   • Website: https://centris.uz/privacy\n"
            response += "   • Address: Toshkent, O'zbekiston\n\n"
            
            # Финальные условия
            response += "🎯 **YAKUNIY SHARTLAR:**\n"
            response += "   • Bu siyosat O'zbekiston qonunlari asosida\n"
            response += "   • Barcha nizolar Toshkent sudida hal qilinadi\n"
            response += "   • Siyosat o'zgarishi xabar beriladi\n"
            response += "   • Yangi versiyalar alohida ko'rsatiladi\n"
            response += "   • Ixtiyoriy buzish taqiqlanadi\n\n"
            
            # Время
            response += "📅 **VAQT:** " + str(datetime.now().strftime("%Y-%m-%d")) + "\n"
            response += "🌍 **JOYLASHUV:** Toshkent, O'zbekiston\n"
            response += "🔒 **MAXFIYLIK:** Faol va amal qiladi"
            
        except Exception as e:
            response += f"❌ **Xatolik:** {str(e)[:100]}...\n\n"
            response += "⚠️ Maxfiylik siyosati ma'lumotlari to'liq ko'rsatilmadi"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при показе политики конфиденциальности: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для условий использования
@dp.message_handler(commands=['terms_group_video'])
async def terms_group_video_command(message: types.Message):
    """
    Команда для условий использования
    """
    logger.info(f"📋 terms_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Формируем информацию об условиях использования
        response = "📋 **FOYDALANISH SHARTLARI VA QOIDALARI:**\n\n"
        
        try:
            # Общие условия
            response += "🌍 **UMUMIY SHARTLAR:**\n"
            response += "   • ✅ Faqat Centris Towers & Golden Lake loyihasi uchun\n"
            response += "   • ✅ Kommerchiy maqsadlarda foydalanish mumkin\n"
            response += "   • ✅ Guruh va kanal boshqaruvi\n"
            response += "   • ✅ Video yuborish va monitoring\n"
            response += "   • ✅ Backup va restore funksiyalari\n"
            response += "   • ✅ Qo'llab-quvvatlash va monitoring\n\n"
            
            # Технические требования
            response += "⚙️ **TEXNIK TALABLAR:**\n"
            response += "   • ✅ Python 3.8+ versiyasi\n"
            response += "   • ✅ PostgreSQL ma'lumotlar bazasi\n"
            response += "   • ✅ Telegram Bot API token\n"
            response += "   • ✅ Internet aloqasi\n"
            response += "   • ✅ Server yoki VPS\n"
            response += "   • ✅ Linux yoki Windows OS\n\n"
            
            # Функциональные возможности
            response += "🚀 **FUNKSIONAL IMKONIYATLAR:**\n"
            response += "   • ✅ Guruh video yuborish\n"
            response += "   • ✅ Avtomatik scheduling\n"
            response += "   • ✅ Whitelist boshqaruvi\n"
            response += "   • ✅ Monitoring va logging\n"
            response += "   • ✅ Backup va restore\n"
            response += "   • ✅ Admin paneli\n\n"
            
            # Ограничения использования
            response += "🚫 **FOYDALANISH CHEKLARI:**\n"
            response += "   • ❌ Boshqa loyihalarda foydalanish\n"
            response += "   • ❌ Kodni tahrirlash va o'zgartirish\n"
            response += "   • ❌ Qayta tarqatish va sotish\n"
            response += "   • ❌ Reverse engineering\n"
            response += "   • ❌ Xavfsizlik tizimini buzish\n"
            response += "   • ❌ Spam va yomon foydalanish\n\n"
            
            # Обязанности пользователя
            response += "👤 **FOYDALANUVCHI VAZIFALARI:**\n"
            response += "   • ✅ Sistema xavfsizligini saqlash\n"
            response += "   • ✅ Admin huquqlarini himoya qilish\n"
            response += "   • ✅ Ma'lumotlarni himoya qilish\n"
            response += "   • ✅ Sistema monitoring qilish\n"
            response += "   • ✅ Xatoliklarni xabar berish\n"
            response += "   • ✅ Yangilanishlarni o'rnatish\n\n"
            
            # Ответственность
            response += "⚖️ **JAVOBGARLIK:**\n"
            response += "   • ✅ Sistema ishlashi kafolatlanadi\n"
            response += "   • ✅ Xavfsizlik ta'minlanadi\n"
            response += "   • ✅ Qo'llab-quvvatlash mavjud\n"
            response += "   • ❌ Moliyaviy zarar uchun javobgar emas\n"
            response += "   • ❌ Ma'lumot yo'qolishi uchun javobgar emas\n"
            response += "   • ❌ Tizim uzilishi uchun javobgar emas\n\n"
            
            # Поддержка и обслуживание
            response += "🆘 **QO'LLAB-QUVVATLASH VA XIZMAT:**\n"
            response += "   • ✅ 24/7 monitoring\n"
            response += "   • ✅ Avtomatik xatolik boshqaruvi\n"
            response += "   • ✅ Sistema yangilanishlari\n"
            response += "   • ✅ Backup va restore\n"
            response += "   • ✅ Qo'llab-quvvatlash\n"
            response += "   • ✅ Dokumentatsiya\n\n"
            
            # Безопасность
            response += "🔐 **XAVFSIZLIK:**\n"
            response += "   • ✅ Admin autentifikatsiya\n"
            response += "   • ✅ Whitelist tizimi\n"
            response += "   • ✅ Guruh ruxsati\n"
            response += "   • ✅ Logging va monitoring\n"
            response += "   • ✅ Xatolik boshqaruvi\n"
            response += "   • ✅ Backup va restore\n\n"
            
            # Обновления и изменения
            response += "🔄 **YANGILANISHLAR VA O'ZGARISHLAR:**\n"
            response += "   • ✅ Avtomatik yangilanishlar\n"
            response += "   • ✅ Xavfsizlik yangilanishlari\n"
            response += "   • ✅ Yangi funksiyalar\n"
            response += "   • ✅ Xatoliklar tuzatish\n"
            response += "   • ✅ Performance yaxshilanishlari\n"
            response += "   • ✅ Monitoring va logging\n\n"
            
            # Прекращение использования
            response += "⏹️ **FOYDALANISHNI TO'XTATISH:**\n"
            response += "   • ✅ Ixtiyoriy to'xtatish\n"
            response += "   • ✅ Shartlarni buzish\n"
            response += "   • ✅ Litsenziya bekor qilish\n"
            response += "   • ✅ Ma'lumotlarni o'chirish\n"
            response += "   • ✅ Sistema o'chirish\n"
            response += "   • ✅ Qayta foydalanish taqiqi\n\n"
            
            # Контакты по условиям
            response += "📞 **SHARTLAR ALOQASI:**\n"
            response += "   • Telegram: @mohirbek\n"
            response += "   • Email: terms@centris.uz\n"
            response += "   • Phone: +998 90 123 45 67\n"
            response += "   • Website: https://centris.uz/terms\n"
            response += "   • Address: Toshkent, O'zbekiston\n\n"
            
            # Финальные условия
            response += "🎯 **YAKUNIY SHARTLAR:**\n"
            response += "   • Bu shartlar O'zbekiston qonunlari asosida\n"
            response += "   • Barcha nizolar Toshkent sudida hal qilinadi\n"
            response += "   • Shartlar o'zgarishi xabar beriladi\n"
            response += "   • Yangi versiyalar alohida ko'rsatiladi\n"
            response += "   • Ixtiyoriy buzish taqiqlanadi\n\n"
            
            # Время
            response += "📅 **VAQT:** " + str(datetime.now().strftime("%Y-%m-%d")) + "\n"
            response += "🌍 **JOYLASHUV:** Toshkent, O'zbekiston\n"
            response += "📋 **SHARTLAR:** Faol va amal qiladi"
            
        except Exception as e:
            response += f"❌ **Xatolik:** {str(e)[:100]}...\n\n"
            response += "⚠️ Foydalanish shartlari ma'lumotlari to'liq ko'rsatilmadi"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при показе условий использования: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Функция для получения клавиатуры выбора проекта
def get_project_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🏢 Centris Towers", callback_data="project_centris"),
        InlineKeyboardButton("🏘️ Golden Lake", callback_data="project_golden"),
        InlineKeyboardButton("🎯 Ikkalasi ham", callback_data="project_both")
    )
    return keyboard

# Функция для получения клавиатуры выбора времени отправки
def get_time_selection_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Предустановленные варианты времени
    keyboard.add(
        InlineKeyboardButton("🌅 07:00, 20:00", callback_data="time_preset_default"),
        InlineKeyboardButton("🌅 07:00, 19:00", callback_data="time_preset_early"),
    )
    keyboard.add(
        InlineKeyboardButton("🌅 09:00, 21:00", callback_data="time_preset_late"),
        InlineKeyboardButton("🌅 10:00, 18:00", callback_data="time_preset_mid"),
    )
    keyboard.add(
        InlineKeyboardButton("⏰ Boshqa vaqt", callback_data="time_custom"),
        InlineKeyboardButton("📅 3 marta kuniga", callback_data="time_three_times"),
    )
    keyboard.add(
        InlineKeyboardButton("✅ Tayyor", callback_data="time_confirm"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="group_cancel")
    )
    
    return keyboard

# Обработчики callback-запросов для set_group_video
@dp.callback_query_handler(lambda c: c.data.startswith("project_"), state="*")
async def process_project_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора проекта"""
    try:
        project = callback_query.data.replace("project_", "")
        await state.update_data(project=project)
        
        if project == "centris":
            await safe_edit_text(callback_query,
                "🏢 **Centris Towers**\n\n"
                "📺 **Sesonni tanlang:**",
                reply_markup=get_season_keyboard("centris")
            )
            await state.set_state(GroupVideoStates.waiting_for_centr_season.state)
            
        elif project == "golden":
            seasons = db.get_seasons_by_project("golden")
            if not seasons:
                await safe_edit_text(callback_query,
                    "❌ **Golden Lake uchun hech qanday seson topilmadi!**\n\n"
                    "Iltimos, avval seson qo'shing."
                , parse_mode="Markdown")
                await state.finish()
                return
                
            await safe_edit_text(callback_query,
                "🏢 **Golden Lake**\n\n"
                "📺 **Sesonni tanlang:**",
                reply_markup=get_season_keyboard("golden")
            )
            await state.set_state(GroupVideoStates.waiting_for_golden_season.state)
            
        elif project == "both":
            await safe_edit_text(callback_query,
                "🏢 **Centris + Golden**\n\n"
                "📺 **Centris Towers uchun sesonni tanlang:**",
                reply_markup=get_season_keyboard("centris")
            )
            await state.set_state(GroupVideoStates.waiting_for_centr_season.state)
            await state.update_data(both_selected=True, both_mode=True)
            
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при выборе проекта: {e}")
        await callback_query.answer("❌ Xatolik yuz berdi!")

@dp.callback_query_handler(lambda c: c.data.startswith("season_"), state="*")
async def process_season_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора сезона"""
    try:
        if callback_query.data == "no_seasons":
            await safe_edit_text(callback_query,
                "❌ **Hech qanday seson topilmadi!**\n\n"
                "Iltimos, avval seson qo'shing."
            , parse_mode="Markdown")
            await state.finish()
            return
            
        season_id = int(callback_query.data.replace("season_", ""))
        data = await state.get_data()
        project = data.get("project")
        
        if project == "centris" or (project == "both" and data.get("both_mode")):
            await state.update_data(centris_season_id=season_id)
            await safe_edit_text(callback_query,
                "🏢 **Centris Towers**\n"
                f"📺 **Seson:** {db.get_season_name(season_id)}\n\n"
                "🎬 **Boshlash uchun videoni tanlang:**",
                reply_markup=get_video_keyboard_from_db(db.get_videos_by_season(season_id), []),
                parse_mode="Markdown"
            )
            await state.set_state(GroupVideoStates.waiting_for_centr_video.state)
            
        elif project == "golden" or (project == "both" and not data.get("both_mode")):
            await state.update_data(golden_season_id=season_id)
            await safe_edit_text(callback_query,
                "🏢 **Golden Lake**\n"
                f"📺 **Seson:** {db.get_season_name(season_id)}\n\n"
                "🎬 **Boshlash uchun videoni tanlang:**",
                reply_markup=get_video_keyboard_from_db(db.get_videos_by_season(season_id), []),
                parse_mode="Markdown"
            )
            await state.set_state(GroupVideoStates.waiting_for_golden_video.state)
            
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при выборе сезона: {e}")
        await callback_query.answer("❌ Xatolik yuz berdi!")

@dp.callback_query_handler(lambda c: c.data.startswith("video_"), state="*")
async def process_video_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора видео"""
    try:
        if callback_query.data == "all_videos_sent":
            await safe_edit_text(callback_query,
                "❌ **Barcha video allaqachon yuborilgan!**\n\n"
                "Boshqa seson tanlang yoki yangi video qo'shing."
            , parse_mode="Markdown")
            await state.finish()
            return
            
        video_idx = int(callback_query.data.replace("video_", ""))
        data = await state.get_data()
        project = data.get("project")
        
        if project == "centris" or (project == "both" and data.get("both_mode")):
            await state.update_data(centris_start_video=video_idx)
            
            if data.get("both_mode"):
                # Если выбран оба проекта, переходим к Golden
                # Сбрасываем both_mode чтобы правильно обработать Golden
                await state.update_data(both_mode=False)
                await safe_edit_text(callback_query,
                    "🏢 **Centris Towers sozlandi!**\n\n"
                    "📺 **Golden Lake uchun sesonni tanlang:**",
                    reply_markup=get_season_keyboard("golden")
                )
                await state.set_state(GroupVideoStates.waiting_for_golden_season.state)
            else:
                # Только Centris - сохраняем настройки
                # Получаем обновленные данные с выбранным видео
                updated_data = await state.get_data()
                # Сохраняем настройки во временное состояние
                await state.update_data(
                    temp_settings=updated_data,
                    settings_complete=True
                )
                
                # Предлагаем выбрать группу для применения настроек
                await safe_edit_text(callback_query,
                    "✅ **Sozlamalar tayyor!**\n\n"
                    "🏢 **Endi guruhni tanlang:**\n\n"
                    "Qaysi guruhga bu sozlamalarni qo'llash kerak?",
                    reply_markup=get_group_selection_keyboard()
                )
                
                # Переходим к выбору группы
                await state.set_state(GroupVideoStates.waiting_for_group_selection.state)
                
        elif project == "golden" or (project == "both" and not data.get("both_mode")):
            await state.update_data(golden_start_video=video_idx)
            
            if project == "both":
                # Оба проекта - сохраняем настройки
                # Получаем обновленные данные с выбранным видео
                updated_data = await state.get_data()
                # Сохраняем настройки во временное состояние
                await state.update_data(
                    temp_settings=updated_data,
                    settings_complete=True
                )
                
                # Предлагаем выбрать группу для применения настроек
                await safe_edit_text(callback_query,
                    "✅ **Sozlamalar tayyor!**\n\n"
                    "🏢 **Endi guruhni tanlang:**\n\n"
                    "Qaysi guruhga bu sozlamalarni qo'llash kerak?",
                    reply_markup=get_group_selection_keyboard()
                )
                
                # Переходим к выбору группы
                await state.set_state(GroupVideoStates.waiting_for_group_selection.state)
            else:
                # Только Golden - сохраняем настройки
                # Получаем обновленные данные с выбранным видео
                updated_data = await state.get_data()
                # Сохраняем настройки во временное состояние
                await state.update_data(
                    temp_settings=updated_data,
                    settings_complete=True
                )
                
                # Предлагаем выбрать группу для применения настроек
                await safe_edit_text(callback_query,
                    "✅ **Sozlamalar tayyor!**\n\n"
                    "🏢 **Endi guruhni tanlang:**\n\n"
                    "Qaysi guruhga bu sozlamalarni qo'llash kerak?",
                    reply_markup=get_group_selection_keyboard()
                )
                
                # Переходим к выбору группы
                await state.set_state(GroupVideoStates.waiting_for_group_selection.state)
                
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при выборе видео: {e}")
        await callback_query.answer("❌ Xatolik yuz berdi!")

# Обработчик для выбора группы
@dp.callback_query_handler(lambda c: c.data.startswith('group_') or c.data.startswith('select_group_'), state=GroupVideoStates.waiting_for_group_selection)
async def process_group_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для выбора группы
    """
    try:
        action = callback_query.data
        logger.info(f"Получен callback: {action}")
        data = await state.get_data()
        temp_settings = data.get("temp_settings")
        
        if not temp_settings:
            await safe_edit_text(callback_query,"❌ **Xatolik!**\n\nSozlamalar topilmadi. Qaytadan boshlang.", parse_mode="Markdown")
            await state.finish()
            return
        
        if action == "group_current":
            # Применяем настройки к текущей группе
            chat_id = callback_query.message.chat.id
            if callback_query.message.chat.type in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
                # Обновляем chat_id в настройках
                temp_settings["chat_id"] = chat_id
                
                # Переходим к выбору времени отправки
                await safe_edit_text(callback_query,
                    "⏰ **Yuborish vaqtini tanlang:**\n\n"
                    "Video qachon yuborilishini tanlang. Bir nechta vaqt tanlashingiz mumkin.\n\n"
                    "📋 **Joriy sozlamalar:**\n"
                    f"• Loyiha: {temp_settings.get('project', 'N/A')}\n"
                    f"• Centris: {'✅' if temp_settings.get('project') in ['centris', 'both'] else '❌'}\n"
                    f"• Golden: {'✅' if temp_settings.get('project') in ['golden', 'both'] else '❌'}",
                    reply_markup=get_time_selection_keyboard()
                )
                await state.set_state(GroupVideoStates.waiting_for_send_times.state)
                await state.update_data(temp_settings=temp_settings)
                await callback_query.answer()
                return
            else:
                await safe_edit_text(callback_query,
                    "❌ **Xatolik!**\n\nBu buyruq faqat guruhlarda ishlaydi."
                , parse_mode="Markdown")
                await state.finish()
        
        elif action == "group_manual":
            # Запрашиваем ввод ID группы вручную
            await safe_edit_text(callback_query,
                "📝 **Guruh ID sini kiriting:**\n\n"
                "Guruh ID sini yuboring (masalan: -1001234567890)\n\n"
                "⚠️ **Eslatma:** Guruh ID si manfiy son bo'lishi kerak.",
                parse_mode="Markdown"
            )
            await state.set_state(GroupVideoStates.waiting_for_group_selection.state)
            await state.update_data(waiting_for_manual_id=True)
        
        elif action == "group_list":
            # Показываем список доступных групп с пагинацией
            groups = db.get_all_whitelisted_groups()
            logger.info(f"Найдено {len(groups)} разрешенных групп")
            for group_data in groups:
                if len(group_data) >= 3:
                    group_id, group_name, created_at = group_data
                else:
                    group_id, group_name = group_data
                logger.info(f"Группа: {group_name} (ID: {group_id})")
            if groups:
                response = "📋 **Mavjud guruhlar:**\n\n"
                response += "Guruh ID sini yuboring yoki ro'yxatdan tanlang:\n\n"
                
                # Добавляем текст с группами первой страницы
                response += create_paginated_groups_text(groups, page=0, title="Mavjud guruhlar")
                
                # Создаем пагинированную клавиатуру
                kb, total_pages, current_page = create_paginated_groups_keyboard(
                    groups, 
                    page=0, 
                    prefix="select_group", 
                    cancel_callback="group_cancel"
                )
                
                await safe_edit_text(callback_query, response, reply_markup=kb, parse_mode="Markdown")
            else:
                await safe_edit_text(callback_query,
                    "❌ **Guruhlar topilmadi!**\n\n"
                    "Ma'lumotlar bazasida guruhlar yo'q yoki hech biri whitelist da emas."
                , parse_mode="Markdown")
                await state.finish()
        
        elif action == "group_cancel":
            # Отменяем настройку
            await safe_edit_text(callback_query,
                "❌ **Sozlamalar bekor qilindi!**\n\n"
                "Hech qanday o'zgarish saqlanmadi."
            , parse_mode="Markdown")
            await state.finish()
        
        elif action.startswith("select_group_"):
            # Выбираем группу из списка
            group_id = action.replace("select_group_", "")
            temp_settings["chat_id"] = int(group_id)
            
            # Переходим к выбору времени отправки
            await safe_edit_text(callback_query,
                "⏰ **Yuborish vaqtini tanlang:**\n\n"
                "Video qachon yuborilishini tanlang. Bir nechta vaqt tanlashingiz mumkin.\n\n"
                "📋 **Joriy sozlamalar:**\n"
                f"• Loyiha: {temp_settings.get('project', 'N/A')}\n"
                f"• Centris: {'✅' if temp_settings.get('project') in ['centris', 'both'] else '❌'}\n"
                f"• Golden: {'✅' if temp_settings.get('project') in ['golden', 'both'] else '❌'}",
                reply_markup=get_time_selection_keyboard()
            )
            await state.set_state(GroupVideoStates.waiting_for_send_times.state)
            await state.update_data(temp_settings=temp_settings)
            await callback_query.answer()
            return
        
    except Exception as e:
        logger.error(f"Ошибка при выборе группы: {e}")
        await safe_edit_text(callback_query,f"❌ Xatolik yuz berdi: {e}")
        await state.finish()

async def update_video_progress(chat_id: int, project: str, season_id: int, video_position: int):
    """
    Обновляет прогресс просмотра видео для группы
    """
    try:
        # Получаем текущие настройки
        current_settings = db.get_group_video_settings(chat_id)
        if not current_settings:
            logger.error(f"Настройки для группы {chat_id} не найдены")
            return False
        
        # Обновляем позицию видео
        if project == 'centris':
            db.set_group_video_start(chat_id, 'centris', season_id, video_position + 1)
            logger.info(f"Группа {chat_id}: Centris прогресс обновлен до видео {video_position + 1}")
        elif project == 'golden':
            db.set_group_video_start(chat_id, 'golden', season_id, video_position + 1)
            logger.info(f"Группа {chat_id}: Golden прогресс обновлен до видео {video_position + 1}")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении прогресса видео для группы {chat_id}: {e}")
        return False

# Обработчик для ввода ID группы вручную
@dp.message_handler(state=GroupVideoStates.waiting_for_group_selection)
async def process_manual_group_id(message: types.Message, state: FSMContext):
    """
    Обработчик для ввода ID группы вручную
    """
    try:
        data = await state.get_data()
        temp_settings = data.get("temp_settings")
        waiting_for_manual_id = data.get("waiting_for_manual_id", False)
        
        if not temp_settings or not waiting_for_manual_id:
            await message.answer("❌ **Xatolik!**\n\nSozlamalar topilmadi yoki noto'g'ri holat.", parse_mode="Markdown")
            await state.finish()
            return
        
        # Пытаемся получить ID группы из сообщения
        try:
            group_id = int(message.text.strip())
        except ValueError:
            await message.answer(
                "❌ **Noto'g'ri format!**\n\n"
                "Guruh ID si son bo'lishi kerak.\n"
                "Masalan: -1001234567890"
            , parse_mode="Markdown")
            return
        
        # Проверяем, что ID группы отрицательный (группы имеют отрицательные ID)
        if group_id >= 0:
            await message.answer(
                "❌ **Noto'g'ri ID!**\n\n"
                "Guruh ID si manfiy son bo'lishi kerak.\n"
                "Masalan: -1001234567890"
            , parse_mode="Markdown")
            return
        
        # Обновляем chat_id в настройках
        temp_settings["chat_id"] = group_id
        
        # Переходим к выбору времени отправки
        await message.answer(
            "⏰ **Yuborish vaqtini tanlang:**\n\n"
            "Video qachon yuborilishini tanlang. Bir nechta vaqt tanlashingiz mumkin.\n\n"
            "📋 **Joriy sozlamalar:**\n"
            f"• Loyiha: {temp_settings.get('project', 'N/A')}\n"
            f"• Centris: {'✅' if temp_settings.get('project') in ['centris', 'both'] else '❌'}\n"
            f"• Golden: {'✅' if temp_settings.get('project') in ['golden', 'both'] else '❌'}",
            reply_markup=get_time_selection_keyboard()
        )
        await state.set_state(GroupVideoStates.waiting_for_send_times.state)
        await state.update_data(temp_settings=temp_settings)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке ID группы: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")
        await state.finish()

# Команда для обновления прогресса видео (для админов)
@dp.message_handler(commands=["update_video_progress"])
async def update_video_progress_command(message: types.Message):
    """
    Обновить прогресс видео для группы (только для админов)
    """
    try:
        # Проверяем права админа
        if not await is_admin_or_super_admin(message.from_user.id):
            await message.answer("❌ **Ruxsat yo'q!**\n\nBu buyruq faqat administratorlar uchun.", parse_mode="Markdown")
            return
        
        # Парсим команду: /update_video_progress <group_id> <project> <season_id> <video_position>
        args = message.text.split()
        if len(args) != 5:
            await message.answer(
                "📝 **Foydalanish:**\n\n"
                "`/update_video_progress <group_id> <project> <season_id> <video_position>`\n\n"
                "**Masalan:**\n"
                "`/update_video_progress -4964612772 centris 3 9`\n\n"
                "**Loyihalar:** `centris`, `golden`"
            , parse_mode="Markdown")
            return
        
        try:
            group_id = int(args[1])
            project = args[2].lower()
            season_id = int(args[3])
            video_position = int(args[4])
        except ValueError:
            await message.answer("❌ **Noto'g'ri format!**\n\nBarcha raqamlar son bo'lishi kerak.", parse_mode="Markdown")
            return
        
        if project not in ['centris', 'golden']:
            await message.answer("❌ **Noto'g'ri loyiha!**\n\nFaqat `centris` yoki `golden` bo'lishi mumkin.", parse_mode="Markdown")
            return
        
        if video_position < 0:
            await message.answer("❌ **Noto'g'ri pozitsiya!**\n\nVideo pozitsiyasi 0 dan katta bo'lishi kerak.", parse_mode="Markdown")
            return
        
        # Обновляем прогресс
        success = await update_video_progress(group_id, project, season_id, video_position)
        
        if success:
            await message.answer(
                f"✅ **Progress yangilandi!**\n\n"
                f"🏢 **Guruh ID:** {group_id}\n"
                f"🎬 **Loyiha:** {project.title()}\n"
                f"📺 **Sezon:** {season_id}\n"
                f"🎥 **Video:** {video_position + 1}\n\n"
                f"Endi guruh {video_position + 1}-video dan boshlab video olishi mumkin."
            )
        else:
            await message.answer("❌ **Xatolik yuz berdi!**\n\nProgress yangilanmadi.", parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"Ошибка при обновлении прогресса видео: {e}")
        await message.answer(f"❌ **Xatolik yuz berdi!**\n\n{e}", parse_mode="Markdown")

# Команда для автоматического обновления прогресса (для админов)
@dp.message_handler(commands=["auto_update_progress"])
async def auto_update_progress_command(message: types.Message):
    """
    Автоматически обновить прогресс для всех групп (только для админов)
    """
    try:
        # Проверяем права админа
        if not await is_admin_or_super_admin(message.from_user.id):
            await message.answer("❌ **Ruxsat yo'q!**\n\nBu buyruq faqat administratorlar uchun.", parse_mode="Markdown")
            return
        
        # Получаем все группы с настройками
        groups_settings = db.get_all_groups_with_settings()
        
        if not groups_settings:
            await message.answer("📋 **Guruhlar sozlamalari:**\n\n❌ Hech qanday guruh sozlamalari topilmadi.", parse_mode="Markdown")
            return
        
        updated_count = 0
        response = "🔄 **Avtomatik yangilash natijalari:**\n\n"
        
        for group in groups_settings:
            chat_id, centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video, viewed_videos, is_subscribed, group_name, send_times = group
            
            try:
                # Название группы уже получено из базы данных
                if not group_name or group_name == "Noma'lum guruh":
                    # Пытаемся получить актуальное название из Telegram
                    try:
                        group_info = await message.bot.get_chat(chat_id)
                        if group_info.title:
                            group_name = group_info.title
                            # Обновляем название в базе данных
                            db.update_group_name(chat_id, group_name)
                        elif group_info.first_name:
                            group_name = group_info.first_name
                            # Обновляем название в базе данных
                            db.update_group_name(chat_id, group_name)
                    except Exception as e:
                        logger.error(f"Не удалось получить название группы {chat_id}: {e}")
                        # Оставляем название из базы данных
                
                # Обновляем прогресс для Centris
                if centris_enabled and centris_season_id is not None:
                    # Получаем количество видео в сезоне
                    videos = db.get_videos_by_season(centris_season_id)
                    if videos and centris_start_video < len(videos) - 1:
                        # Увеличиваем прогресс на 1
                        new_progress = centris_start_video + 1
                        db.set_group_video_start(chat_id, 'centris', centris_season_id, new_progress)
                        response += f"✅ **{group_name}** (Centris): {centris_start_video + 1} → {new_progress + 1}\n"
                        updated_count += 1
                    else:
                        response += f"⚠️ **{group_name}** (Centris): Sezon tugadi\n"
                
                # Обновляем прогресс для Golden
                if golden_enabled and golden_season_id is not None:
                    # Получаем количество видео в сезоне
                    videos = db.get_videos_by_season(golden_season_id)
                    if videos and golden_start_video < len(videos) - 1:
                        # Увеличиваем прогресс на 1
                        new_progress = golden_start_video + 1
                        db.set_group_video_start(chat_id, 'golden', golden_season_id, new_progress)
                        response += f"✅ **{group_name}** (Golden): {golden_start_video + 1} → {new_progress + 1}\n"
                        updated_count += 1
                    else:
                        response += f"⚠️ **{group_name}** (Golden): Sezon tugadi\n"
                
            except Exception as e:
                logger.error(f"Ошибка при обновлении группы {chat_id}: {e}")
                response += f"❌ **Guruh {chat_id}**: Xatolik - {e}\n"
        
        response += f"\n📊 **Jami yangilangan:** {updated_count} guruh"
        
        # Разбиваем на части, если сообщение слишком длинное
        if len(response) > 4096:
            parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
            for i, part in enumerate(parts):
                await message.answer(f"🔄 **Qism {i+1}/{len(parts)}:**\n\n{part}")
        else:
            await message.answer(response)
            
    except Exception as e:
        logger.error(f"Ошибка при автоматическом обновлении прогресса: {e}")
        await message.answer(f"❌ **Xatolik yuz berdi!**\n\n{e}", parse_mode="Markdown")

# Команда для обновления названий групп (для админов)
@dp.message_handler(commands=["update_group_names"])
async def update_group_names_command(message: types.Message):
    """
    Обновить названия всех групп из Telegram (только для админов)
    """
    try:
        # Проверяем права админа
        if not await is_admin_or_super_admin(message.from_user.id):
            await message.answer("❌ **Ruxsat yo'q!**\n\nBu buyruq faqat administratorlar uchun.", parse_mode="Markdown")
            return
        
        # Получаем все группы с настройками
        groups_settings = db.get_all_groups_with_settings()
        
        if not groups_settings:
            await message.answer("📋 **Guruhlar sozlamalari:**\n\n❌ Hech qanday guruh sozlamalari topilmadi.", parse_mode="Markdown")
            return
        
        updated_count = 0
        failed_count = 0
        response = "🔄 **Nama'lum guruhlar yangilash natijalari:**\n\n"
        
        for group in groups_settings:
            chat_id, centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video, viewed_videos, is_subscribed, group_name, send_times = group
            
            # Пропускаем группы, у которых уже есть название
            if group_name and group_name != "Noma'lum guruh":
                continue
            
            try:
                # Пытаемся получить название группы из Telegram
                group_info = await message.bot.get_chat(chat_id)
                if group_info.title:
                    new_name = group_info.title
                    # Обновляем название в базе данных
                    if db.update_group_name(chat_id, new_name):
                        response += f"✅ **{chat_id}**: '{new_name}'\n"
                        updated_count += 1
                    else:
                        response += f"❌ **{chat_id}**: Bazaga yozishda xatolik\n"
                        failed_count += 1
                elif group_info.first_name:
                    new_name = group_info.first_name
                    # Обновляем название в базе данных
                    if db.update_group_name(chat_id, new_name):
                        response += f"✅ **{chat_id}**: '{new_name}'\n"
                        updated_count += 1
                    else:
                        response += f"❌ **{chat_id}**: Bazaga yozishda xatolik\n"
                        failed_count += 1
                else:
                    response += f"⚠️ **{chat_id}**: Noma'lum guruh\n"
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Ошибка при получении названия группы {chat_id}: {e}")
                response += f"❌ **{chat_id}**: {e}\n"
                failed_count += 1
        
        response += f"\n📊 **Natijalar:**\n"
        response += f"✅ Yangilangan: {updated_count}\n"
        response += f"❌ Xatolik: {failed_count}\n"
        response += f"📋 Jami: {len(groups_settings)}"
        
        # Разбиваем на части, если сообщение слишком длинное
        if len(response) > 4096:
            parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
            for i, part in enumerate(parts):
                await message.answer(f"🔄 **Qism {i+1}/{len(parts)}:**\n\n{part}")
        else:
            await message.answer(response)
            
    except Exception as e:
        logger.error(f"Ошибка при обновлении названий групп: {e}")
        await message.answer(f"❌ **Xatolik yuz berdi!**\n\n{e}", parse_mode="Markdown")

# Тестовая команда для отправки видео всем группам (для админов)
@dp.message_handler(commands=["test_send_video_all_groups"])
async def test_send_video_all_groups_command(message: types.Message):
    """
    Тестовая отправка видео всем группам (только для админов)
    """
    try:
        # Проверяем права админа
        if not await is_admin_or_super_admin(message.from_user.id):
            await message.answer("❌ **Ruxsat yo'q!**\n\nBu buyruq faqat administratorlar uchun.", parse_mode="Markdown")
            return
        
        # Парсим команду: /test_send_video_all_groups <project> <season_id> <video_position>
        args = message.text.split()
        if len(args) != 4:
            await message.answer(
                "📝 **Foydalanish:**\n\n"
                "`/test_send_video_all_groups <project> <season_id> <video_position>`\n\n"
                "**Masalan:**\n"
                "`/test_send_video_all_groups centris 2 5`\n\n"
                "**Loyihalar:** `centris`, `golden`"
            , parse_mode="Markdown")
            return
        
        try:
            project = args[1].lower()
            season_id = int(args[2])
            video_position = int(args[3])
        except ValueError:
            await message.answer("❌ **Noto'g'ri format!**\n\nBarcha raqamlar son bo'lishi kerak.", parse_mode="Markdown")
            return
        
        if project not in ['centris', 'golden']:
            await message.answer("❌ **Noto'g'ri loyiha!**\n\nFaqat `centris` yoki `golden` bo'lishi mumkin.", parse_mode="Markdown")
            return
        
        if video_position < 0:
            await message.answer("❌ **Noto'g'ri pozitsiya!**\n\nVideo pozitsiyasi 0 dan katta bo'lishi kerak.", parse_mode="Markdown")
            return
        
        # Получаем все группы с настройками
        groups_settings = db.get_all_groups_with_settings()
        
        if not groups_settings:
            await message.answer("📋 **Guruhlar sozlamalari:**\n\n❌ Hech qanday guruh sozlamalari topilmadi.", parse_mode="Markdown")
            return
        
        # Получаем видео для указанного сезона
        videos = db.get_videos_by_season(season_id)
        if not videos or video_position >= len(videos):
            await message.answer(f"❌ **Xatolik!**\n\nSezon {season_id} da {video_position + 1}-video mavjud emas.", parse_mode="Markdown")
            return
        
        video_url, video_title, video_pos = videos[video_position]
        
        # Отправляем видео всем группам
        sent_count = 0
        failed_count = 0
        response = f"🎬 **Test video yuborish natijalari:**\n\n"
        response += f"📺 **Sezon:** {season_id}\n"
        response += f"🎥 **Video:** {video_position + 1} - {video_title}\n"
        response += f"🔗 **URL:** {video_url}\n\n"
        
        for group in groups_settings:
            chat_id, centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video, viewed_videos, is_subscribed, group_name, send_times = group
            
            # Проверяем, включен ли проект для этой группы
            project_enabled = False
            
            if project == 'centris':
                if centris_enabled and centris_season_id:
                    project_enabled = True
            elif project == 'golden':
                if golden_enabled and golden_season_id:
                    project_enabled = True
            
            if not project_enabled:
                response += f"⚠️ **{group_name}**: Loyihalar o'chirilgan yoki sezon mos kelmaydi\n"
                failed_count += 1
                continue
            
            try:
                # Отправляем видео
                await message.bot.copy_message(
                    chat_id=int(chat_id),
                    from_chat_id=-1002550852551,  # ID канала
                    message_id=int(video_url.split('/')[-1]),
                    caption=f"🎬 **Test video**\n\n📺 Sezon: {season_id}\n🎥 Video: {video_position + 1}\n🏷️ {video_title}\n\n✅ Bu test video yuborish"
                )
                
                response += f"✅ **{group_name}**: Video yuborildi\n"
                sent_count += 1
                
                # Обновляем прогресс в базе данных
                if project == 'centris':
                    db.set_group_video_start(int(chat_id), 'centris', season_id, video_position + 1)
                elif project == 'golden':
                    db.set_group_video_start(int(chat_id), 'golden', season_id, video_position + 1)
                
            except Exception as e:
                logger.error(f"Ошибка при отправке видео в группу {chat_id}: {e}")
                response += f"❌ **{group_name}**: Xatolik - {e}\n"
                failed_count += 1
        
        response += f"\n📊 **Natijalar:**\n"
        response += f"✅ Yuborilgan: {sent_count}\n"
        response += f"❌ Xatolik: {failed_count}\n"
        response += f"📋 Jami: {len(groups_settings)}"
        
        # Разбиваем на части, если сообщение слишком длинное
        if len(response) > 4096:
            parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
            for i, part in enumerate(parts):
                await message.answer(f"🎬 **Qism {i+1}/{len(parts)}:**\n\n{part}")
        else:
            await message.answer(response)
            
    except Exception as e:
        logger.error(f"Ошибка при тестовой отправке видео: {e}")
        await message.answer(f"❌ **Xatolik yuz berdi!**\n\n{e}", parse_mode="Markdown")

# Команда для отправки всех запланированных видео во все группы (для админов)
@dp.message_handler(commands=["send_all_planned_videos"])
async def send_all_planned_videos_command(message: types.Message):
    """
    Отправить все запланированные видео во все группы (только для админов)
    """
    try:
        # Проверяем права админа
        if not await is_admin_or_super_admin(message.from_user.id):
            await message.answer("❌ **Ruxsat yo'q!**\n\nBu buyruq faqat administratorlar uchun.", parse_mode="Markdown")
            return
        
        # Получаем все группы с настройками
        groups_settings = db.get_all_groups_with_settings()
        
        if not groups_settings:
            await message.answer("📋 **Guruhlar sozlamalari:**\n\n❌ Hech qanday guruh sozlamalari topilmadi.", parse_mode="Markdown")
            return
        
        # Отправляем видео всем группам
        sent_count = 0
        failed_count = 0
        response = f"🎬 **Barcha rejalashtirilgan videolar yuborish natijalari:**\n\n"
        
        for group in groups_settings:
            chat_id, centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video, viewed_videos, is_subscribed, group_name, send_times = group
            
            group_sent = 0
            group_failed = 0
            
            try:
                # Отправляем видео Centris если включен
                if centris_enabled:
                    try:
                        # Получаем все сезоны Centris
                        all_seasons = db.get_all_seasons('centris')
                        if all_seasons:
                            current_season_id = centris_season_id if centris_season_id else all_seasons[0][0]
                            start_pos = centris_start_video if centris_start_video is not None else 0
                            
                            # Начинаем с текущего сезона
                            season_index = 0
                            for season in all_seasons:
                                season_id = season[0]
                                if season_id >= current_season_id:
                                    videos = db.get_videos_by_season(season_id)
                                    if videos:
                                        # Для первого сезона начинаем с указанной позиции, для остальных с начала
                                        if season_id == current_season_id:
                                            video_start = start_pos
                                        else:
                                            video_start = 0
                                        
                                        for i in range(video_start, len(videos)):
                                            try:
                                                video_url, video_title, video_pos = videos[i]
                                                
                                                await message.bot.copy_message(
                                                    chat_id=int(chat_id),
                                                    from_chat_id=-1002550852551,  # ID канала
                                                    message_id=int(video_url.split('/')[-1]),
                                                    caption=f"🎬 **Centris Towers**\n\n📺 Sezon: {season_id}\n🎥 Video: {i + 1}\n🏷️ {video_title}\n\n✅ Avtomatik yuborish"
                                                )
                                                
                                                group_sent += 1
                                                # Обновляем прогресс
                                                db.set_group_video_start(int(chat_id), 'centris', season_id, i + 1)
                                                
                                                # Небольшая задержка между видео
                                                await asyncio.sleep(1)
                                                
                                            except Exception as e:
                                                logger.error(f"Ошибка при отправке Centris видео {i} сезона {season_id} в группу {chat_id}: {e}")
                                                group_failed += 1
                                        
                                        # Больше не переключаем сезоны автоматически
                                        logger.info(f"Группа {chat_id}: Сезон Centris завершен. Используйте /set_group_video для смены сезона")
                                    
                                    season_index += 1
                    except Exception as e:
                        logger.error(f"Ошибка при получении видео Centris для группы {chat_id}: {e}")
                        group_failed += 1
                
                # Отправляем видео Golden если включен
                if golden_enabled:
                    try:
                        # Получаем все сезоны Golden
                        all_seasons = db.get_all_seasons('golden')
                        if all_seasons:
                            current_season_id = golden_season_id if golden_season_id else all_seasons[0][0]
                            start_pos = golden_start_video if golden_start_video is not None else 0
                            
                            # Начинаем с текущего сезона
                            season_index = 0
                            for season in all_seasons:
                                season_id = season[0]
                                if season_id >= current_season_id:
                                    videos = db.get_videos_by_season(season_id)
                                    if videos:
                                        # Для первого сезона начинаем с указанной позиции, для остальных с начала
                                        if season_id == current_season_id:
                                            video_start = start_pos
                                        else:
                                            video_start = 0
                                        
                                        for i in range(video_start, len(videos)):
                                            try:
                                                video_url, video_title, video_pos = videos[i]
                                                
                                                await message.bot.copy_message(
                                                    chat_id=int(chat_id),
                                                    from_chat_id=-1002550852551,  # ID канала
                                                    message_id=int(video_url.split('/')[-1]),
                                                    caption=f"🏊 **Golden Lake**\n\n📺 Sezon: {season_id}\n🎥 Video: {i + 1}\n🏷️ {video_title}\n\n✅ Avtomatik yuborish"
                                                )
                                                
                                                group_sent += 1
                                                # Обновляем прогресс
                                                db.set_group_video_start(int(chat_id), 'golden', season_id, i + 1)
                                                
                                                # Небольшая задержка между видео
                                                await asyncio.sleep(1)
                                                
                                            except Exception as e:
                                                logger.error(f"Ошибка при отправке Golden видео {i} сезона {season_id} в группу {chat_id}: {e}")
                                                group_failed += 1
                                        
                                        # Больше не переключаем сезоны автоматически
                                        logger.info(f"Группа {chat_id}: Сезон Golden завершен. Используйте /set_group_video для смены сезона")
                                    
                                    season_index += 1
                    except Exception as e:
                        logger.error(f"Ошибка при получении видео Golden для группы {chat_id}: {e}")
                        group_failed += 1
                
                if group_sent > 0:
                    response += f"✅ **{group_name}**: {group_sent} video yuborildi\n"
                    sent_count += group_sent
                elif group_failed > 0:
                    response += f"❌ **{group_name}**: {group_failed} xatolik\n"
                    failed_count += group_failed
                else:
                    response += f"⚠️ **{group_name}**: Barcha loyihalar o'chirilgan\n"
                
            except Exception as e:
                logger.error(f"Ошибка при обработке группы {chat_id}: {e}")
                response += f"❌ **{group_name}**: Xatolik - {e}\n"
                failed_count += 1
        
        response += f"\n📊 **Jami natijalar:**\n"
        response += f"✅ Yuborilgan: {sent_count} video\n"
        response += f"❌ Xatolik: {failed_count}\n"
        response += f"📋 Guruhlar: {len(groups_settings)}"
        
        # Разбиваем на части, если сообщение слишком длинное
        if len(response) > 4096:
            parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
            for i, part in enumerate(parts):
                await message.answer(f"🎬 **Qism {i+1}/{len(parts)}:**\n\n{part}")
        else:
            await message.answer(response)
            
    except Exception as e:
        logger.error(f"Ошибка при отправке всех запланированных видео: {e}")
        await message.answer(f"❌ **Xatolik yuz berdi!**\n\n{e}", parse_mode="Markdown")

# Вспомогательные функции
def get_season_keyboard(project):
    """Клавиатура для выбора сезона"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    kb = InlineKeyboardMarkup(row_width=2)
    seasons = db.get_seasons_by_project(project)
    if not seasons:
        kb.add(InlineKeyboardButton("❌ Нет сезонов", callback_data="no_seasons"))
        return kb
    
    for season_id, season_name in seasons:
        kb.add(InlineKeyboardButton(f"📺 {season_name}", callback_data=f"season_{season_id}"))
    return kb

def get_video_keyboard_from_db(videos, viewed):
    """Клавиатура для выбора видео"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    kb = InlineKeyboardMarkup(row_width=3)
    has_unwatched = False
    
    for url, title, position in videos:
        if position not in viewed:
            kb.add(InlineKeyboardButton(f"{position+1}. {title}", callback_data=f"video_{position}"))
            has_unwatched = True
    
    if not has_unwatched:
        kb.add(InlineKeyboardButton("❌ Все видео уже отправлены", callback_data="all_videos_sent"))
        return None
    
    return kb

def get_group_selection_keyboard():
    """Клавиатура для выбора группы"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    kb = InlineKeyboardMarkup(row_width=2)
    
    # Кнопка для текущей группы (если команда вызвана в группе)
    kb.add(InlineKeyboardButton("🏢 Hozirgi guruh", callback_data="group_current"))
    
    # Кнопка для ввода ID группы вручную
    kb.add(InlineKeyboardButton("📝 ID guruhni kiriting", callback_data="group_manual"))
    
    # Кнопка для выбора из списка доступных групп
    kb.add(InlineKeyboardButton("📋 Ro'yxatdan tanlang", callback_data="group_list"))
    
    # Кнопка для отмены
    kb.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="group_cancel"))
    
    return kb

async def save_group_settings(data):
    """Сохранение настроек группы"""
    try:
        chat_id = data.get("chat_id")
        project = data.get("project")
        
        # Определяем какие проекты включены
        centris_enabled = project in ["centris", "both"]
        golden_enabled = project in ["golden", "both"]
        
        # Получаем данные
        centris_season_id = data.get("centris_season_id") if centris_enabled else None
        centris_start_video = data.get("centris_start_video", 0)
        golden_season_id = data.get("golden_season_id") if golden_enabled else None
        golden_start_video = data.get("golden_start_video", 0)
        send_times = data.get("send_times", ["07:00", "11:00", "20:00"])
        
        # Убеждаемся что у нас есть все необходимые данные
        if centris_enabled and centris_season_id is None:
            logger.error(f"Centris включен но season_id не установлен для группы {chat_id}")
            raise ValueError("Centris season_id не установлен")
        if golden_enabled and golden_season_id is None:
            logger.error(f"Golden включен но season_id не установлен для группы {chat_id}")
            raise ValueError("Golden season_id не установлен")
        
        # Сохраняем в базу
        db.set_group_video_settings(
            chat_id,
            int(centris_enabled),
            centris_season_id,
            centris_start_video,
            int(golden_enabled),
            golden_season_id,
            golden_start_video
        )
        
        # Сохраняем стартовые позиции
        if centris_enabled and centris_season_id is not None:
            db.set_group_video_start(chat_id, 'centris', centris_season_id, centris_start_video)
            db.reset_group_viewed_videos(chat_id)
            
        if golden_enabled and golden_season_id is not None:
            db.set_group_video_start(chat_id, 'golden', golden_season_id, golden_start_video)
            db.reset_group_viewed_videos(chat_id)
        
        # Сохраняем время отправки
        db.set_group_send_times(chat_id, send_times)
        
        # Планируем задачи для конкретной группы
        schedule_single_group_jobs(chat_id)
        
        logger.info(f"Группа {chat_id}: настройки сохранены - Centris: {centris_enabled}, Golden: {golden_enabled}")
        
        # Возвращаем информацию о сохраненных настройках
        return {
            "centris_enabled": centris_enabled,
            "centris_season_id": centris_season_id,
            "centris_start_video": centris_start_video,
            "golden_enabled": golden_enabled,
            "golden_season_id": golden_season_id,
            "golden_start_video": golden_start_video
        }
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении настроек группы: {e}")
        raise

async def is_admin_or_super_admin(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь админом или супер-админом
    """
    return user_id in ADMINS or user_id in SUPER_ADMIN_IDS or db.is_admin(user_id)

# --- Массовая установка времени отправки всем группам ---
@dp.message_handler(commands=["set_all_groups_time"])  # Пример: /set_all_groups_time 07:30 12:00 20:15
async def set_all_groups_time_command(message: types.Message):
    """
    Админ-команда: установить общее время отправки для всех групп.
    Пример: /set_all_groups_time 07:30 12:00 20:15
    """
    try:
        # Проверяем права
        if not await is_admin_or_super_admin(message.from_user.id):
            await message.answer("❌ Ruxsat yo'q! Bu buyruq faqat administratorlar uchun.")
            return

        args = message.text.split()[1:]
        if not args:
            await message.answer(
                "🕒 Foydalanish: /set_all_groups_time HH:MM [HH:MM ...]\nMasalan: /set_all_groups_time 07:00 11:00 20:00"
            )
            return

        # Валидация формата времени
        validated_times = []
        for t in args:
            try:
                h, m = t.split(":")
                h = int(h); m = int(m)
                if not (0 <= h < 24 and 0 <= m < 60):
                    raise ValueError
                validated_times.append(f"{h:02d}:{m:02d}")
            except Exception:
                await message.answer(f"❌ Noto'g'ri vaqt formati: {t}. To'g'ri format: HH:MM")
                return

        # Обновляем в БД всем группам
        ok = db.set_send_times_for_all_groups(validated_times)
        if not ok:
            await message.answer("❌ Xatolik: bazaga yozishda muammo yuz berdi")
            return

        # Перепланируем задачи для всех групп
        groups_settings = db.get_all_groups_with_settings()
        for group in groups_settings:
            chat_id = group[0]
            schedule_single_group_jobs(chat_id)

        await message.answer(
            "✅ Barcha guruhlar uchun yuborish vaqti yangilandi: " + ", ".join(validated_times)
        )
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")

# --- КОМАНДА УДАЛЕНА: Больше не используем систему чередования сезонов ---
# Все сезоны теперь работают последовательно: 1 сезон до конца, потом 2 сезон, и так далее.

# --- Команда для просмотра прогресса групп ---
@dp.message_handler(commands=["show_groups_progress"])
async def show_groups_progress_command(message: types.Message):
    """
    Админ-команда: показать прогресс всех групп - последний индекс и список просмотренных видео
    """
    try:
        # Проверяем права
        if not await is_admin_or_super_admin(message.from_user.id):
            await message.answer("❌ Ruxsat yo'q! Bu buyruq faqat administratorlar uchun.")
            return

        # Получаем все группы с настройками
        groups_settings = db.get_all_groups_with_settings()
        
        if not groups_settings:
            await message.answer("📋 **Guruhlar progressi:**\n\n❌ Hech qanday guruh sozlamalari topilmadi.", parse_mode="Markdown")
            return

        response = "📊 **Guruhlar progressi:**\n\n"
        
        for group in groups_settings:
            chat_id, centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video, viewed_videos, is_subscribed, group_name, send_times = group
            
            # Получаем название группы
            if not group_name or group_name == "Noma'lum guruh":
                try:
                    group_info = await message.bot.get_chat(chat_id)
                    group_name = group_info.title or group_info.first_name or f"Guruh {chat_id}"
                except:
                    group_name = f"Guruh {chat_id}"
            
            response += f"🏢 **{group_name}** (ID: `{chat_id}`)\n"
            
            # Centris Towers прогресс
            if centris_enabled and centris_season_id:
                centris_detailed = db.get_group_viewed_videos_detailed_by_project(chat_id, "centris")
                centris_old = db.get_group_viewed_videos_by_project(chat_id, "centris")
                
                response += f"  🎬 **Centris Towers:**\n"
                response += f"    📺 Sezon: {centris_season_id}\n"
                response += f"    📊 Yangi tizim: {len(centris_detailed)} video ko'rilgan\n"
                response += f"    📋 Eski tizim: {len(centris_old)} video ko'rilgan\n"
                
                if centris_detailed:
                    # Показываем последние 5 просмотренных видео
                    last_5 = centris_detailed[-5:] if len(centris_detailed) > 5 else centris_detailed
                    response += f"    🎥 So'nggi ko'rilgan: {', '.join(last_5)}\n"
                else:
                    response += f"    🎥 Hech qanday video ko'rilmagan\n"
                
                # Показываем информацию о текущем сезоне (последовательная логика)
                if centris_detailed:
                    response += f"    🎯 Видео отправляются последовательно по выбранному сезону\n"
            else:
                response += f"  🎬 **Centris Towers:** ❌ O'chirilgan\n"
            
            # Golden Lake прогресс
            if golden_enabled and golden_season_id:
                golden_detailed = db.get_group_viewed_videos_detailed_by_project(chat_id, "golden_lake")
                golden_old = db.get_group_viewed_videos_by_project(chat_id, "golden_lake")
                
                response += f"  🏊 **Golden Lake:**\n"
                response += f"    📺 Sezon: {golden_season_id}\n"
                response += f"    📊 Yangi tizim: {len(golden_detailed)} video ko'rilgan\n"
                response += f"    📋 Eski tizim: {len(golden_old)} video ko'rilgan\n"
                
                if golden_detailed:
                    # Показываем последние 5 просмотренных видео
                    last_5 = golden_detailed[-5:] if len(golden_detailed) > 5 else golden_detailed
                    response += f"    🎥 So'nggi ko'rilgan: {', '.join(last_5)}\n"
                else:
                    response += f"    🎥 Hech qanday video ko'rilmagan\n"
                
                # Показываем информацию о текущем сезоне (последовательная логика)
                if golden_detailed:
                    response += f"    🎯 Видео отправляются последовательно по выбранному сезону\n"
            else:
                response += f"  🏊 **Golden Lake:** ❌ O'chirilgan\n"
            
            response += "\n" + "─" * 50 + "\n\n"
        
        # Разбиваем на части, если сообщение слишком длинное
        if len(response) > 4096:
            parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
            for i, part in enumerate(parts):
                await message.answer(f"📊 **Qism {i+1}/{len(parts)}:**\n\n{part}", parse_mode="Markdown")
        else:
            await message.answer(response, parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"Ошибка при показе прогресса групп: {e}")
        await message.answer("❌ **Xatolik yuz berdi!**\n\nIltimos, qaytadan urinib ko'ring.", parse_mode="Markdown")

# --- Команда для детального просмотра прогресса конкретной группы ---
@dp.message_handler(commands=["show_group_detailed_progress"])
async def show_group_detailed_progress_command(message: types.Message):
    """
    Админ-команда: показать детальный прогресс конкретной группы
    Использование: /show_group_detailed_progress <chat_id>
    """
    try:
        # Проверяем права
        if not await is_admin_or_super_admin(message.from_user.id):
            await message.answer("❌ Ruxsat yo'q! Bu buyruq faqat administratorlar uchun.")
            return

        # Парсим аргументы
        args = message.text.split()
        if len(args) != 2:
            await message.answer(
                "📝 **Foydalanish:**\n\n"
                "`/show_group_detailed_progress <chat_id>`\n\n"
                "**Masalan:**\n"
                "`/show_group_detailed_progress -1001234567890`"
            , parse_mode="Markdown")
            return

        try:
            chat_id = int(args[1])
        except ValueError:
            await message.answer("❌ **Noto'g'ri format!** Chat ID raqam bo'lishi kerak.")
            return

        # Получаем настройки группы
        settings = db.get_group_video_settings(chat_id)
        if not settings:
            await message.answer(f"❌ **Guruh topilmadi!**\n\nChat ID: `{chat_id}`", parse_mode="Markdown")
            return

        # Получаем название группы
        try:
            group_info = await message.bot.get_chat(chat_id)
            group_name = group_info.title or group_info.first_name or f"Guruh {chat_id}"
        except:
            group_name = f"Guruh {chat_id}"

        response = f"📊 **Detal progress:** {group_name}\n"
        response += f"🆔 **Chat ID:** `{chat_id}`\n\n"

        # Centris Towers детальный прогресс
        if settings[0]:  # centris_enabled
            centris_detailed = db.get_group_viewed_videos_detailed_by_project(chat_id, "centris")
            response += f"🎬 **Centris Towers:**\n"
            response += f"📊 **Jami ko'rilgan:** {len(centris_detailed)} video\n"
            
            if centris_detailed:
                response += f"📋 **Barcha ko'rilgan video:**\n"
                for i, video_key in enumerate(centris_detailed, 1):
                    response += f"  {i}. `{video_key}`\n"
            else:
                response += f"🎥 Hech qanday video ko'rilmagan\n"
        
        # Golden Lake детальный прогресс
        if settings[4]:  # golden_enabled
            golden_detailed = db.get_group_viewed_videos_detailed_by_project(chat_id, "golden_lake")
            response += f"\n🏊 **Golden Lake:**\n"
            response += f"📊 **Jami ko'rilgan:** {len(golden_detailed)} video\n"
            
            if golden_detailed:
                response += f"📋 **Barcha ko'rilgan video:**\n"
                for i, video_key in enumerate(golden_detailed, 1):
                    response += f"  {i}. `{video_key}`\n"
            else:
                response += f"🎥 Hech qanday video ko'rilmagan\n"

        await message.answer(response, parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"Ошибка при показе детального прогресса группы: {e}")
        await message.answer("❌ **Xatolik yuz berdi!**\n\nIltimos, qaytadan urinib ko'ring.", parse_mode="Markdown")

# --- Команда для сброса прогресса конкретной группы ---
@dp.message_handler(commands=["reset_group_progress"])
async def reset_group_progress_command(message: types.Message):
    """
    Админ-команда: сбросить прогресс конкретной группы
    Использование: /reset_group_progress <chat_id>
    """
    try:
        # Проверяем права
        if not await is_admin_or_super_admin(message.from_user.id):
            await message.answer("❌ Ruxsat yo'q! Bu buyruq faqat administratorlar uchun.")
            return

        # Парсим аргументы
        args = message.text.split()
        if len(args) != 2:
            await message.answer(
                "📝 **Foydalanish:**\n\n"
                "`/reset_group_progress <chat_id>`\n\n"
                "**Masalan:**\n"
                "`/reset_group_progress -1001234567890`"
            , parse_mode="Markdown")
            return

        try:
            chat_id = int(args[1])
        except ValueError:
            await message.answer("❌ **Noto'g'ri format!** Chat ID raqam bo'lishi kerak.")
            return

        # Получаем настройки группы
        settings = db.get_group_video_settings(chat_id)
        if not settings:
            await message.answer(f"❌ **Guruh topilmadi!**\n\nChat ID: `{chat_id}`", parse_mode="Markdown")
            return

        # Получаем название группы
        try:
            group_info = await message.bot.get_chat(chat_id)
            group_name = group_info.title or group_info.first_name or f"Guruh {chat_id}"
        except:
            group_name = f"Guruh {chat_id}"

        # Сбрасываем прогресс
        db.reset_group_viewed_videos(chat_id)
        db.reset_group_viewed_videos_detailed_by_project(chat_id, "centris")
        db.reset_group_viewed_videos_detailed_by_project(chat_id, "golden_lake")

        # Перепланируем задачи для этой группы
        schedule_single_group_jobs(chat_id)

        await message.answer(
            f"✅ **Progress reset qilindi!**\n\n"
            f"🏢 **Guruh:** {group_name}\n"
            f"🆔 **Chat ID:** `{chat_id}`\n\n"
            f"🔄 **Qilingan ishlar:**\n"
            f"• Eski progress tozalandi\n"
            f"• Yangi tizim progress tozalandi\n"
            f"• Vazifalar qayta rejalashtirildi\n\n"
            f"🎯 Guruh endi birinchi videodan boshlaydi!"
        , parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"Ошибка при сбросе прогресса группы: {e}")
        await message.answer("❌ **Xatolik yuz berdi!**\n\nIltimos, qaytadan urinib ko'ring.", parse_mode="Markdown")

# Команда для показа настроек всех групп (только для админов)
@dp.message_handler(commands=["admin_show_all_groups_settings"])
async def admin_show_all_groups_settings(message: types.Message):
    """
    Показать настройки всех групп (только для админов)
    """
    try:
        # Проверяем права админа
        if not await is_admin_or_super_admin(message.from_user.id):
            await message.answer("❌ **Ruxsat yo'q!**\n\nBu buyruq faqat administratorlar uchun.", parse_mode="Markdown")
            return
        
        # Получаем все группы с настройками
        groups_settings = db.get_all_groups_with_settings()
        
        if not groups_settings:
            await message.answer("📋 **Guruhlar sozlamalari:**\n\n❌ Hech qanday guruh sozlamalari topilmadi.", parse_mode="Markdown")
            return
        
        response = "📋 **Barcha guruhlar sozlamalari:**\n\n"
        
        for group in groups_settings:
            chat_id, centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video, viewed_videos, is_subscribed, group_name, send_times = group
            
            # Логируем значения для отладки
            logger.info(f"Группа {chat_id}: centris_start_video={centris_start_video}, golden_start_video={golden_start_video}")
            
            # Название группы уже получено из базы данных
            if not group_name or group_name == "Noma'lum guruh":
                # Пытаемся получить актуальное название из Telegram
                try:
                    group_info = await message.bot.get_chat(chat_id)
                    if group_info.title:
                        group_name = group_info.title
                        # Обновляем название в базе данных
                        db.update_group_name(chat_id, group_name)
                        logger.info(f"Группа {chat_id}: обновлено название '{group_name}'")
                    elif group_info.first_name:
                        group_name = group_info.first_name
                        # Обновляем название в базе данных
                        db.update_group_name(chat_id, group_name)
                        logger.info(f"Группа {chat_id}: обновлено название '{group_name}'")
                except Exception as e:
                    logger.error(f"Ошибка при получении названия группы {chat_id}: {e}")
                    # Оставляем название из базы данных
            
            response += f"🏢 **{group_name}** (ID: `{chat_id}`)\n"
            
            if centris_enabled:
                response += f"  🎬 Centris: ✅ Yoqilgan\n"
                if centris_season_id:
                    response += f"  📺 Sezon: {centris_season_id}\n"
                if centris_start_video is not None and centris_start_video >= 0:
                    response += f"  🎥 Video: {centris_start_video + 1}\n"
                else:
                    response += f"  🎥 Video: Sezondan boshlash\n"
            else:
                response += f"  🎬 Centris: ❌ O'chirilgan\n"
            
            if golden_enabled:
                response += f"  🏊 Golden: ✅ Yoqilgan\n"
                if golden_season_id:
                    response += f"  📺 Sezon: {golden_season_id}\n"
                if golden_start_video is not None and golden_start_video >= 0:
                    response += f"  🎥 Video: {golden_start_video + 1}\n"
                else:
                    response += f"  🎥 Video: Sezondan boshlash\n"
            else:
                response += f"  🏊 Golden: ❌ O'chirilgan\n"
            
            # Проверяем статус подписки вместо расписания
            if is_subscribed:
                response += f"  ⏰ Jadval: ✅ Yoqilgan (1)\n"
            else:
                response += f"  ⏰ Jadval: ❌ O'chirilgan\n"
            
            response += "\n" + "─" * 40 + "\n\n"
        
        # Разбиваем на части, если сообщение слишком длинное
        if len(response) > 4096:
            parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
            for i, part in enumerate(parts):
                await message.answer(f"📋 **Qism {i+1}/{len(parts)}:**\n\n{part}")
        else:
            await message.answer(response)
            
    except Exception as e:
        logger.error(f"Ошибка при показе настроек всех групп: {e}")
        await message.answer("❌ **Xatolik yuz berdi!**\n\nIltimos, qaytadan urinib ko'ring.", parse_mode="Markdown")


# Команда для отправки конкретного видео по номеру во все группы (только для админов)
@dp.message_handler(commands=["send_specific_video"])
async def send_specific_video_by_number(message: types.Message):
    """
    Отправить конкретное видео по номеру во все группы (только для админов)
    Использование: /send_specific_video <project> <season> <video_number>
    Пример: /send_specific_video centris 2 5
    """
    try:
        # Проверяем права админа
        if not await is_admin_or_super_admin(message.from_user.id):
            await message.answer("❌ **Ruxsat yo'q!**\n\nBu buyruq faqat administratorlar uchun.", parse_mode="Markdown")
            return
        
        # Парсим аргументы команды
        args = message.text.split()
        if len(args) != 4:
            await message.answer(
                "📝 **To'g'ri foydalanish:**\n\n"
                "`/send_specific_video <loyiha_nomi> <sezon> <video_number>`\n\n"
                "**Misol:**\n"
                "`/send_specific_video centris 2 5` - Centris 2-sezon 5-video\n"
                "`/send_specific_video golden 1 3` - Golden 1-sezon 3-video\n\n"
                "**Loyihalar:** centris, golden\n"
                "**Sezonlar:** 1, 2, 3, 4...\n"
                "**Video raqami:** 1, 2, 3, 4..."
            , parse_mode="Markdown")
            return
        
        project = args[1].lower()
        try:
            season_id = int(args[2])
            video_number = int(args[3])
        except ValueError:
            await message.answer("❌ **Xatolik!** Sezon va video raqami son bo'lishi kerak.", parse_mode="Markdown")
            return
        
        # Проверяем корректность проекта
        if project not in ['centris', 'golden']:
            await message.answer("❌ **Xatolik!** Loyiha `centris` yoki `golden` bo'lishi kerak.", parse_mode="Markdown")
            return
        
        # Проверяем корректность номера видео
        if video_number < 1:
            await message.answer("❌ **Xatolik!** Video raqami 1 dan katta bo'lishi kerak.", parse_mode="Markdown")
            return
        
        # Получаем все группы с настройками
        groups_settings = db.get_all_groups_with_settings()
        
        if not groups_settings:
            await message.answer("📋 **Guruhlar sozlamalari:**\n\n❌ Hech qanday guruh sozlamalari topilmadi.", parse_mode="Markdown")
            return
        
        # Получаем видео по сезону
        videos = db.get_videos_by_season(season_id)
        if not videos:
            await message.answer(f"❌ **Video topilmadi!**\n\nSezon {season_id} da video mavjud emas.", parse_mode="Markdown")
            return
        
        # Проверяем, существует ли указанный номер видео
        if video_number > len(videos):
            await message.answer(
                f"❌ **Video raqami noto'g'ri!**\n\n"
                f"Sezon {season_id} da faqat {len(videos)} ta video mavjud.\n"
                f"Siz {video_number} raqamini kiritdingiz."
            )
            return
        
        # Получаем информацию о видео
        video_url, video_title, video_pos = videos[video_number - 1]  # -1 потому что индексация с 0
        
        # Определяем название проекта для отображения
        project_name = "🎬 **Centris Towers**" if project == 'centris' else "🏊 **Golden Lake**"
        
        # Отправляем видео во все подходящие группы
        sent_count = 0
        failed_count = 0
        response = f"🎬 **{project_name} - Sezon {season_id}, Video {video_number} yuborish natijalari:**\n\n"
        response += f"📺 **Sezon:** {season_id}\n"
        response += f"🎥 **Video:** {video_number}\n"
        response += f"🏷️ **Nomi:** {video_title}\n\n"
        
        for group in groups_settings:
            chat_id, centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video, viewed_videos, is_subscribed, group_name, send_times = group
            
            # Проверяем, включен ли проект для этой группы И настроен ли для указанного сезона
            project_enabled = False
            if project == 'centris' and centris_enabled and centris_season_id == season_id:
                project_enabled = True
            elif project == 'golden' and golden_enabled and golden_season_id == season_id:
                project_enabled = True
            
            if not project_enabled:
                if project == 'centris':
                    if not centris_enabled:
                        response += f"⚠️ **{group_name}**: Centris o'chirilgan\n"
                    elif centris_season_id != season_id:
                        response += f"⚠️ **{group_name}**: Centris sezon {centris_season_id} uchun sozlangan (siz {season_id} kiritdingiz)\n"
                    else:
                        response += f"⚠️ **{group_name}**: Centris sozlanmagan\n"
                elif project == 'golden':
                    if not golden_enabled:
                        response += f"⚠️ **{group_name}**: Golden o'chirilgan\n"
                    elif golden_season_id != season_id:
                        response += f"⚠️ **{group_name}**: Golden sezon {golden_season_id} uchun sozlangan (siz {season_id} kiritdingiz)\n"
                    else:
                        response += f"⚠️ **{group_name}**: Golden sozlanmagan\n"
                continue
            
            try:
                # Отправляем видео
                await message.bot.copy_message(
                    chat_id=int(chat_id),
                    from_chat_id=-1002550852551,  # ID канала
                    message_id=int(video_url.split('/')[-1]),
                    caption=f"{project_name}\n\n📺 Sezon: {season_id}\n🎥 Video: {video_number}\n🏷️ {video_title}\n\n✅ Maxsus yuborish"
                )
                
                sent_count += 1
                response += f"✅ **{group_name}**: Video yuborildi\n"
                
                # Небольшая задержка между отправками
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Ошибка при отправке видео в группу {chat_id}: {e}")
                failed_count += 1
                response += f"❌ **{group_name}**: Xatolik - {e}\n"
        
        response += f"\n📊 **Jami natijalar:**\n"
        response += f"✅ Yuborilgan: {sent_count} guruh\n"
        response += f"❌ Xatolik: {failed_count}\n"
        response += f"📋 Guruhlar: {len(groups_settings)}"
        
        # Разбиваем на части, если сообщение слишком длинное
        if len(response) > 4096:
            parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
            for i, part in enumerate(parts):
                await message.answer(f"🎬 **Qism {i+1}/{len(parts)}:**\n\n{part}")
        else:
            await message.answer(response)
            
    except Exception as e:
        logger.error(f"Ошибка при отправке конкретного видео: {e}")
        await message.answer(f"❌ **Xatolik yuz berdi!**\n\n{e}", parse_mode="Markdown")

@dp.message_handler(commands=['send_now'])
async def send_video_now(message: types.Message):
    """Немедленная отправка видео в группу (для тестирования)"""
    user_id = message.from_user.id
    
    try:
        from handlers.users.video_scheduler import send_group_video_new
        
        # Проверяем whitelist
        chat_id = message.chat.id
        if not db.is_group_whitelisted(chat_id):
            await message.reply('❌ Эта группа не в whitelist')
            return
        
        # Проверяем настройки группы
        settings = db.get_group_video_settings(chat_id)
        if not settings:
            await message.reply('❌ Группа не настроена для рассылки видео')
            return
        
        centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video = settings
        
        sent = False
        
        if centris_enabled and centris_season_id:
            await message.reply('🎬 Отправляю видео Centris сейчас...')
            result = await send_group_video_new(chat_id, 'centris', centris_season_id, centris_start_video)
            if result:
                await message.reply('✅ Видео Centris отправлено')
                sent = True
            else:
                await message.reply('❌ Ошибка при отправке видео Centris')
        
        if golden_enabled and golden_season_id:
            await message.reply('🎬 Отправляю видео Golden Lake сейчас...')
            result = await send_group_video_new(chat_id, 'golden_lake', golden_season_id, golden_start_video)
            if result:
                await message.reply('✅ Видео Golden Lake отправлено')
                sent = True
            else:
                await message.reply('❌ Ошибка при отправке видео Golden Lake')
        
        if not sent:
            await message.reply('❌ Не удалось отправить ни одно видео')
            
    except Exception as e:
        logger.error(f"Ошибка в send_video_now: {e}")
        await message.reply(f'❌ Ошибка: {e}')

# Команда для исправления неправильных значений сезонов в базе данных
@dp.message_handler(commands=['fix_group_seasons'])
async def fix_group_seasons_command(message: types.Message):
    """
    Команда для исправления неправильных значений сезонов в базе данных
    """
    logger.info(f"🚀 fix_group_seasons вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        # Проверяем, что команда используется в группе
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            logger.warning("⚠️ Команда вызвана не в группе")
            await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
            return
        
        # Получаем текущие настройки группы
        settings = db.get_group_video_settings(chat_id)
        if not settings:
            await message.answer("❌ **Guruh uchun sozlamalar topilmadi!**", parse_mode="Markdown")
            return
        
        centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video = settings[:6]
        
        # Проверяем и исправляем неправильные значения сезонов
        fixed_centris = False
        fixed_golden = False
        
        # Исправляем Centris сезон
        if centris_enabled and centris_season_id:
            try:
                # Пытаемся преобразовать в число
                int(centris_season_id)
                logger.info(f"Centris season_id {centris_season_id} корректен")
            except (ValueError, TypeError):
                # Неправильное значение - заменяем на первый доступный сезон Centris
                logger.warning(f"Найдено неправильное значение Centris season_id: {centris_season_id}")
                centris_seasons = db.get_seasons_by_project("centris")
                if centris_seasons:
                    new_season_id = centris_seasons[0][0]  # Берем первый сезон
                    logger.info(f"Заменяем на первый доступный сезон: {new_season_id}")
                    db.set_group_video_start(chat_id, 'centris', new_season_id, 0)
                    fixed_centris = True
                else:
                    # Если нет сезонов Centris, отключаем проект
                    logger.warning("Нет доступных сезонов Centris, отключаем проект")
                    centris_enabled = False
                    fixed_centris = True
        
        # Исправляем Golden сезон
        if golden_enabled and golden_season_id:
            try:
                # Пытаемся преобразовать в число
                int(golden_season_id)
                logger.info(f"Golden season_id {golden_season_id} корректен")
            except (ValueError, TypeError):
                # Неправильное значение - заменяем на первый доступный сезон Golden
                logger.warning(f"Найдено неправильное значение Golden season_id: {golden_season_id}")
                golden_seasons = db.get_seasons_by_project("golden")
                if golden_seasons:
                    new_season_id = golden_seasons[0][0]  # Берем первый сезон
                    logger.info(f"Заменяем на первый доступный сезон: {new_season_id}")
                    db.set_group_video_start(chat_id, 'golden', new_season_id, 0)
                    fixed_golden = True
                else:
                    # Если нет сезонов Golden, отключаем проект
                    logger.warning("Нет доступных сезонов Golden, отключаем проект")
                    golden_enabled = False
                    fixed_golden = True
        
        # Обновляем настройки если что-то было исправлено
        if fixed_centris or fixed_golden:
            # Получаем обновленные значения
            if fixed_centris:
                if centris_enabled:
                    centris_season_id, centris_start_video = db.get_group_video_start(chat_id, 'centris')
                else:
                    centris_season_id = None
                    centris_start_video = 0
            
            if fixed_golden:
                if golden_enabled:
                    golden_season_id, golden_start_video = db.get_group_video_start(chat_id, 'golden')
                else:
                    golden_season_id = None
                    golden_start_video = 0
            
            # Сохраняем исправленные настройки
            db.set_group_video_settings(
                chat_id,
                int(centris_enabled),
                centris_season_id,
                centris_start_video,
                int(golden_enabled),
                golden_season_id,
                golden_start_video
            )
            
            # Очищаем просмотренные видео для корректного начала
            db.reset_group_viewed_videos(chat_id)
            
            # Перепланируем задачи
            from handlers.users.video_scheduler import schedule_single_group_jobs
            schedule_single_group_jobs(chat_id)
            
            response = "✅ **Guruh sozlamalari tuzatildi!**\n\n"
            if fixed_centris:
                if centris_enabled:
                    season_name = db.get_season_name(centris_season_id)
                    response += f"🏢 **Centris Towers:** {season_name} (ID: {centris_season_id})\n"
                else:
                    response += f"🏢 **Centris Towers:** O'chirildi (sezонlar topilmadi)\n"
            
            if fixed_golden:
                if golden_enabled:
                    season_name = db.get_season_name(golden_season_id)
                    response += f"🏊 **Golden Lake:** {season_name} (ID: {golden_season_id})\n"
                else:
                    response += f"🏊 **Golden Lake:** O'chirildi (sezonlar topilmadi)\n"
            
            response += f"\n🔄 Video tarqatish qaytadan boshlandi!"
            
            await message.answer(response, parse_mode="Markdown")
            logger.info(f"Исправлены настройки для группы {chat_id}")
        else:
            await message.answer("✅ **Guruh sozlamalari to'g'ri!**\n\nHech qanday tuzatish talab qilinmadi.", parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при исправлении настроек группы: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

# Команда для применения новой логики чередования проектов
@dp.message_handler(commands=['update_schedule'])
async def update_schedule_command(message: types.Message):
    """
    Команда для обновления планировщика с новой логикой чередования проектов
    """
    logger.info(f"🚀 update_schedule вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        # Проверяем, что команда используется в группе
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            logger.warning("⚠️ Команда вызвана не в группе")
            await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
            return
        
        # Получаем текущие настройки группы
        settings = db.get_group_video_settings(chat_id)
        if not settings:
            await message.answer("❌ **Guruh uchun sozlamalar topilmadi!**", parse_mode="Markdown")
            return
        
        # Перепланируем задачи с новой логикой
        from handlers.users.video_scheduler import schedule_single_group_jobs
        schedule_single_group_jobs(chat_id)
        
        # Получаем время отправки для отображения
        send_times_json = settings[6] if len(settings) > 6 else None
        try:
            if send_times_json:
                send_times = json.loads(send_times_json)
            else:
                send_times = ["07:00", "11:00", "20:00"]
        except:
            send_times = ["07:00", "11:00", "20:00"]
        
        centris_enabled = bool(settings[0])
        golden_enabled = bool(settings[3])
        
        response = "🔄 **Yangi jadval qo'llanildi!**\n\n"
        
        if centris_enabled and golden_enabled:
            response += "📋 **Yangi tarqatish tartibi:**\n"
            for i, send_time in enumerate(send_times):
                if i % 2 == 0:
                    response += f"• {send_time} - 🏢 **Centris Towers**\n"
                else:
                    response += f"• {send_time} - 🏊 **Golden Lake**\n"
            response += "\n✨ Loyihalar navbat bilan yuboriladi!"
        elif centris_enabled:
            response += f"📋 **Centris Towers:** {', '.join(send_times)}"
        elif golden_enabled:
            response += f"📋 **Golden Lake:** {', '.join(send_times)}"
        
        await message.answer(response, parse_mode="Markdown")
        logger.info(f"Планировщик обновлен для группы {chat_id}")
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении планировщика: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")


# Команда для удаления группы из системы
@dp.message_handler(commands=['remove_group'])
async def remove_group_command(message: types.Message, state: FSMContext):
    """
    Команда для удаления группы из системы
    Поддерживает два режима:
    1. /remove_group - интерактивный выбор группы
    2. /remove_group <group_id> - прямое удаление по ID
    """
    logger.info(f"🚀 remove_group вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        user_id = message.from_user.id
        
        # Проверяем права пользователя (только супер-админы)
        if user_id not in SUPER_ADMIN_IDS and not db.is_superadmin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super-adminlar foydalana oladi.", parse_mode="Markdown")
            return
        
        # Парсим аргументы команды
        args = message.text.split()
        
        # Если передан ID группы напрямую
        if len(args) > 1:
            try:
                group_id = int(args[1])
                logger.info(f"Прямое удаление группы по ID: {group_id}")
                
                # Получаем информацию о группе
                group_info = db.get_group_by_id(group_id)
                if not group_info:
                    await message.answer(f"❌ **Guruh topilmadi!**\n\nID `{group_id}` bo'yicha guruh ma'lumotlar bazasida yo'q.", parse_mode="Markdown")
                    return
                
                group_name = group_info[1]
                
                # Удаляем группу из базы данных
                success = db.remove_group_completely(group_id)
                
                if success:
                    # Пытаемся покинуть группу
                    try:
                        from loader import bot
                        await bot.leave_chat(group_id)
                        logger.info(f"Бот успешно покинул группу {group_id}")
                        leave_status = "✅ Bot guruhdan chiqdi"
                    except Exception as e:
                        logger.warning(f"Не удалось покинуть группу {group_id}: {e}")
                        leave_status = "⚠️ Bot guruhdan chiqa olmadi (guruh mavjud emas yoki botni oldin olib tashlangan)"
                    
                    # Удаляем задачи планировщика для этой группы
                    try:
                        from handlers.users.video_scheduler import scheduler
                        jobs_to_remove = []
                        for job in scheduler.get_jobs():
                            if job.id.endswith(f"_{group_id}"):
                                jobs_to_remove.append(job.id)
                        
                        for job_id in jobs_to_remove:
                            scheduler.remove_job(job_id)
                            logger.info(f"Удалена задача планировщика: {job_id}")
                        
                        schedule_status = f"✅ {len(jobs_to_remove)} ta vazifa o'chirildi"
                    except Exception as e:
                        logger.warning(f"Ошибка при удалении задач планировщика: {e}")
                        schedule_status = "⚠️ Vazifalarni o'chirishda muammo"
                    
                    await message.answer(
                        f"✅ **Guruh muvaffaqiyatli o'chirildi!**\n\n"
                        f"🏢 **Guruh:** {group_name}\n"
                        f"🆔 **ID:** `{group_id}`\n\n"
                        f"📊 **Natijalar:**\n"
                        f"• Ma'lumotlar bazasidan o'chirildi: ✅\n"
                        f"• {leave_status}\n"
                        f"• {schedule_status}",
                        parse_mode="Markdown"
                    )
                else:
                    await message.answer(
                        f"❌ **Guruhni o'chirishda xatolik!**\n\n"
                        f"🏢 **Guruh:** {group_name}\n"
                        f"🆔 **ID:** `{group_id}`\n\n"
                        f"Ma'lumotlar bazasidan o'chirib bo'lmadi.",
                        parse_mode="Markdown"
                    )
                
                return
                
            except ValueError:
                await message.answer(
                    "❌ **Noto'g'ri format!**\n\n"
                    "**Foydalanish:**\n"
                    "• `/remove_group` - guruhni tanlash\n"
                    "• `/remove_group <group_id>` - to'g'ridan-to'g'ri o'chirish\n\n"
                    "**Misollar:**\n"
                    "• `/remove_group`\n"
                    "• `/remove_group -1001234567890`",
                    parse_mode="Markdown"
                )
                return
            except Exception as e:
                logger.error(f"Ошибка при прямом удалении группы: {e}")
                await message.answer(f"❌ **Xatolik yuz berdi:** {e}", parse_mode="Markdown")
                return
        
        # Интерактивный режим - показываем список групп
        # Получаем список всех групп
        try:
            groups = db.get_all_groups()
            logger.info(f"Получено групп из базы: {len(groups)}")
            logger.info(f"Группы: {groups}")
        except Exception as e:
            logger.error(f"Ошибка при получении групп: {e}")
            await message.answer(f"❌ **Xatolik yuz berdi:** {e}", parse_mode="Markdown")
            return
        
        if not groups:
            logger.warning("Список групп пуст!")
            await message.answer("❌ **Guruhlar topilmadi!**\n\nMa'lumotlar bazasida guruhlar yo'q.", parse_mode="Markdown")
            return
        
        # Создаем пагинированную клавиатуру с группами
        response = "🗑️ **O'chirish uchun guruhni tanlang:**\n\n"
        response += "⚠️ **Diqqat!** Guruh to'liq o'chiriladi va bot guruhdan chiqadi.\n\n"
        response += "💡 **Yoki to'g'ridan-to'g'ri ID bilan:** `/remove_group <group_id>`\n\n"
        
        # Добавляем текст с группами первой страницы
        response += create_paginated_groups_text(groups, page=0, title="O'chirish uchun guruhni tanlang")
        
        # Создаем пагинированную клавиатуру
        kb, total_pages, current_page = create_paginated_groups_keyboard(
            groups, 
            page=0, 
            prefix="remove_group", 
            cancel_callback="remove_group_cancel"
        )
        
        await message.answer(response, reply_markup=kb, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при показе списка групп для удаления: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")


# Обработчик выбора группы для удаления
@dp.callback_query_handler(lambda c: c.data.startswith('remove_group_'))
async def remove_group_callback(callback_query: types.CallbackQuery):
    """Обработчик удаления группы"""
    logger.info(f"🗑️ remove_group_callback вызван с данными: {callback_query.data}")
    
    try:
        user_id = callback_query.from_user.id
        
        # Проверяем права пользователя (только супер-админы)
        if user_id not in SUPER_ADMIN_IDS and not db.is_superadmin(user_id):
            await callback_query.answer("❌ Sizda ruxsat yo'q!", show_alert=True)
            return
        
        if callback_query.data == "remove_group_cancel":
            await safe_edit_text(callback_query,
                "❌ **O'chirish bekor qilindi!**\n\nHech qanday guruh o'chirilmadi.",
                parse_mode="Markdown"
            )
            await callback_query.answer()
            return
        
        # Получаем ID группы
        group_id = int(callback_query.data.replace("remove_group_", ""))
        logger.info(f"Удаляем группу с ID: {group_id}")
        
        # Получаем информацию о группе
        group_info = db.get_group_by_id(group_id)
        group_name = group_info[1] if group_info else f"ID: {group_id}"
        
        # Удаляем группу из базы данных
        success = db.remove_group_completely(group_id)
        
        if success:
            # Пытаемся покинуть группу
            try:
                from loader import bot
                await bot.leave_chat(group_id)
                logger.info(f"Бот успешно покинул группу {group_id}")
                leave_status = "✅ Bot guruhdan chiqdi"
            except Exception as e:
                logger.warning(f"Не удалось покинуть группу {group_id}: {e}")
                leave_status = "⚠️ Bot guruhdan chiqa olmadi (guruh mavjud emas yoki botni oldin olib tashlangan)"
            
            # Удаляем задачи планировщика для этой группы
            try:
                from handlers.users.video_scheduler import scheduler
                jobs_to_remove = []
                for job in scheduler.get_jobs():
                    if job.id.endswith(f"_{group_id}"):
                        jobs_to_remove.append(job.id)
                
                for job_id in jobs_to_remove:
                    scheduler.remove_job(job_id)
                    logger.info(f"Удалена задача планировщика: {job_id}")
                
                schedule_status = f"✅ {len(jobs_to_remove)} ta vazifa o'chirildi"
            except Exception as e:
                logger.warning(f"Ошибка при удалении задач планировщика: {e}")
                schedule_status = "⚠️ Vazifalarni o'chirishda muammo"
            
            await safe_edit_text(callback_query,
                f"✅ **Guruh muvaffaqiyatli o'chirildi!**\n\n"
                f"🏢 **Guruh:** {group_name}\n"
                f"🆔 **ID:** `{group_id}`\n\n"
                f"📊 **Natijalar:**\n"
                f"• Ma'lumotlar bazasidan o'chirildi: ✅\n"
                f"• {leave_status}\n"
                f"• {schedule_status}",
                parse_mode="Markdown"
            )
        else:
            await safe_edit_text(callback_query,
                f"❌ **Guruhni o'chirishda xatolik!**\n\n"
                f"🏢 **Guruh:** {group_name}\n"
                f"🆔 **ID:** `{group_id}`\n\n"
                f"Ma'lumotlar bazasidan o'chirib bo'lmadi.",
                parse_mode="Markdown"
            )
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при удалении группы: {e}")
        await callback_query.answer(f"❌ Xatolik: {e}", show_alert=True)


# Обработчики пагинации для remove_group
@dp.callback_query_handler(lambda c: c.data.startswith('page_remove_group_'))
async def remove_group_pagination_callback(callback_query: types.CallbackQuery):
    """Обработчик пагинации для списка групп в remove_group"""
    logger.info(f"📄 remove_group_pagination_callback вызван с данными: {callback_query.data}")
    
    try:
        user_id = callback_query.from_user.id
        
        # Проверяем права пользователя (только супер-админы)
        if user_id not in SUPER_ADMIN_IDS and not db.is_superadmin(user_id):
            await callback_query.answer("❌ Sizda ruxsat yo'q!", show_alert=True)
            return
        
        # Получаем номер страницы
        page = int(callback_query.data.replace("page_remove_group_", ""))
        logger.info(f"Переходим на страницу {page} для remove_group")
        
        # Отвечаем на callback_query сразу
        await callback_query.answer()
        
        # Получаем список всех групп
        groups = db.get_all_groups()
        
        if not groups:
            await safe_edit_text(callback_query,
                "❌ **Guruhlar topilmadi!**\n\nMa'lumotlar bazasida guruhlar yo'q.",
                parse_mode="Markdown"
            )
            await callback_query.answer()
            return
        
        # Создаем текст и клавиатуру для новой страницы
        response = "🗑️ **O'chirish uchun guruhni tanlang:**\n\n"
        response += "⚠️ **Diqqat!** Guruh to'liq o'chiriladi va bot guruhdan chiqadi.\n\n"
        response += create_paginated_groups_text(groups, page=page, title="O'chirish uchun guruhni tanlang")
        
        kb, total_pages, current_page = create_paginated_groups_keyboard(
            groups, 
            page=page, 
            prefix="remove_group", 
            cancel_callback="remove_group_cancel"
        )
        
        await safe_edit_text(callback_query, response, reply_markup=kb, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при пагинации remove_group: {e}")
        await callback_query.answer(f"❌ Xatolik: {e}", show_alert=True)


# Обработчики пагинации для select_group (set_group_video)
@dp.callback_query_handler(lambda c: c.data.startswith('page_select_group_'), state=GroupVideoStates.waiting_for_group_selection)
async def select_group_pagination_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик пагинации для списка групп в set_group_video"""
    logger.info(f"📄 select_group_pagination_callback вызван с данными: {callback_query.data}")
    
    try:
        user_id = callback_query.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + SUPER_ADMIN_IDS and not db.is_admin(user_id):
            await callback_query.answer("❌ Sizda ruxsat yo'q!", show_alert=True)
            return
        
        # Получаем номер страницы
        page = int(callback_query.data.replace("page_select_group_", ""))
        logger.info(f"Переходим на страницу {page} для select_group")
        
        # Отвечаем на callback_query сразу
        await callback_query.answer()
        
        # Получаем список всех разрешенных групп
        groups = db.get_all_whitelisted_groups()
        
        if not groups:
            await safe_edit_text(callback_query,
                "❌ **Guruhlar topilmadi!**\n\nMa'lumotlar bazasida guruhlar yo'q yoki hech biri whitelist da emas.",
                parse_mode="Markdown"
            )
            await callback_query.answer()
            return
        
        # Создаем текст и клавиатуру для новой страницы
        response = "📋 **Mavjud guruhlar:**\n\n"
        response += "Guruh ID sini yuboring yoki ro'yxatdan tanlang:\n\n"
        response += create_paginated_groups_text(groups, page=page, title="Mavjud guruhlar")
        
        kb, total_pages, current_page = create_paginated_groups_keyboard(
            groups, 
            page=page, 
            prefix="select_group", 
            cancel_callback="group_cancel"
        )
        
        await safe_edit_text(callback_query, response, reply_markup=kb, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при пагинации select_group: {e}")
        await callback_query.answer(f"❌ Xatolik: {e}", show_alert=True)


# Обработчик для кнопки информации о странице
@dp.callback_query_handler(lambda c: c.data == "page_info")
async def page_info_callback(callback_query: types.CallbackQuery):
    """Обработчик для кнопки информации о странице"""
    await callback_query.answer("📄 Bu sahifa haqida ma'lumot", show_alert=False)


# Команда для удаления последних сообщений бота в группе (только для супер-админов)
@dp.message_handler(commands=['delete_bot_messages'])
async def delete_bot_messages_command(message: types.Message, state: FSMContext):
    """Удалить последние сообщения бота в группе"""
    user_id = message.from_user.id
    
    # Проверяем права доступа - только супер-админы
    if user_id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super-adminlar foydalana oladi.", parse_mode="Markdown")
        return
    
    # Получаем список всех групп
    groups = db.get_all_groups()
    
    if not groups:
        await message.answer("❌ **Hech qanday guruh topilmadi!**\n\nAvval botni guruhlarga qo'shing.")
        return
    
    # Создаем inline клавиатуру для выбора группы
    keyboard = types.InlineKeyboardMarkup()
    
    # Показываем первые 10 групп на странице
    page_size = 10
    total_pages = (len(groups) - 1) // page_size + 1
    current_page = 0
    start_idx = current_page * page_size
    end_idx = min(start_idx + page_size, len(groups))
    
    for i in range(start_idx, end_idx):
        group = groups[i]
        group_id = group[0]
        group_name = group[1] if group[1] else "Noma'lum guruh"
        
        # Ограничиваем длину названия группы
        if len(group_name) > 30:
            group_name = group_name[:27] + "..."
        
        keyboard.add(types.InlineKeyboardButton(
            text=f"📱 {group_name} (ID: {group_id})",
            callback_data=f"delete_msgs_group_{group_id}"
        ))
    
    # Добавляем кнопки навигации если нужно
    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️ Oldingi", callback_data=f"delete_msgs_page_{current_page - 1}"))
    
    nav_buttons.append(types.InlineKeyboardButton(f"📄 {current_page + 1}/{total_pages}", callback_data="page_info"))
    
    if current_page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton("Keyingi ➡️", callback_data=f"delete_msgs_page_{current_page + 1}"))
    
    if nav_buttons:
        keyboard.row(*nav_buttons)
    
    # Добавляем кнопку для ввода ID вручную
    keyboard.add(types.InlineKeyboardButton("🆔 Guruh ID ni qo'lda kiritish", callback_data="delete_msgs_manual_id"))
    keyboard.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_delete_msgs"))
    
    # Сохраняем список групп в состояние для пагинации
    await state.update_data(groups=groups, current_page=current_page)
    await DeleteBotMessagesStates.waiting_for_group_selection.set()
    
    await message.answer(
        "🗑️ **Bot xabarlarini o'chirish**\n\n"
        "📋 **Quyidagi guruhlardan birini tanlang:**\n\n"
        "Yoki guruh ID sini qo'lda kiritishingiz mumkin.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# Обработчик выбора группы для удаления сообщений
@dp.callback_query_handler(lambda c: c.data.startswith('delete_msgs_group_'), state=DeleteBotMessagesStates.waiting_for_group_selection)
async def delete_msgs_select_group_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора группы для удаления сообщений"""
    try:
        group_id = int(callback_query.data.split('_')[-1])
        
        # Сохраняем выбранную группу
        await state.update_data(selected_group_id=group_id)
        
        # Получаем информацию о группе
        group_info = db.get_group_by_id(group_id)
        group_name = group_info[1] if group_info and group_info[1] else "Noma'lum guruh"
        
        # Переходим к вводу количества сообщений
        await DeleteBotMessagesStates.waiting_for_message_count.set()
        
        await safe_edit_text(callback_query,
            f"🗑️ **Bot xabarlarini o'chirish**\n\n"
            f"📱 **Tanlangan guruh:** {group_name}\n"
            f"🆔 **Guruh ID:** `{group_id}`\n\n"
            f"📊 **Nechta oxirgi xabarni o'chirish kerak?**\n\n"
            f"Raqam kiriting (1-100 oralig'ida):",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при выборе группы для удаления сообщений: {e}")
        await callback_query.answer(f"❌ Xatolik: {e}", show_alert=True)


# Обработчик для ручного ввода ID группы
@dp.callback_query_handler(lambda c: c.data == 'delete_msgs_manual_id', state=DeleteBotMessagesStates.waiting_for_group_selection)
async def delete_msgs_manual_id_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик для ручного ввода ID группы"""
    await safe_edit_text(callback_query,
        "🆔 **Guruh ID ni kiriting**\n\n"
        "Guruh ID sini kiriting (masalan: -1001234567890):\n\n"
        "⚠️ **Diqqat:** ID aniq bo'lishi kerak!",
        parse_mode="Markdown"
    )


# Обработчик ввода ID группы вручную
@dp.message_handler(state=DeleteBotMessagesStates.waiting_for_group_selection)
async def delete_msgs_manual_id_input(message: types.Message, state: FSMContext):
    """Обработчик ввода ID группы вручную"""
    try:
        group_id = int(message.text.strip())
        
        # Проверяем, что группа существует в базе данных
        group_info = db.get_group_by_id(group_id)
        if not group_info:
            await message.answer(
                "❌ **Guruh topilmadi!**\n\n"
                "Kiritilgan ID bilan guruh ma'lumotlar bazasida mavjud emas.\n"
                "Iltimos, to'g'ri ID kiriting yoki ro'yxatdan tanlang.\n\n"
                "Qaytadan urinish uchun /delete_bot_messages buyrug'ini ishlatng."
            )
            await state.finish()
            return
        
        group_name = group_info[1] if group_info[1] else "Noma'lum guruh"
        
        # Сохраняем выбранную группу
        await state.update_data(selected_group_id=group_id)
        
        # Переходим к вводу количества сообщений
        await DeleteBotMessagesStates.waiting_for_message_count.set()
        
        await message.answer(
            f"✅ **Guruh tanlandi**\n\n"
            f"📱 **Guruh:** {group_name}\n"
            f"🆔 **ID:** `{group_id}`\n\n"
            f"📊 **Nechta oxirgi xabarni o'chirish kerak?**\n\n"
            f"Raqam kiriting (1-100 oralig'ida):",
            parse_mode="Markdown"
        )
        
    except ValueError:
        await message.answer(
            "❌ **Noto'g'ri format!**\n\n"
            "Iltimos, to'g'ri guruh ID sini kiriting.\n"
            "Masalan: -1001234567890\n\n"
            "Qaytadan urinish uchun /delete_bot_messages buyrug'ini ishlatng."
        )
        await state.finish()
    except Exception as e:
        logger.error(f"Ошибка при обработке ручного ввода ID группы: {e}")
        await message.answer("❌ **Xatolik yuz berdi!**")
        await state.finish()


# Обработчик ввода количества сообщений для удаления
@dp.message_handler(state=DeleteBotMessagesStates.waiting_for_message_count)
async def delete_msgs_count_input(message: types.Message, state: FSMContext):
    """Обработчик ввода количества сообщений для удаления"""
    try:
        message_count = int(message.text.strip())
        
        if message_count < 1 or message_count > 100:
            await message.answer(
                "❌ **Noto'g'ri son!**\n\n"
                "Xabarlar soni 1 dan 100 gacha bo'lishi kerak.\n"
                "Iltimos, qaytadan kiriting:"
            )
            return
        
        # Получаем данные из состояния
        data = await state.get_data()
        group_id = data.get('selected_group_id')
        
        if not group_id:
            await message.answer("❌ **Xatolik!** Guruh ma'lumotlari topilmadi.")
            await state.finish()
            return
        
        # Получаем информацию о группе
        group_info = db.get_group_by_id(group_id)
        group_name = group_info[1] if group_info and group_info[1] else "Noma'lum guruh"
        
        # Создаем клавиатуру подтверждения
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_delete_{group_id}_{message_count}"),
            types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_delete_msgs")
        )
        
        await message.answer(
            f"⚠️ **Tasdiqlash talab qilinadi**\n\n"
            f"📱 **Guruh:** {group_name}\n"
            f"🆔 **ID:** `{group_id}`\n"
            f"🗑️ **O'chiriladigan xabarlar:** {message_count} ta\n\n"
            f"**Bu amal qaytarib bo'lmaydi!**\n"
            f"Davom etishni istaysizmi?",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except ValueError:
        await message.answer(
            "❌ **Noto'g'ri format!**\n\n"
            "Iltimos, raqam kiriting (1-100 oralig'ida).\n"
            "Masalan: 10"
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке количества сообщений: {e}")
        await message.answer("❌ **Xatolik yuz berdi!**")
        await state.finish()


# Обработчик подтверждения удаления сообщений
@dp.callback_query_handler(lambda c: c.data.startswith('confirm_delete_'), state=DeleteBotMessagesStates.waiting_for_message_count)
async def confirm_delete_messages_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик подтверждения удаления сообщений"""
    try:
        # Парсим данные
        parts = callback_query.data.split('_')
        group_id = int(parts[2])
        message_count = int(parts[3])
        
        # Получаем информацию о группе
        group_info = db.get_group_by_id(group_id)
        group_name = group_info[1] if group_info and group_info[1] else "Noma'lum guruh"
        
        await safe_edit_text(callback_query,
            f"🔄 **Xabarlar o'chirilmoqda...**\n\n"
            f"📱 **Guruh:** {group_name}\n"
            f"🆔 **ID:** `{group_id}`\n"
            f"🗑️ **O'chiriladigan xabarlar:** {message_count} ta\n\n"
            f"Iltimos, kuting...",
            parse_mode="Markdown"
        )
        
        # Выполняем удаление сообщений
        from loader import bot
        deleted_count = 0
        errors_count = 0
        
        # Получаем информацию о боте для поиска его сообщений
        bot_user = await bot.get_me()
        bot_id = bot_user.id
        
        try:
            # Отправляем временное сообщение чтобы получить текущий message_id  
            temp_msg = await bot.send_message(group_id, "🔍 Bot xabarlarini qidirilmoqda...")
            current_message_id = temp_msg.message_id
            await bot.delete_message(group_id, current_message_id)
            
            logger.info(f"Начинаем поиск сообщений бота в группе {group_id} от ID {current_message_id}")
            
            # Простой подход: идем назад по ID и пытаемся удалить сообщения
            # Telegram API позволит удалить только сообщения бота
            checked_count = 0
            max_attempts = message_count * 20  # Проверяем больше сообщений чем нужно удалить
            
            # Начинаем с последнего message_id и идем назад
            for message_id in range(current_message_id - 1, max(1, current_message_id - max_attempts), -1):
                if deleted_count >= message_count:
                    break
                    
                try:
                    # Пытаемся удалить сообщение
                    # Telegram API позволит удалить только если это сообщение бота
                    await bot.delete_message(group_id, message_id)
                    deleted_count += 1
                    logger.info(f"✅ Удалено сообщение бота {message_id} в группе {group_id}")
                    
                    # Небольшая пауза чтобы не превысить лимиты API
                    await asyncio.sleep(0.3)
                    
                except Exception as delete_error:
                    error_msg = str(delete_error).lower()
                    
                    if "message to delete not found" in error_msg:
                        # Сообщение не существует - это нормально, продолжаем
                        pass
                    elif "message can't be deleted" in error_msg:
                        # Сообщение не от бота или слишком старое - продолжаем
                        pass
                    elif "not enough rights" in error_msg or "can't delete" in error_msg:
                        # У бота нет прав удалять или это не его сообщение - продолжаем
                        pass
                    elif "bad request" in error_msg and "message to delete not found" in error_msg:
                        # Еще один вариант "сообщение не найдено"
                        pass
                    else:
                        # Другие ошибки логируем но продолжаем
                        logger.debug(f"Ошибка при попытке удалить сообщение {message_id}: {delete_error}")
                        errors_count += 1
                    
                    continue
                
                checked_count += 1
                
                # Обновляем прогресс каждые 10 проверенных сообщений
                if checked_count % 10 == 0:
                    try:
                        await safe_edit_text(callback_query,
                            f"🔄 **Bot xabarlarini qidirilmoqda...**\n\n"
                            f"📱 **Guruh:** {group_name}\n"
                            f"🆔 **ID:** `{group_id}`\n"
                            f"🗑️ **O'chirildi:** {deleted_count}/{message_count}\n"
                            f"🔍 **Tekshirildi:** {checked_count} ta xabar\n\n"
                            f"Iltimos, kuting...",
                            parse_mode="Markdown"
                        )
                    except:
                        pass  # Игнорируем ошибки обновления прогресса
            
            logger.info(f"Поиск завершен. Удалено: {deleted_count}, проверено: {checked_count}, ошибок: {errors_count}")
        
        except Exception as main_error:
            logger.error(f"Основная ошибка при удалении сообщений: {main_error}")
            errors_count += 1
        
        # Завершаем процесс и показываем результат
        await state.finish()
        
        result_text = f"✅ **Xabarlar o'chirish yakunlandi!**\n\n"
        result_text += f"📱 **Guruh:** {group_name}\n"
        result_text += f"🆔 **ID:** `{group_id}`\n\n"
        result_text += f"📊 **Natijalar:**\n"
        result_text += f"• O'chirilgan xabarlar: **{deleted_count}** ta\n"
        result_text += f"• Maqsad: **{message_count}** ta\n"
        
        if deleted_count == 0:
            result_text += f"\n⚠️ **Hech qanday bot xabari o'chirilmadi**\n"
            result_text += f"Bu quyidagi sabablarga bog'liq bo'lishi mumkin:\n"
            result_text += f"• So'ngi vaqtlarda guruhda bot xabarlari yo'q\n"
            result_text += f"• Bot xabarlari 48 soatdan eski (Telegram cheklovi)\n"
            result_text += f"• Botda xabarlarni o'chirish huquqi yo'q\n"
            result_text += f"• Tekshirilgan oraliqda faqat foydalanuvchi xabarlari bor"
        elif deleted_count < message_count:
            result_text += f"\n✅ **Qisman muvaffaqiyatli**\n"
            result_text += f"• {deleted_count} ta bot xabari o'chirildi\n"
            result_text += f"• Qolgan {message_count - deleted_count} ta o'chirilmadi\n\n"
            result_text += f"**Sabablari:**\n"
            result_text += f"• Guruhda yetarli bot xabarlari yo'q\n"
            result_text += f"• Ba'zi xabarlar 48 soatdan eski\n"
            result_text += f"• Tekshirilgan oraliqda asosan foydalanuvchi xabarlari"
        else:
            result_text += f"\n🎉 **Muvaffaqiyatli yakunlandi!**\n"
            result_text += f"Barcha so'ralgan bot xabarlari o'chirildi."
        
        await safe_edit_text(callback_query, result_text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при подтверждении удаления сообщений: {e}")
        await callback_query.answer(f"❌ Xatolik: {e}", show_alert=True)
        await state.finish()


# Обработчик отмены удаления сообщений
@dp.callback_query_handler(lambda c: c.data == 'cancel_delete_msgs', state=[DeleteBotMessagesStates.waiting_for_group_selection, DeleteBotMessagesStates.waiting_for_message_count])
async def cancel_delete_messages_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик отмены удаления сообщений"""
    await state.finish()
    await safe_edit_text(callback_query,
        "❌ **Bekor qilindi**\n\n"
        "Xabarlarni o'chirish bekor qilindi.",
        parse_mode="Markdown"
    )


# Обработчик пагинации для выбора группы при удалении сообщений
@dp.callback_query_handler(lambda c: c.data.startswith('delete_msgs_page_'), state=DeleteBotMessagesStates.waiting_for_group_selection)
async def delete_msgs_pagination_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик пагинации для выбора группы при удалении сообщений"""
    try:
        new_page = int(callback_query.data.split('_')[-1])
        data = await state.get_data()
        groups = data.get('groups', [])
        
        if not groups:
            await callback_query.answer("❌ Guruhlar ro'yxati topilmadi", show_alert=True)
            return
        
        # Создаем клавиатуру для новой страницы
        keyboard = types.InlineKeyboardMarkup()
        
        page_size = 10
        total_pages = (len(groups) - 1) // page_size + 1
        
        if new_page < 0 or new_page >= total_pages:
            await callback_query.answer("❌ Noto'g'ri sahifa", show_alert=True)
            return
        
        start_idx = new_page * page_size
        end_idx = min(start_idx + page_size, len(groups))
        
        for i in range(start_idx, end_idx):
            group = groups[i]
            group_id = group[0]
            group_name = group[1] if group[1] else "Noma'lum guruh"
            
            if len(group_name) > 30:
                group_name = group_name[:27] + "..."
            
            keyboard.add(types.InlineKeyboardButton(
                text=f"📱 {group_name} (ID: {group_id})",
                callback_data=f"delete_msgs_group_{group_id}"
            ))
        
        # Добавляем кнопки навигации
        nav_buttons = []
        if new_page > 0:
            nav_buttons.append(types.InlineKeyboardButton("⬅️ Oldingi", callback_data=f"delete_msgs_page_{new_page - 1}"))
        
        nav_buttons.append(types.InlineKeyboardButton(f"📄 {new_page + 1}/{total_pages}", callback_data="page_info"))
        
        if new_page < total_pages - 1:
            nav_buttons.append(types.InlineKeyboardButton("Keyingi ➡️", callback_data=f"delete_msgs_page_{new_page + 1}"))
        
        if nav_buttons:
            keyboard.row(*nav_buttons)
        
        keyboard.add(types.InlineKeyboardButton("🆔 Guruh ID ni qo'lda kiritish", callback_data="delete_msgs_manual_id"))
        keyboard.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_delete_msgs"))
        
        # Обновляем состояние
        await state.update_data(current_page=new_page)
        
        await safe_edit_text(callback_query,
            "🗑️ **Bot xabarlarini o'chirish**\n\n"
            "📋 **Quyidagi guruhlardan birini tanlang:**\n\n"
            "Yoki guruh ID sini qo'lda kiritishingiz mumkin.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при пагинации delete_msgs: {e}")
        await callback_query.answer(f"❌ Xatolik: {e}", show_alert=True)


# Команда для создания тестовых сообщений (только для супер-админов)
@dp.message_handler(commands=['create_test_messages'])
async def create_test_messages_command(message: types.Message):
    """Создать тестовые сообщения в группе для проверки удаления"""
    user_id = message.from_user.id
    
    # Проверяем права доступа - только супер-админы
    if user_id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super-adminlar foydalana oladi.", parse_mode="Markdown")
        return
    
    # Парсим аргументы: /create_test_messages <group_id> [count]
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "❌ **Noto'g'ri format!**\n\n"
            "**Foydalanish:** `/create_test_messages <group_id> [count]`\n"
            "**Misollar:**\n"
            "• `/create_test_messages -1001234567890` - 5 ta test xabar\n"
            "• `/create_test_messages -1001234567890 10` - 10 ta test xabar",
            parse_mode="Markdown"
        )
        return
    
    try:
        group_id = int(args[1])
        count = int(args[2]) if len(args) > 2 else 5
        
        if count < 1 or count > 20:
            await message.answer("❌ **Xabarlar soni 1 dan 20 gacha bo'lishi kerak!**")
            return
        
        # Проверяем, что группа существует в базе данных
        group_info = db.get_group_by_id(group_id)
        if not group_info:
            await message.answer(
                "❌ **Guruh topilmadi!**\n\n"
                "Kiritilgan ID bilan guruh ma'lumotlar bazasida mavjud emas."
            )
            return
        
        group_name = group_info[1] if group_info[1] else "Noma'lum guruh"
        
        # Создаем тестовые сообщения
        sent_count = 0
        failed_count = 0
        from loader import bot
        
        await message.answer(
            f"🔄 **Test xabarlar yaratilmoqda...**\n\n"
            f"📱 **Guruh:** {group_name}\n"
            f"🆔 **ID:** `{group_id}`\n"
            f"📊 **Soni:** {count} ta xabar\n\n"
            f"Iltimos, kuting...",
            parse_mode="Markdown"
        )
        
        for i in range(1, count + 1):
            try:
                test_message = f"🧪 **Test xabar #{i}**\n\n" \
                              f"📅 **Sana:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n" \
                              f"🤖 **Bot:** Test rejimida\n" \
                              f"👤 **Yuboruvchi:** Super Admin\n\n" \
                              f"Bu xabar test maqsadida yaratilgan va keyinchalik o'chirilishi mumkin."
                
                sent_msg = await bot.send_message(group_id, test_message, parse_mode="Markdown")
                sent_count += 1
                logger.info(f"Создано тестовое сообщение {i}/{count} в группе {group_id}, ID: {sent_msg.message_id}")
                
                # Небольшая пауза между отправками
                await asyncio.sleep(0.5)
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Ошибка при создании тестового сообщения {i}: {e}")
                continue
        
        await message.answer(
            f"✅ **Test xabarlar yaratildi!**\n\n"
            f"📱 **Guruh:** {group_name}\n"
            f"🆔 **ID:** `{group_id}`\n\n"
            f"📊 **Natijalar:**\n"
            f"• Yaratilgan: **{sent_count}** ta\n"
            f"• Xatolik: **{failed_count}** ta\n"
            f"• Jami: **{count}** ta\n\n"
            f"💡 **Eslatma:** Endi `/delete_bot_messages` buyrug'i bilan ushbu xabarlarni o'chirishni sinab ko'ring.",
            parse_mode="Markdown"
        )
        
    except ValueError:
        await message.answer(
            "❌ **Noto'g'ri format!**\n\n"
            "Guruh ID va xabarlar soni raqam bo'lishi kerak.\n"
            "Masalan: `/create_test_messages -1001234567890 5`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка при создании тестовых сообщений: {e}")
        await message.answer("❌ **Xatolik yuz berdi!**")


# Команда для тестирования автопереключения сезонов (только для супер-админов)
@dp.message_handler(commands=['test_auto_season_switch'])
async def test_auto_season_switch_command(message: types.Message):
    """Тестировать автоматическое переключение сезонов"""
    user_id = message.from_user.id
    
    # Проверяем права доступа - только супер-админы
    if user_id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super-adminlar foydalana oladi.", parse_mode="Markdown")
        return
    
    # Парсим аргументы: /test_auto_season_switch <group_id> <project> <current_season_id>
    args = message.text.split()
    if len(args) < 4:
        await message.answer(
            "❌ **Noto'g'ri format!**\n\n"
            "**Foydalanish:** `/test_auto_season_switch <group_id> <project> <current_season_id>`\n"
            "**Misollar:**\n"
            "• `/test_auto_season_switch -1001234567890 centris 1`\n"
            "• `/test_auto_season_switch -1001234567890 golden 5`\n\n"
            "**Loyihalar:** `centris` yoki `golden`",
            parse_mode="Markdown"
        )
        return
    
    try:
        group_id = int(args[1])
        project = args[2].lower()
        current_season_id = int(args[3])
        
        if project not in ['centris', 'golden']:
            await message.answer("❌ **Loyiha noto'g'ri!**\n\nFaqat `centris` yoki `golden` bo'lishi mumkin.")
            return
        
        # Проверяем, что группа существует в базе данных
        group_info = db.get_group_by_id(group_id)
        if not group_info:
            await message.answer(
                "❌ **Guruh topilmadi!**\n\n"
                "Kiritilgan ID bilan guruh ma'lumotlar bazasida mavjud emas."
            )
            return
        
        group_name = group_info[1] if group_info[1] else "Noma'lum guruh"
        
        # Получаем информацию о текущем сезоне
        current_season_info = db.get_season_by_id(current_season_id)
        if not current_season_info:
            await message.answer(f"❌ **Sezon topilmadi!**\n\nID {current_season_id} bilan sezon mavjud emas.")
            return
        
        current_season_name = current_season_info[1]
        
        # Пытаемся найти следующий сезон
        next_season = db.get_next_season_in_project(current_season_id, project)
        
        if not next_season:
            await message.answer(f"❌ **Keyingi sezon topilmadi!**\n\nLoyiha {project} da sezon {current_season_id} dan keyin sezon yo'q.")
            return
        
        next_season_id, next_season_name = next_season
        
        # Показываем предварительную информацию
        await message.answer(
            f"🔄 **Avtomatik sezon almashtirish testi**\n\n"
            f"📱 **Guruh:** {group_name}\n"
            f"🆔 **ID:** `{group_id}`\n"
            f"🎬 **Loyiha:** {project.title()}\n\n"
            f"📊 **Sezon almashtirish:**\n"
            f"• Hozirgi sezon: `{current_season_id}` - {current_season_name}\n"
            f"• Keyingi sezon: `{next_season_id}` - {next_season_name}\n\n"
            f"🚀 **Avtomatik almashtirishni boshlayapman...**",
            parse_mode="Markdown"
        )
        
        # Выполняем автоматическое переключение
        success = db.auto_switch_to_next_season(group_id, project, current_season_id)
        
        if success:
            await message.answer(
                f"✅ **Muvaffaqiyatli almashtirild!**\n\n"
                f"📱 **Guruh:** {group_name}\n"
                f"🆔 **ID:** `{group_id}`\n"
                f"🎬 **Loyiha:** {project.title()}\n\n"
                f"📊 **Natija:**\n"
                f"• Sezon muvaffaqiyatli almashtirildi\n"
                f"• Yangi sezon: `{next_season_id}` - {next_season_name}\n"
                f"• Start video: `1` (birinchi video)\n\n"
                f"🎉 **Test muvaffaqiyatli tugadi!**\n"
                f"📹 **Keyingi video yuborish vaqtida yangi sezondan boshlanadi.**",
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                f"❌ **Almashtirish muvaffaqiyatsiz!**\n\n"
                f"Ma'lumotlar bazasida xatolik yuz berdi.\n"
                f"Loglarni tekshiring."
            )
        
    except ValueError:
        await message.answer(
            "❌ **Noto'g'ri format!**\n\n"
            "Guruh ID va sezon ID raqam bo'lishi kerak.\n"
            "Masalan: `/test_auto_season_switch -1001234567890 centris 1`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка при тестировании автопереключения сезонов: {e}")
        await message.answer("❌ **Xatolik yuz berdi!**")


# Команда для просмотра статистики сезонов (только для супер-админов)
@dp.message_handler(commands=['seasons_stats'])
async def seasons_stats_command(message: types.Message):
    """Показать статистику сезонов для всех проектов"""
    user_id = message.from_user.id
    
    # Проверяем права доступа - только супер-админы
    if user_id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super-adminlar foydalana oladi.", parse_mode="Markdown")
        return
    
    try:
        # Получаем сезоны для каждого проекта
        centris_seasons = db.get_seasons_by_project("centris")
        golden_seasons = db.get_seasons_by_project("golden")
        
        response = "📊 **Loyihalar bo'yicha sezonlar statistikasi**\n\n"
        
        # Centris Towers
        response += f"🏢 **Centris Towers:**\n"
        response += f"• Jami sezonlar: **{len(centris_seasons)}** ta\n"
        if centris_seasons:
            response += f"• Sezonlar ro'yxati:\n"
            for i, (season_id, season_name) in enumerate(centris_seasons, 1):
                response += f"  {i}. ID:`{season_id}` - {season_name[:50]}{'...' if len(season_name) > 50 else ''}\n"
        else:
            response += f"• ❌ Hech qanday sezon topilmadi\n"
        
        response += f"\n"
        
        # Golden Lake  
        response += f"🌊 **Golden Lake:**\n"
        response += f"• Jami sezonlar: **{len(golden_seasons)}** ta\n"
        if golden_seasons:
            response += f"• Sezonlar ro'yxati:\n"
            for i, (season_id, season_name) in enumerate(golden_seasons, 1):
                response += f"  {i}. ID:`{season_id}` - {season_name[:50]}{'...' if len(season_name) > 50 else ''}\n"
        else:
            response += f"• ❌ Hech qanday sezon topilmadi\n"
        
        response += f"\n📋 **Avtomatik almashtirish tartibi:**\n"
        response += f"🏢 **Centris:** Sezon 1 → 2 → 3 → 4 → 5 → 6 → 1 → ...\n"
        response += f"🌊 **Golden:** Sezon 1 → 2 → 3 → 4 → 1 → ...\n\n"
        response += f"💡 **Eslatma:** Agar sezonlar soni ko'rsatilganidan kam bo'lsa, yangi sezonlar qo'shish kerak."
        
        # Разбиваем на части если слишком длинное
        if len(response) > 4096:
            parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
            for i, part in enumerate(parts):
                await message.answer(f"📊 **Qism {i+1}/{len(parts)}:**\n\n{part}", parse_mode="Markdown")
        else:
            await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики сезонов: {e}")
        await message.answer("❌ **Xatolik yuz berdi!**")


# Команда для тестирования отправки видео (только для супер-админов)
@dp.message_handler(commands=['test_send_video'])
async def test_send_video_command(message: types.Message):
    """Тестировать отправку видео в группу"""
    user_id = message.from_user.id
    
    # Проверяем права доступа - только супер-админы
    if user_id not in SUPER_ADMIN_IDS:
        await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat super-adminlar foydalana oladi.", parse_mode="Markdown")
        return
    
    # Парсим аргументы: /test_send_video <group_id>
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "❌ **Noto'g'ri format!**\n\n"
            "**Foydalanish:** `/test_send_video <group_id>`\n"
            "**Misol:** `/test_send_video -1001234567890`",
            parse_mode="Markdown"
        )
        return
    
    try:
        group_id = int(args[1])
        
        # Проверяем, что группа существует в базе данных
        group_info = db.get_group_by_id(group_id)
        if not group_info:
            await message.answer(
                "❌ **Guruh topilmadi!**\n\n"
                "Kiritilgan ID bilan guruh ma'lumotlar bazasida mavjud emas."
            )
            return
        
        group_name = group_info[1] if group_info[1] else "Noma'lum guruh"
        
        # Получаем настройки группы
        settings = db.get_group_video_settings(group_id)
        if not settings:
            await message.answer(
                f"❌ **Guruh sozlanmagan!**\n\n"
                f"📱 Guruh: {group_name}\n"
                f"🆔 ID: `{group_id}`\n\n"
                f"Bu guruh uchun video sozlamalari topilmadi.\n"
                f"Avval `/set_group_video` buyrug'i bilan sozlang."
            )
            return
        
        centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video, send_times = settings
        
        # Подготавливаем статусы для отображения
        centris_status = '✅ Yoqilgan' if centris_enabled else '❌ O`chirilgan'
        golden_status = '✅ Yoqilgan' if golden_enabled else '❌ O`chirilgan'
        
        await message.answer(
            f"🧪 **Video yuborish testi**\n\n"
            f"📱 **Guruh:** {group_name}\n"
            f"🆔 **ID:** `{group_id}`\n\n"
            f"📊 **Sozlamalar:**\n"
            f"🏢 **Centris:** {centris_status}\n"
            f"  • Sezon ID: `{centris_season_id}`\n"
            f"  • Start video: `{centris_start_video}`\n\n"
            f"🌊 **Golden:** {golden_status}\n"
            f"  • Sezon ID: `{golden_season_id}`\n"
            f"  • Start video: `{golden_start_video}`\n\n"
            f"🚀 **Video yuborishni boshlayapman...**",
            parse_mode="Markdown"
        )
        
        # Тестируем отправку видео
        from handlers.users.video_scheduler import send_group_video_by_settings
        
        try:
            result = await send_group_video_by_settings(group_id)
            
            if result:
                await message.answer(
                    f"✅ **Video muvaffaqiyatli yuborildi!**\n\n"
                    f"📱 **Guruh:** {group_name}\n"
                    f"🆔 **ID:** `{group_id}`\n\n"
                    f"🎉 **Test muvaffaqiyatli tugadi!**"
                )
            else:
                await message.answer(
                    f"⚠️ **Video yuborilmadi**\n\n"
                    f"📱 **Guruh:** {group_name}\n"
                    f"🆔 **ID:** `{group_id}`\n\n"
                    f"📋 **Mumkin bo'lgan sabablar:**\n"
                    f"• Barcha videolar ko'rilgan\n"
                    f"• Loyihalar o'chirilgan\n"
                    f"• Sezon ID noto'g'ri\n"
                    f"• Video ma'lumotlar bazasida yo'q\n\n"
                    f"💡 **Tekshirib ko'ring:** loglarni va sozlamalarni"
                )
        except Exception as e:
            logger.error(f"Ошибка при тестировании отправки видео: {e}")
            await message.answer(
                f"❌ **Xatolik yuz berdi!**\n\n"
                f"📱 **Guruh:** {group_name}\n"
                f"🆔 **ID:** `{group_id}`\n"
                f"🔥 **Xatolik:** `{str(e)}`\n\n"
                f"Loglarni tekshiring va qaytadan urinib ko'ring."
            )
        
    except ValueError:
        await message.answer(
            "❌ **Noto'g'ri format!**\n\n"
            "Guruh ID raqam bo'lishi kerak.\n"
            "Masalan: `/test_send_video -1001234567890`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка при тестировании отправки видео: {e}")
        await message.answer("❌ **Xatolik yuz berdi!**")
