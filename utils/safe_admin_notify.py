"""
Безопасная отправка уведомлений администраторам
"""

import logging
from aiogram.utils.exceptions import CantInitiateConversation, BotBlocked, UserDeactivated
from data.config import ADMINS, SUPER_ADMIN_ID


async def safe_send_to_admins(bot, message_text, **kwargs):
    """
    Безопасно отправляет сообщение всем администраторам
    
    Args:
        bot: Экземпляр бота
        message_text: Текст сообщения
        **kwargs: Дополнительные параметры для send_message (reply_markup, parse_mode и т.д.)
    
    Returns:
        int: Количество успешно отправленных сообщений
    """
    success_count = 0
    
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, message_text, **kwargs)
            success_count += 1
            logging.info(f"Уведомление отправлено администратору {admin_id}")
            
        except CantInitiateConversation:
            logging.warning(f"Не удалось отправить уведомление администратору {admin_id}: пользователь не начинал диалог с ботом")
        except BotBlocked:
            logging.warning(f"Не удалось отправить уведомление администратору {admin_id}: бот заблокирован пользователем")
        except UserDeactivated:
            logging.warning(f"Не удалось отправить уведомление администратору {admin_id}: пользователь деактивирован")
        except Exception as e:
            logging.error(f"Неожиданная ошибка при отправке уведомления администратору {admin_id}: {e}")
    
    return success_count


async def safe_send_to_admin(bot, admin_id, message_text, **kwargs):
    """
    Безопасно отправляет сообщение конкретному администратору
    
    Args:
        bot: Экземпляр бота
        admin_id: ID администратора
        message_text: Текст сообщения
        **kwargs: Дополнительные параметры для send_message
    
    Returns:
        bool: True если сообщение отправлено успешно, False в противном случае
    """
    try:
        await bot.send_message(admin_id, message_text, **kwargs)
        logging.info(f"Уведомление отправлено администратору {admin_id}")
        return True
        
    except CantInitiateConversation:
        logging.warning(f"Не удалось отправить уведомление администратору {admin_id}: пользователь не начинал диалог с ботом")
        return False
    except BotBlocked:
        logging.warning(f"Не удалось отправить уведомление администратору {admin_id}: бот заблокирован пользователем")
        return False
    except UserDeactivated:
        logging.warning(f"Не удалось отправить уведомление администратору {admin_id}: пользователь деактивирован")
        return False
    except Exception as e:
        logging.error(f"Неожиданная ошибка при отправке уведомления администратору {admin_id}: {e}")
        return False


async def safe_send_error_notification(bot, error_message, error_details=None, **kwargs):
    """
    Безопасно отправляет уведомление об ошибке конкретному пользователю
    
    Args:
        bot: Экземпляр бота
        error_message: Основное сообщение об ошибке
        error_details: Дополнительные детали ошибки (опционально)
        **kwargs: Дополнительные параметры для send_message
    
    Returns:
        bool: True если сообщение отправлено успешно, False в противном случае
    """
    from datetime import datetime
    
    # Форматируем сообщение об ошибке
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    full_message = f"🚨 **Ошибка в боте**\n\n"
    full_message += f"⏰ **Время:** `{timestamp}`\n"
    full_message += f"❌ **Ошибка:** {error_message}\n"
    
    if error_details:
        full_message += f"📋 **Детали:** `{error_details}`\n"
    
    full_message += f"\n🔧 **ID пользователя:** `{SUPER_ADMIN_ID}`"
    
    try:
        await bot.send_message(
            SUPER_ADMIN_ID, 
            full_message, 
            parse_mode="Markdown",
            **kwargs
        )
        logging.info(f"Уведомление об ошибке отправлено пользователю {SUPER_ADMIN_ID}")
        return True
        
    except CantInitiateConversation:
        logging.warning(f"Не удалось отправить уведомление об ошибке пользователю {SUPER_ADMIN_ID}: пользователь не начинал диалог с ботом")
        return False
    except BotBlocked:
        logging.warning(f"Не удалось отправить уведомление об ошибке пользователю {SUPER_ADMIN_ID}: бот заблокирован пользователем")
        return False
    except UserDeactivated:
        logging.warning(f"Не удалось отправить уведомление об ошибке пользователю {SUPER_ADMIN_ID}: пользователь деактивирован")
        return False
    except Exception as e:
        logging.error(f"Неожиданная ошибка при отправке уведомления об ошибке пользователю {SUPER_ADMIN_ID}: {e}")
        return False


async def safe_send_error_to_all_admins(bot, error_message, error_details=None, **kwargs):
    """
    Безопасно отправляет уведомление об ошибке всем администраторам и конкретному пользователю
    
    Args:
        bot: Экземпляр бота
        error_message: Основное сообщение об ошибке
        error_details: Дополнительные детали ошибки (опционально)
        **kwargs: Дополнительные параметры для send_message
    
    Returns:
        int: Количество успешно отправленных сообщений
    """
    from datetime import datetime
    
    # Форматируем сообщение об ошибке
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    full_message = f"🚨 **Ошибка в боте**\n\n"
    full_message += f"⏰ **Время:** `{timestamp}`\n"
    full_message += f"❌ **Ошибка:** {error_message}\n"
    
    if error_details:
        full_message += f"📋 **Детали:** `{error_details}`\n"
    
    success_count = 0
    
    # Отправляем всем администраторам
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, full_message, parse_mode="Markdown", **kwargs)
            success_count += 1
            logging.info(f"Уведомление об ошибке отправлено администратору {admin_id}")
            
        except CantInitiateConversation:
            logging.warning(f"Не удалось отправить уведомление об ошибке администратору {admin_id}: пользователь не начинал диалог с ботом")
        except BotBlocked:
            logging.warning(f"Не удалось отправить уведомление об ошибке администратору {admin_id}: бот заблокирован пользователем")
        except UserDeactivated:
            logging.warning(f"Не удалось отправить уведомление об ошибке администратору {admin_id}: пользователь деактивирован")
        except Exception as e:
            logging.error(f"Неожиданная ошибка при отправке уведомления об ошибке администратору {admin_id}: {e}")
    
    # Отправляем конкретному пользователю (если он не в списке админов)
    if SUPER_ADMIN_ID not in ADMINS:
        try:
            await bot.send_message(SUPER_ADMIN_ID, full_message, parse_mode="Markdown", **kwargs)
            success_count += 1
            logging.info(f"Уведомление об ошибке отправлено пользователю {SUPER_ADMIN_ID}")
            
        except CantInitiateConversation:
            logging.warning(f"Не удалось отправить уведомление об ошибке пользователю {SUPER_ADMIN_ID}: пользователь не начинал диалог с ботом")
        except BotBlocked:
            logging.warning(f"Не удалось отправить уведомление об ошибке пользователю {SUPER_ADMIN_ID}: бот заблокирован пользователем")
        except UserDeactivated:
            logging.warning(f"Не удалось отправить уведомление об ошибке пользователю {SUPER_ADMIN_ID}: пользователь деактивирован")
        except Exception as e:
            logging.error(f"Неожиданная ошибка при отправке уведомления об ошибке пользователю {SUPER_ADMIN_ID}: {e}")
    
    return success_count
