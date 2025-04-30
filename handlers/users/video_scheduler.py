try:
    from aiogram import types
    import asyncio
    from datetime import datetime, timedelta, time
    from db import db
    from loader import dp, bot
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    import pytz
    import logging
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

    # Настройка логирования
    logger = logging.getLogger(__name__)

    # Список из 14 ссылок на сообщения в канале
    VIDEO_LIST = [
        'https://t.me/c/2550852551/102',
        'https://t.me/c/2550852551/103',
        'https://t.me/c/2550852551/104',
        'https://t.me/c/2550852551/105',
        'https://t.me/c/2550852551/106',
        'https://t.me/c/2550852551/107',
        'https://t.me/c/2550852551/108',
        'https://t.me/c/2550852551/109',
        'https://t.me/c/2550852551/110',
        'https://t.me/c/2550852551/111',
        'https://t.me/c/2550852551/112',
        'https://t.me/c/2550852551/113',
        'https://t.me/c/2550852551/114',
        'https://t.me/c/2550852551/115',
        'https://t.me/c/2550852551/116'
    ]


    # Инициализация планировщика
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

    def get_next_video_index(user_id: int) -> int:
        """Получить следующий непросмотренный индекс видео"""
        viewed_videos = db.get_viewed_videos(user_id)
        current_index = db.get_video_index(user_id)
        
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
            logger.error(f"Ошибка в send_scheduled_video: {e}")

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
            await message.answer("Kechirasiz, xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

    # Модифицируем функцию планирования задач
    def schedule_jobs_for_users():
        try:
            logger.info("Начало планирования задач для пользователей")
            
            # Удаляем все существующие задачи
            scheduler.remove_all_jobs()
            logger.info("Все существующие задачи удалены")

            # Получаем всех подписанных пользователей
            users = db.get_all_users()
            logger.info(f"Найдено {len(users)} подписанных пользователей")
            
            if not users:
                logger.warning("Нет подписанных пользователей в базе данных")
                return

            for user_id in users:
                try:
                    logger.info(f"Обработка пользователя {user_id}")
                    
                    # Проверяем статус подписки
                    if not db.get_subscription_status(user_id):
                        logger.info(f"Пользователь {user_id} не подписан, пропускаем")
                        continue
                    
                    # Проверяем, есть ли непросмотренные видео
                    next_index = get_next_video_index(user_id)
                    if next_index == -1:
                        logger.info(f"Пользователь {user_id} уже просмотрел все видео, задача не создаётся")
                        continue

                    # Получаем предпочтительное время пользователя
                    preferred_time = db.get_preferred_time(user_id)
                    if not preferred_time:
                        preferred_time = "09:00"  # Время по умолчанию
                        db.set_preferred_time(user_id, preferred_time)

                    # Разбираем время на часы и минуты
                    hours, minutes = map(int, preferred_time.split(':'))
                    
                    # Добавляем задачу для этого пользователя
                    scheduler.add_job(
                        send_scheduled_video,
                        'cron',
                        hour=hours,
                        minute=minutes,
                        args=[user_id],
                        id=f"send_video_{user_id}",
                        replace_existing=True
                    )
                    logger.info(f"Задача для пользователя {user_id} запланирована на {preferred_time}")

                except Exception as e:
                    logger.error(f"Ошибка при планировании задачи для пользователя {user_id}: {e}")

            # Проверяем, что задачи были созданы
            jobs = scheduler.get_jobs()
            logger.info(f"Итоговое количество активных задач: {len(jobs)}")
            if len(jobs) == 0:
                logger.warning("Не было создано ни одной задачи")

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

except Exception as exx:
    from datetime import datetime
    now = datetime.now()
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    logger.error(f"Критическая ошибка в video_scheduler: {formatted_date_time} - {exx}")