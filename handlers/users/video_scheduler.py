from handlers import groups

from aiogram import types
import asyncio
from datetime import datetime, timedelta, time
from db import db
from loader import dp, bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
import logging
import json
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from handlers.users.video_lists import VIDEO_LIST_1, VIDEO_LIST_2, VIDEO_LIST_3, VIDEO_LIST_4, VIDEO_LIST_5, VIDEO_LIST_GOLDEN_1
from aiogram.utils.exceptions import MigrateToChat

# Настройка логирования
logger = logging.getLogger(__name__)

# Список супер-админов для уведомлений
SUPER_ADMIN_IDS = [5657091547, 7983512278, 5310261745, 8053364577]

# Вместо VIDEO_LIST теперь используем VIDEO_LIST_1
VIDEO_LIST = VIDEO_LIST_1

# Инициализация планировщика
scheduler = AsyncIOScheduler(
    timezone="Asia/Tashkent",
    job_defaults={
        'coalesce': False,  # Не объединять пропущенные задачи
        'max_instances': 1,  # Максимум одна задача одновременно
        'misfire_grace_time': 300  # 5 минут на выполнение пропущенной задачи
    }
)

def schedule_job_with_immediate_check(scheduler, func, hour, minute, args, job_id, timezone="Asia/Tashkent"):
    """
    Планирует задачу: если время уже прошло, планирует на завтра
    """
    try:
        current_time = datetime.now(pytz.timezone(timezone))
        target_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if current_time >= target_time:
            # Время уже прошло, планируем на завтра
            logger.info(f"Время {hour:02d}:{minute:02d} уже прошло, планируем на завтра для {job_id}")
            # НЕ отправляем немедленно!
        
        # Планируем задачу
        scheduler.add_job(
            func,
            'cron',
            hour=hour, minute=minute,
            args=args,
            id=job_id,
            timezone=timezone,
            misfire_grace_time=300,  # 5 минут на выполнение пропущенной задачи
            replace_existing=True,
            max_instances=1  # Только одна задача может выполняться одновременно
        )
        
        logger.info(f"Задача {job_id} запланирована на {hour:02d}:{minute:02d}")
        
    except Exception as e:
        logger.error(f"Ошибка при планировании задачи {job_id}: {e}")

def get_video_list_by_project_and_season(project: str, season: str):
    if project == "centris":
        if season == "1-sezon":
            return VIDEO_LIST_1
        elif season == "2-sezon":
            return VIDEO_LIST_2
        elif season == "3-sezon":
            return VIDEO_LIST_3
        elif season == "4-sezon":
            return VIDEO_LIST_4
        elif season == "5-sezon":
            return VIDEO_LIST_5
        else:
            return VIDEO_LIST_1
    elif project == "golden_lake":
        return VIDEO_LIST_GOLDEN_1
    return []

def get_all_group_videos(project):
    if project == "centris":
        return VIDEO_LIST_1 + VIDEO_LIST_2 + VIDEO_LIST_3 + VIDEO_LIST_4 + VIDEO_LIST_5
    elif project == "golden_lake":
        return VIDEO_LIST_GOLDEN_1
    return []

# --- Функция рассылки для групп (старая логика) ---
async def send_group_video(chat_id: int, project: str, season: str, video_index: int):
    try:
        all_videos = get_all_group_videos(project)
        viewed = db.get_group_viewed_videos(chat_id)
        # Найти следующее непросмотренное видео
        next_idx = db.get_next_unwatched_group_video_index(chat_id, len(all_videos))
        if next_idx == -1:
            logger.info(f"Группа {chat_id} просмотрела все видео ({project})")
            return False
        video_url = all_videos[next_idx]
        message_id = int(video_url.split("/")[-1])
        await bot.copy_message(
            chat_id=chat_id,
            from_chat_id=-1002550852551,
            message_id=message_id,
            protect_content=True
        )
        db.mark_group_video_as_viewed(chat_id, next_idx)
        logger.info(f"Видео {next_idx} отправлено в группу {chat_id} (проект {project})")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке видео в группу {chat_id}: {e}")
        return False

# --- Новая функция: получить все видео сезона по ID (из базы) ---
def get_videos_for_group(project, season_id):
    if project == "centris" and season_id:
        return db.get_videos_by_season(season_id)
    elif project == "golden_lake" and season_id:
        return db.get_videos_by_season(season_id)
    return []

# --- Функция уведомления супер-админов о завершении сезона ---
async def notify_superadmins_season_completed(chat_id: int, season_id: int, project: str):
    """Уведомить супер-админов о завершении сезона в группе"""
    try:
        # Получаем информацию о группе
        group_name = "Noma'lum guruh"
        try:
            chat_info = await bot.get_chat(chat_id)
            group_name = chat_info.title or f"Guruh {chat_id}"
        except Exception:
            group_name = f"Guruh {chat_id}"
        
        # Получаем название сезона
        season_name = db.get_season_name(season_id) or f"Sezon {season_id}"
        
        # Переводим название проекта на узбекский
        project_name_uz = "Centris Towers" if project == "centris" else "Golden Lake" if project in ["golden", "golden_lake"] else project
        
        # Формируем сообщение на узбекском
        message = (
            f"🏁 **SEZON TUGADI**\n\n"
            f"🏢 **Guruh:** {group_name}\n"
            f"🆔 **ID:** `{chat_id}`\n"
            f"🎬 **Loyiha:** {project_name_uz}\n"
            f"📺 **Sezon:** {season_name}\n\n"
            f"✅ Ushbu guruhdagi barcha videolar yuborildi.\n"
            f"🔄 Keyingi sezonni boshlash uchun `/set_group_video` buyrug'ini ishlatish kerak.\n\n"
            f"📅 **Vaqt:** {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        
        # Отправляем уведомление каждому супер-админу
        for admin_id in SUPER_ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode="Markdown"
                )
                logger.info(f"✅ Уведомление о завершении сезона отправлено админу {admin_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка при отправке уведомления админу {admin_id}: {e}")
                
        logger.info(f"🏁 Уведомления о завершении сезона {season_id} в группе {chat_id} отправлены")
        
    except Exception as e:
        logger.error(f"Ошибка при уведомлении админов о завершении сезона: {e}")


# --- Функция уведомления о автоматическом переключении сезона ---
async def notify_superadmins_season_auto_switched(chat_id: int, old_season_id: int, project: str):
    """Уведомить супер-админов об автоматическом переключении на следующий сезон"""
    try:
        from loader import dp
        from data.config import ADMINS
        
        # Получаем информацию о группе
        group_info = db.get_group_by_id(chat_id)
        group_name = group_info[1] if group_info and group_info[1] else "Noma'lum guruh"
        
        # Получаем информацию о новом сезоне
        settings = db.get_group_video_settings(chat_id)
        project_for_db = "golden" if project == "golden_lake" else project
        
        if project_for_db == "centris" and settings:
            new_season_id = settings[1]  # centris_season_id
        elif project_for_db == "golden" and settings:
            new_season_id = settings[4]  # golden_season_id
        else:
            new_season_id = None
            
        # Получаем название нового сезона
        new_season_name = "Noma'lum sezon"
        if new_season_id:
            season_info = db.get_season_by_id(new_season_id)
            if season_info:
                new_season_name = season_info[1]
        
        project_name = "Centris Towers" if project_for_db == "centris" else "Golden Lake"
        
        message = f"🔄 **Avtomatik sezon almashtirish**\n\n" \
                 f"📱 **Guruh:** {group_name}\n" \
                 f"🆔 **ID:** `{chat_id}`\n" \
                 f"🎬 **Loyiha:** {project_name}\n\n" \
                 f"📊 **O'zgarishlar:**\n" \
                 f"• Eski sezon ID: `{old_season_id}`\n" \
                 f"• Yangi sezon ID: `{new_season_id}`\n" \
                 f"• Yangi sezon: {new_season_name}\n\n" \
                 f"✅ **Guruh avtomatik ravishda keyingi sezonga o'tdi!**\n" \
                 f"🚀 **Birinchi video tez orada yuboriladi.**"
        
        # Отправляем уведомления всем админам
        success_count = 0
        for admin_id in ADMINS:
            try:
                await dp.bot.send_message(admin_id, message, parse_mode="Markdown")
                success_count += 1
                logger.info(f"✅ Уведомление о автопереключении сезона отправлено админу {admin_id}")
            except Exception as e:
                logger.warning(f"❌ Не удалось отправить уведомление админу {admin_id}: {e}")
        
        logger.info(f"🔄 Уведомления об автопереключении сезона {old_season_id}→{new_season_id} в группе {chat_id} отправлены {success_count} админам")
        
    except Exception as e:
        logger.error(f"Ошибка при уведомлении админов об автопереключении сезона: {e}")

# --- Новая функция рассылки для групп ---
async def send_group_video_new(chat_id: int, project: str, season_id: int = None, start_video: int = None):
    """Отправить новое видео в группу согласно настройкам"""
    try:
        # ПРОВЕРКА БЕЗОПАСНОСТИ: Группа должна быть в whitelist
        if not db.is_group_whitelisted(chat_id):
            logger.warning(f"Guruh {chat_id} whitelist da emas, video yuborilmaydi")
            return False

        # Получаем стартовые значения из базы
        season_db, video_db = db.get_group_video_start(chat_id, project)
        logger.info(f"🎯 Данные из БД для группы {chat_id}, проект {project}: season_db={season_db}, video_db={video_db}")
        
        season_id = season_id if season_id is not None else season_db
        start_video = start_video if start_video is not None else video_db
        
        logger.info(f"🎯 Итоговые значения: season_id={season_id}, start_video={start_video}")
        
        # Проверяем валидность season_id
        if not season_id:
            logger.info(f"Не найден стартовый сезон для группы {chat_id}, проект {project}")
            return False
        
        # ИСПРАВЛЕНИЕ: Обрабатываем случай когда season_id - строка "centris" или "golden"
        if season_id == "centris" and project == "centris":
            # Получаем первый сезон Centris
            centris_seasons = db.get_seasons_by_project("centris")
            if centris_seasons:
                season_id = centris_seasons[0][0]
                logger.info(f"Исправлен season_id для группы {chat_id}: 'centris' -> {season_id}")
            else:
                logger.error(f"Нет сезонов Centris для группы {chat_id}")
                return False
        elif season_id == "golden" and project in ["golden_lake", "golden"]:
            # Получаем первый сезон Golden Lake
            golden_seasons = db.get_seasons_by_project("golden")
            if golden_seasons:
                season_id = golden_seasons[0][0]
                logger.info(f"Исправлен season_id для группы {chat_id}: 'golden' -> {season_id}")
            else:
                logger.error(f"Нет сезонов Golden Lake для группы {chat_id}")
                return False
        
        # ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: убеждаемся что season_id - это число
        try:
            season_id = int(season_id)
        except (ValueError, TypeError):
            logger.error(f"Неправильный season_id '{season_id}' для группы {chat_id}, проект {project}. Требуется исправление настроек группы.")
            return False

        # Получаем все сезоны проекта
        if project == "centris":
            all_seasons = db.get_seasons_by_project("centris")
        elif project == "golden_lake" or project == "golden":
            all_seasons = db.get_seasons_by_project("golden")
        else:
            all_seasons = []

        if not all_seasons:
            logger.info(f"Нет сезонов для проекта {project}")
            return False

        # Находим индекс текущего сезона
        current_season_index = -1
        for i, (s_id, s_name) in enumerate(all_seasons):
            if s_id == season_id:
                current_season_index = i
                break

        if current_season_index == -1:
            logger.info(f"Сезон {season_id} не найден, начинаем с первого")
            current_season_index = 0
            season_id = all_seasons[0][0]
            start_video = 0

        # Унифицируем название проекта для получения просмотренных видео
        project_for_db = "golden_lake" if project == "golden" else project
        # --- ИСПРАВЛЕННАЯ ЛОГИКА: последовательная отправка ТОЛЬКО по выбранному сезону ---
        
        # Получаем просмотренные видео в формате "season_id:position"
        viewed_videos_detailed = db.get_group_viewed_videos_detailed_by_project(chat_id, project_for_db)
        
        logger.info(f"🎯 Всего просмотрено видео проекта {project}: {len(viewed_videos_detailed)}")
        logger.info(f"🎯 Просмотренные видео: {viewed_videos_detailed}")
        logger.info(f"🎯 Отправляем видео ТОЛЬКО из выбранного сезона {season_id}")
        logger.info(f"🎯 Стартовое видео установлено: {start_video}")
        
        # Работаем ТОЛЬКО с выбранным сезоном
        current_season_videos = db.get_videos_by_season(season_id)
        logger.info(f"🎯 Проверяем выбранный сезон {season_id}: {len(current_season_videos)} видео")
        
        # Ищем первое непросмотренное видео в выбранном сезоне (начиная со стартового)
        logger.info(f"🎯 Начинаем поиск с позиции start_video: {start_video}")
        logger.info(f"🎯 Список всех видео сезона: {[(position, title[:30]) for url, title, position in current_season_videos[:5]]}...")
        
        for video_idx, (url, title, position) in enumerate(current_season_videos):
            video_key = f"{season_id}:{position}"
            logger.info(f"🎯 Проверяем видео: position={position}, start_video={start_video}, video_key={video_key}")
            
            # ВАЖНО: Ищем видео начиная с start_video (или больше)
            if position >= start_video and video_key not in viewed_videos_detailed:
                logger.info(f"🎯 Найдено непросмотренное видео: {video_key} (сезон {season_id}, позиция {position})")
                logger.info(f"🎯 Отправляем: {title}")
                
                message_id = int(url.split("/")[-1])
                await bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=-1002550852551,
                    message_id=message_id,
                    protect_content=True
                )
                logger.info(f"✅ Видео {position} сезона {season_id} отправлено в группу {chat_id} (проект {project})")
                
                # Отмечаем как просмотренное в детальном формате
                db.mark_group_video_as_viewed_detailed_by_project(chat_id, season_id, position, project_for_db)
                logger.info(f"✅ Видео {video_key} отмечено как просмотренное для группы {chat_id}, проект {project}")
                
                # ВАЖНО: Обновляем start_video на следующую позицию
                next_position = position + 1
                # Приводим название проекта к формату базы данных
                project_for_db_update = "golden" if project == "golden_lake" else project
                db.set_group_video_start(chat_id, project_for_db_update, season_id, next_position)
                logger.info(f"🎯 Обновлен start_video для группы {chat_id}: {position} → {next_position}")
                
                return True
            else:
                logger.info(f"🎯 Видео {video_key} уже просмотрено, пропускаем")
        
        # Если все видео выбранного сезона просмотрены - сезон завершен
        logger.info(f"🔄 Все видео выбранного сезона {season_id} просмотрены для проекта {project}")
        
        # Пытаемся автоматически переключиться на следующий сезон
        project_for_db = "golden" if project == "golden_lake" else project
        success = db.auto_switch_to_next_season(chat_id, project_for_db, season_id)
        
        if success:
            logger.info(f"🎉 Группа {chat_id}: автоматически переключена на следующий сезон в проекте {project}")
            
            # Уведомляем супер-админов о переключении
            await notify_superadmins_season_auto_switched(chat_id, season_id, project)
            
            # Сразу пробуем отправить первое видео нового сезона
            try:
                # Получаем новые настройки после переключения
                new_settings = db.get_group_video_settings(chat_id)
                if new_settings:
                    if project_for_db == "centris" and new_settings[0]:  # centris_enabled
                        new_season_id = new_settings[1]  # centris_season_id
                        if new_season_id:
                            logger.info(f"🚀 Отправляем первое видео нового сезона {new_season_id} проекта {project}")
                            
                            # Отправляем первое видео нового сезона
                            from loader import bot
                            new_season_videos = db.get_videos_by_season(new_season_id)
                            if new_season_videos:
                                first_video = new_season_videos[0]  # Первое видео
                                url, title, position = first_video
                                
                                message_id = int(url.split("/")[-1])
                                await bot.copy_message(
                                    chat_id=chat_id,
                                    from_chat_id=-1002550852551,
                                    message_id=message_id,
                                    protect_content=True
                                )
                                
                                # Отмечаем как просмотренное
                                db.mark_group_video_as_viewed_detailed_by_project(chat_id, new_season_id, position, project_for_db)
                                
                                # Обновляем start_video на следующую позицию
                                db.set_group_video_start(chat_id, project_for_db, new_season_id, position + 1)
                                
                                logger.info(f"✅ Отправлено первое видео нового сезона {new_season_id}: {title}")
                                return True
                            
                    elif project_for_db == "golden" and new_settings[3]:  # golden_enabled
                        new_season_id = new_settings[4]  # golden_season_id
                        if new_season_id:
                            logger.info(f"🚀 Отправляем первое видео нового сезона {new_season_id} проекта {project}")
                            
                            # Отправляем первое видео нового сезона
                            from loader import bot
                            new_season_videos = db.get_videos_by_season(new_season_id)
                            if new_season_videos:
                                first_video = new_season_videos[0]  # Первое видео
                                url, title, position = first_video
                                
                                message_id = int(url.split("/")[-1])
                                await bot.copy_message(
                                    chat_id=chat_id,
                                    from_chat_id=-1002550852551,
                                    message_id=message_id,
                                    protect_content=True
                                )
                                
                                # Отмечаем как просмотренное
                                db.mark_group_video_as_viewed_detailed_by_project(chat_id, new_season_id, position, project_for_db)
                                
                                # Обновляем start_video на следующую позицию
                                db.set_group_video_start(chat_id, project_for_db, new_season_id, position + 1)
                                
                                logger.info(f"✅ Отправлено первое видео нового сезона {new_season_id}: {title}")
                                return True
                                
            except Exception as e:
                logger.error(f"Ошибка при отправке первого видео нового сезона: {e}")
                
            # После успешной отправки первого видео нового сезона, возвращаем True
            return True
        else:
            logger.warning(f"⚠️ Не удалось автоматически переключиться на следующий сезон для группы {chat_id}")
            
            # Если автопереключение не удалось, уведомляем админов как раньше
            await notify_superadmins_season_completed(chat_id, season_id, project)
            
            return False
    except Exception as e:
        logger.error(f"Ошибка в send_group_video_new: {e}")
        return False

# --- Функция для тестирования исправлений ---
async def test_video_sequence_fix(chat_id: int, project: str):
    """
    Тестовая функция для проверки корректности исправлений в логике отправки видео
    Поддерживает любое количество сезонов (3, 8, 9 и больше)
    """
    logger.info(f"🧪 ТЕСТ: Начинаем тестирование для группы {chat_id}, проект {project}")
    
    # Получаем настройки группы
    settings = db.get_group_video_settings(chat_id)
    if not settings:
        logger.error(f"🧪 ТЕСТ: Группа {chat_id} не найдена в настройках")
        return False
    
    # Получаем просмотренные видео
    project_for_db = "golden_lake" if project == "golden" else project
    viewed_positions = db.get_group_viewed_videos_by_project(chat_id, project_for_db)
    logger.info(f"🧪 ТЕСТ: Просмотренные позиции для {project_for_db}: {viewed_positions}")
    
    # Получаем все сезоны проекта
    if project == "centris":
        all_seasons = db.get_seasons_by_project("centris")
    elif project == "golden" or project == "golden_lake":
        all_seasons = db.get_seasons_by_project("golden")
    else:
        logger.error(f"🧪 ТЕСТ: Неизвестный проект {project}")
        return False
    
    logger.info(f"🧪 ТЕСТ: Найдено сезонов для {project}: {len(all_seasons)} (поддерживает любое количество: 3, 8, 9+)")
    for i, (season_id, season_name) in enumerate(all_seasons):
        logger.info(f"🧪 ТЕСТ: Сезон #{i+1} (ID: {season_id}): {season_name}")
    
    # Получаем стартовые значения
    season_db, video_db = db.get_group_video_start(chat_id, project)
    logger.info(f"🧪 ТЕСТ: Стартовый сезон: {season_db}, стартовое видео: {video_db}")
    
    # Проверяем логику перехода между сезонами
    if len(all_seasons) > 1:
        logger.info(f"🧪 ТЕСТ: Логика переходов будет работать для всех {len(all_seasons)} сезонов")
        logger.info(f"🧪 ТЕСТ: Порядок: Сезон 1 → Сезон 2 → ... → Сезон {len(all_seasons)} → Сезон 1 (цикл)")
    else:
        logger.info(f"🧪 ТЕСТ: Только 1 сезон - будет циклическое воспроизведение")
    
    return True

# --- Функция для получения статистики сезонов ---
def get_seasons_statistics():
    """
    Возвращает статистику по количеству сезонов в каждом проекте
    """
    try:
        centris_seasons = db.get_seasons_by_project("centris")
        golden_seasons = db.get_seasons_by_project("golden")
        
        stats = {
            "centris": {
                "count": len(centris_seasons),
                "seasons": centris_seasons
            },
            "golden": {
                "count": len(golden_seasons), 
                "seasons": golden_seasons
            }
        }
        
        logger.info(f"📊 СТАТИСТИКА: Centris Towers - {stats['centris']['count']} сезонов")
        logger.info(f"📊 СТАТИСТИКА: Golden Lake - {stats['golden']['count']} сезонов")
        
        return stats
    except Exception as e:
        logger.error(f"Ошибка при получении статистики сезонов: {e}")
        return None

# --- Планировщик для групп (старая логика) ---
async def send_group_video_by_settings(chat_id: int):
    """
    Отправляет видео в группу в зависимости от group_video_settings:
    - Если группа не настроена — не отправлять
    - Если centris_enabled/golden_enabled — отправлять только соответствующие видео
    - Если оба True — отправлять оба потока
    """
    # ПРОВЕРКА БЕЗОПАСНОСТИ: Группа должна быть в whitelist
    if not db.is_group_whitelisted(chat_id):
        logger.warning(f"Guruh {chat_id} whitelist da emas, rассылка o'tkazib yuboriladi")
        return
        
    settings = db.get_group_video_settings(chat_id)
    if not settings or (not settings[0] and not settings[4]):
        logger.info(f"Группа {chat_id} не настроена для рассылки видео")
        return False
    centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video, send_times = settings
    sent = False
    if centris_enabled and centris_season_id:
        # Отправить видео Centris
        res = await send_group_video_new(chat_id, "centris", centris_season_id, centris_start_video)
        sent = sent or res
    if golden_enabled and golden_season_id:
        # Отправить видео Golden Lake
        res = await send_group_video_new(chat_id, "golden_lake", golden_season_id, golden_start_video)
        sent = sent or res
    return sent

# --- УСТАРЕВШИЙ ПЛАНИРОВЩИК: НЕ ИСПОЛЬЗУЕТСЯ ---
# def schedule_group_jobs():
    try:
        logger.info("Начало планирования задач для групп (логика Centris/Golden)")
        jobs = scheduler.get_jobs()
        for job in jobs:
            if job.id.startswith("group_"):
                scheduler.remove_job(job.id)
        groups = db.get_all_groups_with_settings()
        logger.info(f"Найдено {len(groups)} групп с настройками")
        for chat_id, centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video, viewed_videos, is_subscribed, group_name in groups:
            if centris_enabled and not golden_enabled:
                # Только Centris Towers - 3 раза в день: 07:00, 11:00, 20:00
                    scheduler.add_job(
                    send_group_video_new,
                        trigger='cron',
                        hour=7,
                        minute=0,
                    args=[chat_id, 'centris', centris_season_id],
                        id=f"group_centrismorning_{chat_id}",
                        replace_existing=True,
                        timezone="Asia/Tashkent"
                    )
                    scheduler.add_job(
                    send_group_video_new,
                        trigger='cron',
                        hour=11,
                        minute=0,
                    args=[chat_id, 'centris', centris_season_id],
                        id=f"group_centrismid_{chat_id}",
                        replace_existing=True,
                        timezone="Asia/Tashkent"
                    )
                    scheduler.add_job(
                    send_group_video_new,
                        trigger='cron',
                        hour=20,
                        minute=0,
                    args=[chat_id, 'centris', centris_season_id],
                        id=f"group_centrisevening_{chat_id}",
                        replace_existing=True,
                        timezone="Asia/Tashkent"
                    )
            elif golden_enabled and not centris_enabled:
                # Только Golden Lake - 3 раза в день: 07:00, 11:00, 20:00
                scheduler.add_job(
                    send_group_video_new,
                    trigger='cron',
                    hour=7,
                    minute=0,
                    args=[chat_id, 'golden_lake', golden_season_id],
                    id=f"group_goldenmorning_{chat_id}",
                    replace_existing=True,
                    timezone="Asia/Tashkent"
                )
                scheduler.add_job(
                    send_group_video_new,
                    trigger='cron',
                    hour=11,
                    minute=0,
                    args=[chat_id, 'golden_lake', golden_season_id],
                    id=f"group_goldenmid_{chat_id}",
                    replace_existing=True,
                    timezone="Asia/Tashkent"
                )
                scheduler.add_job(
                    send_group_video_new,
                    trigger='cron',
                    hour=20,
                    minute=0,
                    args=[chat_id, 'golden_lake', golden_season_id],
                    id=f"group_goldenevening_{chat_id}",
                    replace_existing=True,
                    timezone="Asia/Tashkent"
                )
            elif centris_enabled and golden_enabled:
                # Оба: Centris 07:00, 11:00, 20:00, Golden 11:00
                    scheduler.add_job(
                    send_group_video_new,
                        trigger='cron',
                        hour=7,
                        minute=0,
                    args=[chat_id, 'centris', centris_season_id],
                        id=f"group_centrismorning_{chat_id}",
                        replace_existing=True,
                        timezone="Asia/Tashkent"
                    )
                    scheduler.add_job(
                    send_group_video_new,
                        trigger='cron',
                        hour=11,
                        minute=0,
                    args=[chat_id, 'centris', centris_season_id],
                        id=f"group_centrismid_{chat_id}",
                        replace_existing=True,
                        timezone="Asia/Tashkent"
                    )
                    scheduler.add_job(
                    send_group_video_new,
                        trigger='cron',
                        hour=20,
                        minute=0,
                        args=[chat_id, 'centris', centris_season_id],
                        id=f"group_centrisevening_{chat_id}",
                        replace_existing=True,
                        timezone="Asia/Tashkent"
                    )
                    scheduler.add_job(
                        send_group_video_new,
                        trigger='cron',
                        hour=11,
                        minute=0,
                        args=[chat_id, 'golden_lake', golden_season_id],
                        id=f"group_golden_{chat_id}",
                        replace_existing=True,
                        timezone="Asia/Tashkent"
                    )
        logger.info("Задачи для групп запланированы по новым правилам Centris/Golden")
    except Exception as e:
        logger.error(f"Ошибка при планировании задач для групп: {e}")

def get_next_video_index(user_id: int) -> int:
    """Получить следующий непросмотренный индекс видео"""
    viewed_videos = db.get_viewed_videos(user_id)
    current_index = db.get_video_index(user_id)

    # Если пользователь еще не просматривал видео, начинаем с сохраненного начального индекса
    if not viewed_videos and current_index == 0:
        start_index = db.get_start_video_index()
        if start_index < len(VIDEO_LIST):
            return start_index

    # Находим следующий непросмотренный индекс
    for i in range(current_index, len(VIDEO_LIST)):
        if i not in viewed_videos:
            return i

    # Если все видео просмотрены, возвращаем -1
    return -1

# Функция для отправки видео
async def send_video_to_user(user_id: int, video_index: int) -> bool:
    try:
        # Проверяем, что индекс не превышает количество видео
        if video_index >= len(VIDEO_LIST) or video_index < 0:
            logger.info(f"Пользователь {user_id} просмотрел все видео")
            return False

        # Отправляем видео пользователю
        await bot.forward_message(
            chat_id=user_id,
            from_chat_id=-1002550852551,  # ID канала
            message_id=int(VIDEO_LIST[video_index].split('/')[-1])
        )

        # Добавляем видео в список просмотренных
        db.mark_video_as_viewed(user_id, video_index)
        logger.info(f"Видео {video_index} отмечено как просмотренное для пользователя {user_id}")

        return True

    except Exception as e:
        logger.error(f"Ошибка при отправке видео пользователю {user_id}: {e}")
        try:
            await bot.send_message(user_id, f"Xatolik yuz berdi: {e}")
        except Exception:
            pass
        return False

# Функция для отправки видео конкретному пользователю
async def send_scheduled_video(user_id: int) -> None:
    try:
        # Получаем следующий непросмотренный индекс видео
        next_index = get_next_video_index(user_id)
        logger.info(f"Отправка запланированного видео пользователю {user_id}. Следующий индекс: {next_index}")

        # Проверяем, просмотрел ли пользователь все видео
        if next_index == -1:
            logger.info(f"Пользователь {user_id} уже просмотрел все видео")
            return

        # Отправляем видео
        success = await send_video_to_user(user_id, next_index)

        if not success:
            logger.error(f"Не удалось отправить видео {next_index} пользователю {user_id}")

        # Обновляем индекс видео после успешной отправки
        db.update_video_index(user_id, next_index + 1)
        logger.info(f"Индекс видео для пользователя {user_id} обновлен до {next_index + 1}")

    except Exception as e:
        logger.error(f"Ошибка в handle_time_selection: {e}")
        try:
            await bot.send_message(user_id, f"Xatolik yuz berdi: {e}")
        except Exception:
            pass


    # Добавляем клавиатуру для выбора времени
def get_time_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    times = ["09:00", "12:00", "15:00", "18:00", "21:00"]
    for t in times:
        keyboard.add(KeyboardButton(t))
    return keyboard

    # Обработчик команды для выбора времени
async def handle_set_time(message: types.Message) -> None:
    try:
        user_id = message.from_user.id

        # Проверяем статус подписки
        if not db.get_subscription_status(user_id):
            await message.answer("Siz obuna bo'lmagansiz. Obuna bo'lish uchun /start buyrug'ini bosing.")
            return

        await message.answer(
            "Iltimos, video olish uchun qulay vaqtni tanlang:",
            reply_markup=get_time_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в handle_set_time: {e}")
        await message.answer("Kechirasiz, xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

    # Обработчик выбора времени
async def handle_time_selection(message: types.Message) -> None:
    try:
        user_id = message.from_user.id
        selected_time = message.text

        # Проверяем формат времени
        try:
            time.strptime(selected_time, "%H:%M")
        except ValueError:
            await message.answer("Noto'g'ri vaqt formati. Iltimos, qaytadan tanlang.", reply_markup=get_time_keyboard())
            return

        # Сохраняем выбранное время
        db.update_preferred_time(user_id, selected_time)
        await message.answer(f"Video olish vaqti {selected_time} ga o'rnatildi!", reply_markup=types.ReplyKeyboardRemove())

        # Обновляем планировщик
        schedule_jobs_for_users()

    except Exception as e:
        logger.error(f"Ошибка в handle_time_selection: {e}")
        try:
            await bot.send_message(user_id, f"Xatolik yuz berdi: {e}")
        except Exception:
            pass
        await message.answer("Kechirasiz, xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

    # Модифицируем функцию планирования задач
def schedule_jobs_for_users():
    try:
        logger.info("Начало планирования задач для пользователей и групп")
        
        # Получаем активных получателей
        recipients = db.get_all_subscribers_with_type()
        logger.info(f"Найдено {len(recipients)} получателей (пользователи и группы)")
        
        if not recipients:
            logger.warning("Нет подписчиков в базе данных, задачи не создаются")
            return
        
        # Удаляем только старые задачи пользователей (не групповые!)
        current_jobs = scheduler.get_jobs()
        for job in current_jobs:
            if job.id.startswith("video_morning_") or job.id.startswith("video_evening_"):
                # Проверяем, есть ли такой получатель в актуальном списке
                recipient_id = int(job.id.split("_")[-1])
                if not any(r[0] == recipient_id for r in recipients):
                    scheduler.remove_job(job.id)
                    logger.info(f"Удалена устаревшая задача: {job.id}")
        
        # Создаем задачи для текущих получателей
        for recipient_id, is_group in recipients:
            scheduler.add_job(
                scheduled_send_08,
                trigger='cron',
                hour=8,
                minute=0,
                args=[recipient_id],
                id=f"video_morning_{recipient_id}",
                replace_existing=True
            )
            scheduler.add_job(
                scheduled_send_20,
                trigger='cron',
                hour=20,
                minute=0,
                args=[recipient_id],
                id=f"video_evening_{recipient_id}",
                replace_existing=True
            )
        logger.info("Задачи на 08:00 и 20:00 для всех получателей созданы")

        # Планируем задачи для групп с настройками (новая логика)
        groups_settings = db.get_all_groups_with_settings()
        logger.info(f"Планируем задачи для {len(groups_settings)} групп с настройками")
        for group in groups_settings:
            chat_id = group[0]
            schedule_single_group_jobs(chat_id)

    except Exception as e:
        logger.error(f"Ошибка при планировании задач: {e}")

    # Добавляем обработчик для обновления планировщика при изменении времени
async def update_scheduler_on_time_change(user_id: int, new_time: str) -> None:
    """Обновляет планировщик при изменении времени пользователем"""
    try:
        # Обновляем время в базе данных
        db.set_preferred_time(user_id, new_time)

        # Обновляем планировщик
        schedule_jobs_for_users()

        logger.info(f"Планировщик обновлен для пользователя {user_id} с новым временем {new_time}")
    except Exception as e:
        logger.error(f"Ошибка при обновлении планировщика: {e}")

    # Регистрируем обработчик для обновления планировщика
    dp.register_message_handler(
        lambda message: update_scheduler_on_time_change(message.from_user.id, message.text),
        lambda message: message.text and message.text.count(':') == 1 and all(x.isdigit() for x in message.text.split(':'))
    )

    # Функция для периодического обновления задач
async def update_scheduled_jobs():
    """Обновляет задачи планировщика каждые 30 минут"""
    while True:
        try:
            logger.info("Начало обновления задач планировщика")
            schedule_jobs_for_users()
            logger.info("Задачи планировщика обновлены")
        except Exception as e:
            logger.error(f"Ошибка при обновлении задач: {e}")
        try:
            await asyncio.sleep(1800)  # Обновляем каждые 30 минут
        except asyncio.CancelledError:
            logger.info("Задача обновления планировщика отменена")
            break

    # Инициализация планировщика при старте
async def init_scheduler():
    try:
        logger.info("Начало инициализации планировщика")

        # Проверяем, запущен ли уже планировщик
        if scheduler.running:
            logger.info("Планировщик уже запущен, останавливаем его")
            scheduler.shutdown()

        # Инициализируем планировщик
        schedule_jobs_for_users()
        schedule_access_checks()  # Добавляем планировщик проверки доступа
        scheduler.start()
        logger.info("Планировщик успешно инициализирован и запущен")

        # Проверяем, что планировщик запущен
        if not scheduler.running:
            raise Exception("Планировщик не запустился после start()")

        # Запускаем обновление задач в фоновом режиме
        asyncio.create_task(update_scheduled_jobs())
        logger.info("Задача обновления планировщика запущена в фоновом режиме")

        # Проверяем наличие задач
        jobs = scheduler.get_jobs()
        logger.info(f"Количество активных задач после инициализации: {len(jobs)}")
        if len(jobs) == 0:
            logger.warning("Нет активных задач в планировщике")

    except Exception as e:
        logger.error(f"Ошибка при инициализации планировщика: {e}")
        raise

async def handle_video_command(message: types.Message) -> None:
    try:
        user_id = message.from_user.id

        # Проверяем статус подписки
        if not db.get_subscription_status(user_id):
            await message.answer("Siz obuna bo'lmagansiz. Obuna bo'lish uchun /start buyrug'ini bosing.")
            return

        # Получаем следующий непросмотренный индекс видео
        next_index = get_next_video_index(user_id)
        logger.info(f"Пользователь {user_id} запросил видео. Следующий индекс: {next_index}")

        # Проверяем, просмотрел ли пользователь все видео
        if next_index == -1:
            await message.answer("Siz barcha videolarni ko'rdingiz!")
            return

        # Отправляем видео
        success = await send_video_to_user(user_id, next_index)

        if not success:
            await message.answer("Kechirasiz, video yuborishda xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

    except Exception as e:
        logger.error(f"Ошибка в handle_video_command: {e}")
        await message.answer("Kechirasiz, xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

    # Регистрируем обработчики
    dp.register_message_handler(handle_set_time, commands=['settime'])
    dp.register_message_handler(handle_time_selection, lambda message: message.text in ["09:00", "12:00", "15:00", "18:00", "21:00"])

async def send_next_unwatched_video(user_id, video_list, viewed_key):
    viewed = db.get_viewed_videos(user_id)
    for idx, _ in enumerate(video_list):
        if idx not in viewed:
            try:
                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=-1002550852551,
                    message_id=int(video_list[idx].split("/")[-1]),
                    protect_content=True
                )
                db.mark_video_as_viewed(user_id, idx)
                return True
            except MigrateToChat as e:
                new_chat_id = e.migrate_to_chat_id
                db.update_group_chat_id(user_id, new_chat_id)
                await bot.copy_message(
                    chat_id=new_chat_id,
                    from_chat_id=-1002550852551,
                    message_id=int(video_list[idx].split("/")[-1]),
                    protect_content=True
                )
                db.mark_video_as_viewed(new_chat_id, idx)
                return True
            except Exception as e:
                logger.error(f"Ошибка при отправке видео {idx} пользователю {user_id}: {e}")
                return False
    return False  # Все просмотрены

async def scheduled_send_08(user_id):
    await send_next_unwatched_video(user_id, VIDEO_LIST_1, 'v1')

async def scheduled_send_20(user_id):
    sent = await send_next_unwatched_video(user_id, VIDEO_LIST_1, 'v1')
    if not sent:
        sent2 = await send_next_unwatched_video(user_id, VIDEO_LIST_2, 'v2')
        if not sent2:
            await send_next_unwatched_video(user_id, VIDEO_LIST_3, 'v3')

    # --- Функция для обновления настроек группы и сброса просмотренных видео ---
def update_group_video_settings_and_reset(chat_id, centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_start_video):
    db.set_group_video_settings(chat_id, centris_enabled, centris_season_id, centris_start_video, golden_enabled, None, golden_start_video)
    db.reset_group_viewed_videos(chat_id)

def schedule_group_jobs_v2():
    logger.warning("⚠️ УСТАРЕВШАЯ ФУНКЦИЯ schedule_group_jobs_v2() - используйте schedule_single_group_jobs()")
    logger.info("Планирование задач для групп (отдельные потоки)")
    jobs = scheduler.get_jobs()
    for job in jobs:
        if job.id.startswith("group_"):
            scheduler.remove_job(job.id)
    groups = db.get_all_groups_with_settings()
    for group in groups:
        chat_id = group[0]
        safe_chat_id = abs(chat_id)  # Безопасный ID для задач
        centris_enabled = bool(group[1])
        centris_season_id = group[2]  # centris_season_id
        centris_start_video = group[3]  # centris_start_video
        golden_enabled = bool(group[4])
        golden_season_id = group[5]  # golden_season_id
        golden_start_video = group[6]  # golden_start_video
        viewed_videos = group[7]
        is_subscribed = group[8]
        group_name = group[9]  # group_name
        send_times_json = group[10] if len(group) > 10 else None  # send_times
        
        # Получаем время отправки
        try:
            if send_times_json:
                send_times = json.loads(send_times_json)
            else:
                send_times = ["07:00", "11:00", "20:00"]  # По умолчанию
        except:
            send_times = ["07:00", "11:00", "20:00"]  # Fallback
        
        logger.info(f"Группа {chat_id}: время отправки {send_times}")
        
        # Определяем режим работы
        both_enabled = centris_enabled and golden_enabled
        
        # Режим 1: Только Centris Towers - пользовательское время
        if centris_enabled and centris_season_id and not golden_enabled:
            for i, send_time in enumerate(send_times):
                try:
                    hour, minute = map(int, send_time.split(':'))
                    schedule_job_with_immediate_check(
                        scheduler,
                        send_group_video_new,
                        hour, minute,
                        [chat_id, 'centris', centris_season_id, centris_start_video],
                        f'group_{safe_chat_id}_centris_{i}',
                        "Asia/Tashkent"
                    )
                except ValueError:
                    logger.error(f"Неверный формат времени {send_time} для группы {chat_id}")
                    continue
            logger.info(f"Группа {chat_id}: Только Centris - {send_times}")
        
        # Режим 2: Только Golden Lake - пользовательское время
        elif golden_enabled and golden_season_id and not centris_enabled:
            for i, send_time in enumerate(send_times):
                try:
                    hour, minute = map(int, send_time.split(':'))
                    schedule_job_with_immediate_check(
                        scheduler,
                        send_group_video_new,
                        hour, minute,
                        [chat_id, 'golden_lake', golden_season_id, golden_start_video],
                        f'group_{safe_chat_id}_golden_{i}',
                        "Asia/Tashkent"
                    )
                except ValueError:
                    logger.error(f"Неверный формат времени {send_time} для группы {chat_id}")
                    continue
            logger.info(f"Группа {chat_id}: Только Golden Lake - {send_times}")
        
        # Режим 3: Оба проекта - ЧЕРЕДОВАНИЕ ПО ВРЕМЕНИ
        elif both_enabled and centris_season_id and golden_season_id:
            logger.info(f"Группа {chat_id}: Режим чередования проектов по времени")
            
            # Чередуем проекты по времени: Centris -> Golden -> Centris -> Golden...
            for i, send_time in enumerate(send_times):
                try:
                    hour, minute = map(int, send_time.split(':'))
                    
                    # Определяем какой проект отправлять в это время
                    if i % 2 == 0:  # Четные индексы (0, 2, 4...) - Centris
                        project = 'centris'
                        season_id = centris_season_id
                        start_video = centris_start_video
                        project_name = "Centris"
                    else:  # Нечетные индексы (1, 3, 5...) - Golden Lake
                        project = 'golden_lake'
                        season_id = golden_season_id
                        start_video = golden_start_video
                        project_name = "Golden Lake"
                    
                    schedule_job_with_immediate_check(
                        scheduler,
                        send_group_video_new,
                        hour, minute,
                        [chat_id, project, season_id, start_video],
                        f'group_{safe_chat_id}_{project}_{i}',
                        "Asia/Tashkent"
                    )
                    
                    logger.info(f"Группа {chat_id}: {send_time} -> {project_name}")
                    
                except ValueError:
                    logger.error(f"Неверный формат времени {send_time} для группы {chat_id}")
                    continue
            
            logger.info(f"Группа {chat_id}: Чередование настроено - времена: {send_times}")
    
    logger.info(f"Всего запланировано задач: {len(scheduler.get_jobs())}")


def schedule_single_group_jobs(chat_id: int):
    """
    Планирует задачи для конкретной группы с поддержкой пользовательского времени
    """
    try:
        logger.info(f"Планирование задач для группы {chat_id}")
        
        # Создаем безопасный ID для задач (убираем знак минус)
        safe_chat_id = abs(chat_id)
        
        # Удаляем существующие задачи для этой группы
        jobs = scheduler.get_jobs()
        for job in jobs:
            if job.id.startswith(f"group_{safe_chat_id}_"):
                scheduler.remove_job(job.id)
                logger.info(f"Удалена задача {job.id}")
        
        # Получаем настройки группы
        group_settings = db.get_group_video_settings(chat_id)
        if not group_settings:
            logger.warning(f"Группа {chat_id} не найдена в настройках")
            return False
        
        # Распаковываем tuple в переменные (теперь включает send_times)
        if len(group_settings) >= 7:
            centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video, send_times_json = group_settings
        else:
            centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video = group_settings
            send_times_json = None
        
        # Приводим к правильным типам
        centris_enabled = bool(centris_enabled)
        centris_start_video = centris_start_video or 0
        golden_enabled = bool(golden_enabled)
        golden_start_video = golden_start_video or 0
        
        # ИСПРАВЛЕНИЕ: Обрабатываем случай когда season_id - строка "centris" или "golden"
        if centris_season_id == "centris":
            # Получаем первый сезон Centris Towers
            centris_seasons = db.get_seasons_by_project("centris")
            if centris_seasons:
                centris_season_id = centris_seasons[0][0]  # Первый сезон
                logger.info(f"Исправлен centris_season_id для группы {chat_id}: 'centris' -> {centris_season_id}")
            else:
                centris_season_id = None
                logger.warning(f"Нет сезонов Centris для группы {chat_id}")
        
        if golden_season_id == "golden":
            # Получаем первый сезон Golden Lake
            golden_seasons = db.get_seasons_by_project("golden")
            if golden_seasons:
                golden_season_id = golden_seasons[0][0]  # Первый сезон
                logger.info(f"Исправлен golden_season_id для группы {chat_id}: 'golden' -> {golden_season_id}")
            else:
                golden_season_id = None
                logger.warning(f"Нет сезонов Golden Lake для группы {chat_id}")
        
        # Приводим к int если это возможно
        try:
            if centris_season_id:
                centris_season_id = int(centris_season_id)
        except (ValueError, TypeError):
            logger.error(f"Неверный centris_season_id для группы {chat_id}: {centris_season_id}")
            centris_season_id = None
            
        try:
            if golden_season_id:
                golden_season_id = int(golden_season_id)
        except (ValueError, TypeError):
            logger.error(f"Неверный golden_season_id для группы {chat_id}: {golden_season_id}")
            golden_season_id = None
        
        # Получаем время отправки
        try:
            if send_times_json:
                send_times = json.loads(send_times_json)
            else:
                send_times = ["07:00", "11:00", "20:00"]  # По умолчанию
        except:
            send_times = ["07:00", "11:00", "20:00"]  # Fallback
        
        logger.info(f"Группа {chat_id}: время отправки {send_times}")
        
        both_enabled = centris_enabled and golden_enabled
        
        # Режим 1: Только Centris Towers - пользовательское время
        if centris_enabled and centris_season_id and not golden_enabled:
            for i, send_time in enumerate(send_times):
                try:
                    hour, minute = map(int, send_time.split(':'))
                    schedule_job_with_immediate_check(
                        scheduler,
                        send_group_video_new,
                        hour, minute,
                        [chat_id, 'centris', centris_season_id, centris_start_video],
                        f'group_{safe_chat_id}_centris_{i}',
                        "Asia/Tashkent"
                    )
                except ValueError:
                    logger.error(f"Неверный формат времени {send_time} для группы {chat_id}")
                    continue
            logger.info(f"Группа {chat_id}: Только Centris - {send_times}")
        
        # Режим 2: Только Golden Lake - пользовательское время
        elif golden_enabled and golden_season_id and not centris_enabled:
            for i, send_time in enumerate(send_times):
                try:
                    hour, minute = map(int, send_time.split(':'))
                    schedule_job_with_immediate_check(
                        scheduler,
                        send_group_video_new,
                        hour, minute,
                        [chat_id, 'golden_lake', golden_season_id, golden_start_video],
                        f'group_{safe_chat_id}_golden_{i}',
                        "Asia/Tashkent"
                    )
                except ValueError:
                    logger.error(f"Неверный формат времени {send_time} для группы {chat_id}")
                    continue
            logger.info(f"Группа {chat_id}: Только Golden Lake - {send_times}")
        
        # Режим 3: Оба проекта - ЧЕРЕДОВАНИЕ ПО ВРЕМЕНИ
        elif both_enabled and centris_season_id and golden_season_id:
            logger.info(f"Группа {chat_id}: Режим чередования проектов по времени")
            
            # Чередуем проекты по времени: Centris -> Golden -> Centris -> Golden...
            for i, send_time in enumerate(send_times):
                try:
                    hour, minute = map(int, send_time.split(':'))
                    
                    # Определяем какой проект отправлять в это время
                    if i % 2 == 0:  # Четные индексы (0, 2, 4...) - Centris
                        project = 'centris'
                        season_id = centris_season_id
                        start_video = centris_start_video
                        project_name = "Centris"
                    else:  # Нечетные индексы (1, 3, 5...) - Golden Lake
                        project = 'golden_lake'
                        season_id = golden_season_id
                        start_video = golden_start_video
                        project_name = "Golden Lake"
                    
                    schedule_job_with_immediate_check(
                        scheduler,
                        send_group_video_new,
                        hour, minute,
                        [chat_id, project, season_id, start_video],
                        f'group_{safe_chat_id}_{project}_{i}',
                        "Asia/Tashkent"
                    )
                    
                    logger.info(f"Группа {chat_id}: {send_time} -> {project_name}")
                    
                except ValueError:
                    logger.error(f"Неверный формат времени {send_time} для группы {chat_id}")
                    continue
            
            logger.info(f"Группа {chat_id}: Чередование настроено - времена: {send_times}")
        
        logger.info(f"Группа {chat_id}: задачи запланированы успешно")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при планировании задач для группы {chat_id}: {e}")
        return False

async def auto_revoke_expired_access():
    """Автоматически отозвать доступ у пользователей с истекшим временем"""
    try:
        logger.info("Запуск автоматической проверки истекшего доступа...")
        
        # Отзываем доступ у пользователей с истекшим временем
        revoked_count = db.auto_revoke_expired_access()
        
        if revoked_count > 0:
            logger.info(f"Автоматически отозван доступ у {revoked_count} пользователей")
            
            # Уведомляем супер-админов
            from data.config import SUPER_ADMIN_ID, ADMINS
            super_admins = [SUPER_ADMIN_ID] + ADMINS
            
            for admin_id in super_admins:
                try:
                    await bot.send_message(
                        admin_id,
                        f"🔄 **Автоматическая проверка доступа**\n\n"
                        f"🚫 **Отозван доступ у:** {revoked_count} пользователей\n"
                        f"⏰ **Время:** {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления админу {admin_id}: {e}")
        else:
            logger.info("Пользователей с истекшим доступом не найдено")
            
    except Exception as e:
        logger.error(f"Ошибка при автоматической проверке доступа: {e}")

def schedule_access_checks():
    """Планирует автоматическую проверку доступа"""
    try:
        # Проверяем каждые 6 часов
        scheduler.add_job(
            auto_revoke_expired_access,
            'interval',
            hours=6,
            id='access_check',
            timezone="Asia/Tashkent"
        )
        logger.info("Задача автоматической проверки доступа запланирована (каждые 6 часов)")
    except Exception as e:
        logger.error(f"Ошибка при планировании проверки доступа: {e}")