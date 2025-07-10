from tgbotmuvofiqiyat.handlers import groups

from aiogram import types
import asyncio
from datetime import datetime, timedelta, time
from db import db
from loader import dp, bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
import logging
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from handlers.users.video_lists import VIDEO_LIST_1, VIDEO_LIST_2, VIDEO_LIST_3, VIDEO_LIST_4, VIDEO_LIST_5, VIDEO_LIST_GOLDEN_1
from aiogram.utils.exceptions import MigrateToChat

# Настройка логирования
logger = logging.getLogger(__name__)

# Вместо VIDEO_LIST теперь используем VIDEO_LIST_1
VIDEO_LIST = VIDEO_LIST_1

# Инициализация планировщика
scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

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
        if db.is_group_banned(chat_id):
            logger.info(f"Пропускаем отправку видео в заблокированную группу {chat_id}")
            return False
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
    try:
        if db.is_group_banned(chat_id):
            logger.error(f"Группа {chat_id} заблокирована, рассылка не производится")
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
            all_seasons = db.get_seasons_by_project("centr")
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

        # Получаем просмотренные видео для группы
        viewed_positions = db.get_group_viewed_videos(chat_id)
        logger.info(f"Просмотренные позиции для группы {chat_id}: {viewed_positions}")
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
                    db.mark_group_video_as_viewed(chat_id, position)
                    logger.info(f"Видео {position} отмечено как просмотренное для группы {chat_id}")
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
                db.mark_group_video_as_viewed(chat_id, position)
                logger.info(f"Видео {position} отмечено как просмотренное для группы {chat_id}")
                return True
            else:
                logger.info(f"Видео позиция {position} уже просмотрено, пропускаем")
        logger.info(f"Нет новых видео для отправки во всех сезонах проекта {project}")
        return False


# --- Планировщик для групп (старая логика) ---
async def send_group_video_by_settings(chat_id: int):
    """
    Отправляет видео в группу в зависимости от group_video_settings:
    - Если группа не настроена — не отправлять
    - Если centris_enabled/golden_enabled — отправлять только соответствующие видео
    - Если оба True — отправлять оба потока
    """
    settings = db.get_group_video_settings(chat_id)
    if not settings or (not settings[0] and not settings[2]):
        logger.info(f"Группа {chat_id} не настроена для рассылки видео")
        return False
    centris_enabled, centris_season_id, golden_enabled, golden_season_id = settings
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
        logger.info("Начало планирования задач для групп (старая логика)")
        jobs = scheduler.get_jobs()
        for job in jobs:
            if job.id.startswith("group_"):
                scheduler.remove_job(job.id)
        groups = db.get_all_groups_with_settings()
        logger.info(f"Найдено {len(groups)} групп с настройками")
        for chat_id, centris_enabled, centris_season_id, golden_enabled, golden_season_id in groups:
            # Если ни centris, ни golden не включены — не планируем
            if not centris_enabled and not golden_enabled:
                continue
            centris_season_name = None
            if centris_season_id:
                season_data = db.get_season_by_id(centris_season_id)
                if season_data:
                    centris_season_name = season_data[2]
            # Centris Towers
            if centris_enabled and centris_season_id:
                # 1-й сезон — 08:00 и 20:00
                if centris_season_name and (centris_season_name == "1-sezon" or centris_season_name == "Яқинлар 1.0 I I Иброҳим Мамасаидов"):
                    scheduler.add_job(
                        send_group_video_by_settings,
                        trigger='cron',
                        hour=8,
                        minute=0,
                        args=[chat_id],
                        id=f"group_centrismorning_{chat_id}",
                        replace_existing=True,
                        timezone="Asia/Tashkent"
                    )
                    scheduler.add_job(
                        send_group_video_by_settings,
                        trigger='cron',
                        hour=20,
                        minute=0,
                        args=[chat_id],
                        id=f"group_centrisevening_{chat_id}",
                        replace_existing=True,
                        timezone="Asia/Tashkent"
                    )
                else:
                    # Остальные сезоны — только 08:00
                    scheduler.add_job(
                        send_group_video_by_settings,
                        trigger='cron',
                        hour=8,
                        minute=0,
                        args=[chat_id],
                        id=f"group_centrismorning_{chat_id}",
                        replace_existing=True,
                        timezone="Asia/Tashkent"
                    )
            # Golden Lake
            if golden_enabled and golden_season_id:
                # Если выбран только Golden Lake — 08:00
                if not centris_enabled:
                    scheduler.add_job(
                        send_group_video_by_settings,
                        trigger='cron',
                        hour=8,
                        minute=0,
                        args=[chat_id],
                        id=f"group_golden_{chat_id}",
                        replace_existing=True,
                        timezone="Asia/Tashkent"
                    )
                # Если выбраны оба — Golden Lake в 11:00
                else:
                    scheduler.add_job(
                        send_group_video_by_settings,
                        trigger='cron',
                        hour=11,
                        minute=0,
                        args=[chat_id],
                        id=f"group_golden_{chat_id}",
                        replace_existing=True,
                        timezone="Asia/Tashkent"
                    )
        logger.info("Задачи для групп (логика через базу) запланированы по новым правилам")
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

        # Планируем задачи для групп с настройками
        schedule_group_jobs()

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
def update_group_video_settings_and_reset(chat_id, centris_enabled, centris_season, centris_start_video, golden_enabled, golden_start_video):
    db.set_group_video_settings(chat_id, centris_enabled, centris_season, centris_start_video, golden_enabled, golden_start_video)
    db.reset_group_viewed_videos(chat_id)

def schedule_group_jobs_v2():
    logger.info("Планирование задач для групп (фиксированное время)")
    jobs = scheduler.get_jobs()
    for job in jobs:
        if job.id.startswith("group_"):
            scheduler.remove_job(job.id)
    groups = db.get_all_groups_with_settings()
    for group in groups:
        chat_id = group[0]
        centris_enabled = bool(group[1])
        both_enabled = centris_enabled and bool(group[4])
        # Centris Towers
        centris_start_season_id, centris_start_video = db.get_group_video_start(chat_id, 'centris')
        if centris_enabled and centris_start_season_id:
            if str(centris_start_season_id) == '1':
                scheduler.add_job(
                    send_group_video_new,
                    'cron',
                    hour=8, minute=0,
                    args=[chat_id, 'centris', centris_start_season_id, centris_start_video],
                    id=f'group_{chat_id}_centris_1'
                )
                scheduler.add_job(
                    send_group_video_new,
                    'cron',
                    hour=20, minute=0,
                    args=[chat_id, 'centris', centris_start_season_id, centris_start_video],
                    id=f'group_{chat_id}_centris_2'
                )
            else:
                scheduler.add_job(
                    send_group_video_new,
                    'cron',
                    hour=8, minute=0,
                    args=[chat_id, 'centris', centris_start_season_id, centris_start_video],
                    id=f'group_{chat_id}_centris'
                )
    # Golden Lake
    golden_start_season_id, golden_start_video = db.get_group_video_start(chat_id, 'golden')
    if bool(group[4]) and golden_start_season_id:
        if both_enabled:
            scheduler.add_job(
                send_group_video_new,
                'cron',
                hour=11, minute=0,
                args=[chat_id, 'golden_lake', golden_start_season_id, golden_start_video],
                id=f'group_{chat_id}_golden'
            )
        else:
            scheduler.add_job(
                send_group_video_new,
                'cron',
                hour=8, minute=0,
                args=[chat_id, 'golden_lake', golden_start_season_id, golden_start_video],
                id=f'group_{chat_id}_golden'
            )