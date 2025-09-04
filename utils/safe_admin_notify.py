"""
Безопасная отправка уведомлений администраторам
"""

import logging
from aiogram.utils.exceptions import CantInitiateConversation, BotBlocked, UserDeactivated
from data.config import ADMINS


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
