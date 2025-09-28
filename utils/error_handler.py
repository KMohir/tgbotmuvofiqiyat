"""
Декоратор для автоматической обработки ошибок в хендлерах
"""

import logging
import traceback
from functools import wraps
from aiogram import Bot
from utils.safe_admin_notify import safe_send_error_notification

logger = logging.getLogger(__name__)


def error_handler(bot: Bot = None):
    """
    Декоратор для автоматической обработки ошибок в хендлерах
    
    Args:
        bot: Экземпляр бота для отправки уведомлений об ошибках
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Логируем ошибку
                error_msg = f"Ошибка в функции {func.__name__}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                
                # Получаем детали ошибки
                error_details = traceback.format_exc()
                
                # Отправляем уведомление об ошибке, если бот доступен
                if bot:
                    try:
                        await safe_send_error_notification(
                            bot=bot,
                            error_message=error_msg,
                            error_details=error_details[:1000]  # Ограничиваем размер деталей
                        )
                    except Exception as notify_error:
                        logger.error(f"Не удалось отправить уведомление об ошибке: {notify_error}")
                
                # Пытаемся отправить ответ пользователю, если это возможно
                try:
                    # Ищем объект message в аргументах
                    message = None
                    for arg in args:
                        if hasattr(arg, 'answer') and hasattr(arg, 'from_user'):
                            message = arg
                            break
                    
                    if message:
                        await message.answer(
                            "❌ Произошла ошибка при обработке вашего запроса. "
                            "Попробуйте позже или обратитесь к администратору."
                        )
                except Exception as reply_error:
                    logger.error(f"Не удалось отправить ответ пользователю: {reply_error}")
                
                # Не поднимаем исключение дальше, чтобы бот продолжал работать
                return None
        
        return wrapper
    return decorator


def error_handler_with_reply(bot: Bot = None, reply_text: str = None):
    """
    Декоратор для автоматической обработки ошибок с кастомным ответом пользователю
    
    Args:
        bot: Экземпляр бота для отправки уведомлений об ошибках
        reply_text: Текст ответа пользователю при ошибке
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Логируем ошибку
                error_msg = f"Ошибка в функции {func.__name__}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                
                # Получаем детали ошибки
                error_details = traceback.format_exc()
                
                # Отправляем уведомление об ошибке, если бот доступен
                if bot:
                    try:
                        await safe_send_error_notification(
                            bot=bot,
                            error_message=error_msg,
                            error_details=error_details[:1000]  # Ограничиваем размер деталей
                        )
                    except Exception as notify_error:
                        logger.error(f"Не удалось отправить уведомление об ошибке: {notify_error}")
                
                # Отправляем кастомный ответ пользователю
                try:
                    # Ищем объект message в аргументах
                    message = None
                    for arg in args:
                        if hasattr(arg, 'answer') and hasattr(arg, 'from_user'):
                            message = arg
                            break
                    
                    if message:
                        custom_reply = reply_text or "❌ Произошла ошибка при обработке вашего запроса. Попробуйте позже."
                        await message.answer(custom_reply)
                except Exception as reply_error:
                    logger.error(f"Не удалось отправить ответ пользователю: {reply_error}")
                
                # Не поднимаем исключение дальше, чтобы бот продолжал работать
                return None
        
        return wrapper
    return decorator
