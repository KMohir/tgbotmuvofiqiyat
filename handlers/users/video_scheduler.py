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

# Вместо VIDEO_LIST теперь используем VIDEO_LIST_1
VIDEO_LIST = VIDEO_LIST_1

# Инициализация планировщика
scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

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
            misfire_grace_time=None
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
        season_id = season_id if season_id is not None else season_db
        start_video = start_video if start_video is not None else video_db
        if not season_id:
            logger.info(f"Не найден стартовый сезон для группы {chat_id}, проект {project}")
            return False

        # Получаем все сезоны проекта
        if project == "centris":
            all_seasons = db.get_seasons_by_project("centris")
        elif project == "golden_lake":
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

        # Получаем просмотренные видео для группы по проекту
        viewed_positions = db.get_group_viewed_videos_by_project(chat_id, project)
        logger.info(f"Просмотренные позиции для группы {chat_id}, проект {project}: {viewed_positions}")
        # Получаем список видео текущего сезона
        videos = db.get_videos_by_season(season_id)
        # --- Исправление: сначала отправляем именно стартовое видео, если оно не просмотрено ---
        if start_video not in viewed_positions:
            logger.info(f"Сначала отправляем стартовое видео {start_video} для группы {chat_id}")
            for url, title, position in videos:
                if position == start_video:
                    message_id = int(url.split("/")[-1])
                    await bot.copy_message(
                        chat_id=chat_id,
                        from_chat_id=-1002550852551,
                        message_id=message_id,
                        protect_content=True
                    )
                    logger.info(f"Стартовое видео {position} сезона {season_id} отправлено в группу {chat_id} (проект {project})")
                    db.mark_group_video_as_viewed_by_project(chat_id, position, project)
                    logger.info(f"Видео {position} отмечено как просмотренное для группы {chat_id}, проект {project}")
                    return True
            # Если вдруг стартовое видео не найдено — продолжаем обычную логику
        # --- Обычная логика: ищем первое непосмотренное видео начиная с season_start_video ---
        season_start_video = start_video if start_video > 0 else 0
        logger.info(f"Стартовая позиция для сезона {season_id}: {season_start_video}")
        for url, title, position in videos:
            logger.info(f"Проверяем видео позиция {position}, просмотрено: {position in viewed_positions}")
            if position < season_start_video:
                logger.info(f"Пропускаем позицию {position} (меньше стартовой {season_start_video})")
                continue
            if position not in viewed_positions:
                logger.info(f"Отправляем видео позиция {position}, title: {title}")
                message_id = int(url.split("/")[-1])
                await bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=-1002550852551,
                    message_id=message_id,
                    protect_content=True
                )
                logger.info(f"Видео {position} сезона {season_id} отправлено в группу {chat_id} (проект {project})")
                db.mark_group_video_as_viewed_by_project(chat_id, position, project)
                logger.info(f"Видео {position} отмечено как просмотренное для группы {chat_id}, проект {project}")
                return True
            else:
                logger.info(f"Видео позиция {position} уже просмотрено, пропускаем")
        
        # --- АВТОМАТИЧЕСКИЙ ПЕРЕХОД НА СЛЕДУЮЩИЙ СЕЗОН ---
        logger.info(f"Все видео сезона {season_id} просмотрены, пытаемся перейти на следующий сезон")
        
        # Находим следующий сезон
        next_season_index = current_season_index + 1
        if next_season_index < len(all_seasons):
            next_season_id = all_seasons[next_season_index][0]
            next_season_name = all_seasons[next_season_index][1]
            
            logger.info(f"Переходим на следующий сезон: {next_season_id} ({next_season_name})")
            
            # Обновляем настройки группы для следующего сезона
            if project == "centris":
                db.set_group_video_start(chat_id, 'centris', next_season_id, 0)
            elif project == "golden_lake":
                db.set_group_video_start(chat_id, 'golden', next_season_id, 0)
            
            # Пытаемся отправить первое видео из следующего сезона
            next_videos = db.get_videos_by_season(next_season_id)
            if next_videos:
                url, title, position = next_videos[0]  # Берем первое видео
                message_id = int(url.split("/")[-1])
                await bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=-1002550852551,
                    message_id=message_id,
                    protect_content=True
                )
                logger.info(f"Первое видео {position} нового сезона {next_season_id} отправлено в группу {chat_id} (проект {project})")
                db.mark_group_video_as_viewed_by_project(chat_id, position, project)
                
                # Обновляем планировщик для группы
                schedule_single_group_jobs(chat_id)
                
                return True
        
        logger.info(f"Нет новых видео для отправки во всех сезонах проекта {project}")
        return False
    except Exception as e:
        logger.error(f"Ошибка в send_group_video_new: {e}")
        return False

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
    centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video = settings
    sent = False
    if centris_enabled and centris_season_id:
        # Отправить видео Centris
        res = await send_group_video_new(chat_id, "centris", centris_season_id)
        sent = sent or res
    if golden_enabled and golden_season_id:
        # Golden Lake — всегда первый сезон (или из настроек)
        res = await send_group_video_new(chat_id, "golden_lake", golden_season_id)
        sent = sent or res
    return sent

# --- Планировщик для групп ---
def schedule_group_jobs():
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
        scheduler.remove_all_jobs()
        logger.info("Все существующие задачи удалены")
        recipients = db.get_all_subscribers_with_type()
        logger.info(f"Найдено {len(recipients)} получателей (пользователи и группы)")
        if not recipients:
            logger.warning("Нет подписчиков в базе данных, задачи не создаются")
            return
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
        schedule_group_jobs_v2()

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
    while True:
        try:
            logger.info("Начало обновления задач планировщика")
            schedule_jobs_for_users()
            logger.info("Задачи планировщика обновлены")
        except Exception as e:
            logger.error(f"Ошибка при обновлении задач: {e}")
        await asyncio.sleep(300)  # Обновляем каждые 5 минут

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
    logger.info("Планирование задач для групп (отдельные потоки)")
    jobs = scheduler.get_jobs()
    for job in jobs:
        if job.id.startswith("group_"):
            scheduler.remove_job(job.id)
    groups = db.get_all_groups_with_settings()
    for group in groups:
        chat_id = group[0]
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
                        f'group_{chat_id}_centris_{i}',
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
                        f'group_{chat_id}_golden_{i}',
                        "Asia/Tashkent"
                    )
                except ValueError:
                    logger.error(f"Неверный формат времени {send_time} для группы {chat_id}")
                    continue
            logger.info(f"Группа {chat_id}: Только Golden Lake - {send_times}")
        
        # Режим 3: Оба проекта - Centris по расписанию, Golden Lake между ними
        elif both_enabled and centris_season_id and golden_season_id:
            # Centris: пользовательское время
            for i, send_time in enumerate(send_times):
                try:
                    hour, minute = map(int, send_time.split(':'))
                    schedule_job_with_immediate_check(
                        scheduler,
                        send_group_video_new,
                        hour, minute,
                        [chat_id, 'centris', centris_season_id, centris_start_video],
                        f'group_{chat_id}_centris_{i}',
                        "Asia/Tashkent"
                    )
                except ValueError:
                    logger.error(f"Неверный формат времени {send_time} для группы {chat_id}")
                    continue
            
            # Golden Lake: в промежуточное время (например, между первыми двумя временами Centris)
            if len(send_times) >= 2:
                try:
                    first_hour = int(send_times[0].split(':')[0])
                    second_hour = int(send_times[1].split(':')[0])
                    golden_hour = (first_hour + second_hour) // 2
                    if golden_hour == first_hour:
                        golden_hour = first_hour + 3  # Добавляем 3 часа
                    schedule_job_with_immediate_check(
                        scheduler,
                        send_group_video_new,
                        golden_hour, 0,
                        [chat_id, 'golden_lake', golden_season_id, golden_start_video],
                        f'group_{chat_id}_golden_mid',
                        "Asia/Tashkent"
                    )
                except:
                    # Fallback: 11:00
                    schedule_job_with_immediate_check(
                        scheduler,
                        send_group_video_new,
                        11, 0,
                        [chat_id, 'golden_lake', golden_season_id, golden_start_video],
                        f'group_{chat_id}_golden_mid',
                        "Asia/Tashkent"
                    )
            else:
                # Если только одно время для Centris, Golden Lake в 11:00
                schedule_job_with_immediate_check(
                    scheduler,
                    send_group_video_new,
                    11, 0,
                    [chat_id, 'golden_lake', golden_season_id, golden_start_video],
                    f'group_{chat_id}_golden_mid',
                    "Asia/Tashkent"
                )
            logger.info(f"Группа {chat_id}: Оба проекта - Centris {send_times}, Golden промежуточное время")
    
    logger.info(f"Всего запланировано задач: {len(scheduler.get_jobs())}")


def schedule_single_group_jobs(chat_id: int):
    """
    Планирует задачи для конкретной группы с поддержкой пользовательского времени
    """
    try:
        logger.info(f"Планирование задач для группы {chat_id}")
        
        # Удаляем существующие задачи для этой группы
        jobs = scheduler.get_jobs()
        for job in jobs:
            if job.id.startswith(f"group_{chat_id}_"):
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
                        f'group_{chat_id}_centris_{i}',
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
                        f'group_{chat_id}_golden_{i}',
                        "Asia/Tashkent"
                    )
                except ValueError:
                    logger.error(f"Неверный формат времени {send_time} для группы {chat_id}")
                    continue
            logger.info(f"Группа {chat_id}: Только Golden Lake - {send_times}")
        
        # Режим 3: Оба проекта - Centris по расписанию, Golden Lake между ними
        elif both_enabled and centris_season_id and golden_season_id:
            # Centris: пользовательское время
            for i, send_time in enumerate(send_times):
                try:
                    hour, minute = map(int, send_time.split(':'))
                    schedule_job_with_immediate_check(
                        scheduler,
                        send_group_video_new,
                        hour, minute,
                        [chat_id, 'centris', centris_season_id, centris_start_video],
                        f'group_{chat_id}_centris_{i}',
                        "Asia/Tashkent"
                    )
                except ValueError:
                    logger.error(f"Неверный формат времени {send_time} для группы {chat_id}")
                    continue
            
            # Golden Lake: в промежуточное время
            if len(send_times) >= 2:
                try:
                    first_hour = int(send_times[0].split(':')[0])
                    second_hour = int(send_times[1].split(':')[0])
                    golden_hour = (first_hour + second_hour) // 2
                    if golden_hour == first_hour:
                        golden_hour = first_hour + 3  # Добавляем 3 часа
                    schedule_job_with_immediate_check(
                        scheduler,
                        send_group_video_new,
                        golden_hour, 0,
                        [chat_id, 'golden_lake', golden_season_id, golden_start_video],
                        f'group_{chat_id}_golden_mid',
                        "Asia/Tashkent"
                    )
                except:
                    # Fallback: 11:00
                    schedule_job_with_immediate_check(
                        scheduler,
                        send_group_video_new,
                        11, 0,
                        [chat_id, 'golden_lake', golden_season_id, golden_start_video],
                        f'group_{chat_id}_golden_mid',
                        "Asia/Tashkent"
                    )
            else:
                # Если только одно время для Centris, Golden Lake в 11:00
                schedule_job_with_immediate_check(
                    scheduler,
                    send_group_video_new,
                    11, 0,
                    [chat_id, 'golden_lake', golden_season_id, golden_start_video],
                    f'group_{chat_id}_golden_mid',
                    "Asia/Tashkent"
                )
            logger.info(f"Группа {chat_id}: Оба проекта - Centris {send_times}, Golden промежуточное время")
        
        logger.info(f"Группа {chat_id}: задачи запланированы успешно")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при планировании задач для группы {chat_id}: {e}")
        return False