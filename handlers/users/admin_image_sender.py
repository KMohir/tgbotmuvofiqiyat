from datetime import datetime, timedelta
import logging
from handlers.users.group_video_states import GroupVideoStates
from handlers.users.video_lists import VIDEO_LIST_1, VIDEO_LIST_2, VIDEO_LIST_3, VIDEO_LIST_4, VIDEO_LIST_5, VIDEO_LIST_GOLDEN_1
from data.config import ADMINS, SUPER_ADMIN_ID

# Настройка логирования
logger = logging.getLogger(__name__)

try:
    from aiogram import types
    from aiogram.dispatcher import FSMContext
    from aiogram.dispatcher.filters.builtin import Command
    from aiogram.types import MediaGroup
    import asyncio
    from db import db
    from loader import dp, bot
    print("dp в admin_image_sender.py:", id(dp))
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.dispatcher.filters.state import State, StatesGroup

    # FSM definitions moved to: GroupVideoStates in `handlers.users.group_video_states`

    # --- FSM для добавления сезона ---
    class AddSeasonStates(StatesGroup):
        waiting_for_project = State()
        waiting_for_season_name = State()
        waiting_for_video_links = State()
        waiting_for_video_titles = State()

    # --- FSM для редактирования сезона ---
    class EditSeasonStates(StatesGroup):
        waiting_for_season_id = State()
        waiting_for_new_name = State()
        waiting_for_action = State()  # edit_name, edit_video, delete_video, delete_season

    # --- FSM для редактирования видео ---
    class EditVideoStates(StatesGroup):
        waiting_for_video_id = State()
        waiting_for_new_url = State()
        waiting_for_new_title = State()
        waiting_for_new_position = State()

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

    # --- Клавиатуры для set_group_video ---
    def get_project_keyboard():
        """Клавиатура для выбора проекта"""
        return InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton("🏢 Centris Towers", callback_data="project_centris"),
            InlineKeyboardButton("🏢 Golden Lake", callback_data="project_golden"),
            InlineKeyboardButton("🏢 Centris + Golden", callback_data="project_both")
            )

    def get_season_keyboard(project):
        """Клавиатура для выбора сезона"""
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

    @dp.message_handler(Command('set_start_video'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def set_start_video_command(message: types.Message, state: FSMContext):
        await message.answer(
            "Har kungi video yuborishni qaysi videodan boshlashni belgilang.\n"
            "Video raqamini kiriting (1-15):"
        )
        await state.set_state("waiting_for_video_number")

    # Команда /set_group_video и связанные обработчики перенесены в handlers/users/group_video_commands.py
    # для устранения дублирования и циклических импортов

    # --- Тестовый обработчик ---
    @dp.message_handler(commands=['test_command'], chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
    async def test_command_handler(message: types.Message):
        """Тестовый обработчик для проверки работы команд в группах"""
        await message.answer("✅ **Тестовая команда работает!**\n\nБот получает сообщения в группе.")
        print(f"Тестовая команда получена от {message.from_user.id} в группе {message.chat.id}")

    @dp.message_handler(state="waiting_for_video_number")
    async def process_video_number(message: types.Message, state: FSMContext):
        if message.from_user.id != SUPER_ADMIN_ID and message.from_user.id not in ADMINS:
            await message.answer("Sizda bu buyruqni bajarish uchun ruxsat yo'q.")
            await state.finish()
            return

        try:
            video_number = int(message.text)
            if 1 <= video_number <= 15:
                # Сохраняем номер видео в базе данных
                db.set_start_video_index(video_number - 1)  # Индекс начинается с 0
                await message.answer(f"Har kungi video yuborish {video_number}-chi videodan boshlanadi.")
                logger.info(f"Админ {message.from_user.id} установил начальное видео: {video_number}")
            else:
                await message.answer("Video raqami 1-15 oralig'ida bo'lishi kerak.")
        except ValueError:
            await message.answer("Iltimos, to'g'ri raqam kiriting (1-15).")
        
        await state.finish()

    @dp.message_handler(Command('send_media'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def send_media_command(message: types.Message, state: FSMContext):
        await message.answer(
            "Iltimos, barcha foydalanuvchilarga jo'natmoqchi bo'lgan rasmlar yoki videolarni yuboring. "
            "Tugatganingizdan so'ng /done buyrug'ini kiritin.")
        await state.set_state("waiting_for_media")
        await state.update_data(media=[])

    @dp.message_handler(content_types=[types.ContentType.PHOTO, types.ContentType.VIDEO], state="waiting_for_media")
    async def process_media(message: types.Message, state: FSMContext):
        if message.from_user.id != SUPER_ADMIN_ID and message.from_user.id not in ADMINS:
            await message.answer("Sizda bu buyruqni bajarish uchun ruxsat yo'q.")
            await state.finish()
            return

        data = await state.get_data()
        media = data.get('media', [])

        if message.photo:
            file_id = message.photo[-1].file_id
            media_type = 'photo'
        elif message.video:
            file_id = message.video.file_id
            media_type = 'video'

        media.append({'file_id': file_id, 'type': media_type})
        await state.update_data(media=media)
        await message.answer(
            f"{media_type.capitalize()} qo'shildi. Jami: {len(media)}. Yana yuboring yoki /done buyrug'i bilan yakunlang.")

    @dp.message_handler(Command('done'), state="waiting_for_media")
    async def finish_media_collection(message: types.Message, state: FSMContext):
        if message.from_user.id != SUPER_ADMIN_ID and message.from_user.id not in ADMINS:
            await message.answer("Sizda bu buyruqni bajarish uchun ruxsat yo'q.")
            await state.finish()
            return

        data = await state.get_data()
        media = data.get('media', [])

        if not media:
            await message.answer("Siz birorta ham rasm yoki video yubormadingiz.")
            await state.finish()
            return

        # Переходим к состоянию ожидания описания
        await message.answer(
            "Media fayllar qabul qilindi. Endi media bilan birga jo'natiladigan opisaniyeni kiriting. "
            "Agar opisaniye kerak bo'lmasa, /skip buyrug'ini kiriting.")
        await state.set_state("waiting_for_caption")
        # Сохраняем медиа в состоянии
        await state.update_data(media=media)

    @dp.message_handler(Command('skip'), state="waiting_for_caption")
    async def skip_caption(message: types.Message, state: FSMContext):
        if message.from_user.id != SUPER_ADMIN_ID and message.from_user.id not in ADMINS:
            await message.answer("Sizda bu buyruqni bajarish uchun ruxsat yo'q.")
            await state.finish()
            return

        await process_media_sending(message, state, caption="")

    @dp.message_handler(state="waiting_for_caption")
    async def process_caption(message: types.Message, state: FSMContext):
        if message.from_user.id != SUPER_ADMIN_ID and message.from_user.id not in ADMINS:
            await message.answer("Sizda bu buyruqni bajarish uchun ruxsat yo'q.")
            await state.finish()
            return

        caption = message.text
        await process_media_sending(message, state, caption)

    async def process_media_sending(message: types.Message, state: FSMContext, caption: str):
        data = await state.get_data()
        media = data.get('media', [])

        total_media = len(media)
        await message.answer(f"Jami {total_media} ta media qabul qilindi. Opisaniye: {caption or 'yoq'}. Jo'natish boshlanadi...")

        users = db.get_all_users()


        chunk_size = 10
        media_chunks = [media[i:i + chunk_size] for i in range(0, len(media), chunk_size)]

        sent_count = 0
        for user_id in users:
            try:
                for chunk in media_chunks:
                    media_group = MediaGroup()
                    for i, item in enumerate(chunk):
                        if item['type'] == 'photo':
                            if i == 0 and caption:
                                media_group.attach_photo(item['file_id'], caption=caption)
                            else:
                                media_group.attach_photo(item['file_id'])
                        elif item['type'] == 'video':
                            if i == 0 and caption:
                                media_group.attach_video(item['file_id'], caption=caption)
                            else:
                                media_group.attach_video(item['file_id'])
                    await bot.send_media_group(
                        chat_id=user_id,
                        media=media_group,
                        protect_content=True
                    )
                    await asyncio.sleep(1)
                sent_count += 1
            except Exception as e:
                print(f"Media guruhini foydalanuvchiga yuborish mumkin emas {user_id}: {e}")
                continue

        await message.answer(
            f"{total_media} ta mediadan media guruhlar {sent_count} foydalanuvchilarga muvaffaqiyatli yuborildi!")
        await state.finish()

    @dp.message_handler(state="waiting_for_media")
    async def invalid_input(message: types.Message, state: FSMContext):
        await message.answer("Iltimos, rasm yoki video yuboring yoki /done buyrug'i bilan kirishni yakunlang.")
        await state.set_state("waiting_for_media")

    @dp.message_handler(Command('get_all_users'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def get_all_users_command(message: types.Message):
        users_data = db.get_all_users_data()
        if not users_data:
            await message.answer("Пользователей не найдено.")
            return

        response = "Список всех пользователей:\n\n"
        for user_id, name, phone, datetime, video_index, preferred_time, is_group in users_data:
            user_type = "Группа" if is_group else "Пользователь"
            response += f"ID: {user_id}\n"
            response += f"Тип: {user_type}\n"
            response += f"Имя: {name}\n"
            if not is_group:
                response += f"Телефон: {phone}\n"
            response += f"Дата регистрации: {datetime}\n"
            response += f"Индекс видео: {video_index}\n"
            response += f"Предпочтительное время: {preferred_time}\n"
            response += "-" * 30 + "\n"

        # Разбиваем на части, если сообщение слишком длинное
        if len(response) > 4096:
            for x in range(0, len(response), 4096):
                await message.answer(response[x:x+4096])
        else:
            await message.answer(response)

    @dp.message_handler(Command('banned_groups'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def banned_groups_command(message: types.Message):
        banned_groups = db.get_banned_groups()
        if not banned_groups:
            await message.answer("Заблокированных групп нет.")
            return

        response = "Список заблокированных групп:\n\n"
        for group_id, group_name in banned_groups:
            response += f"ID: {group_id}\n"
            response += f"Название: {group_name}\n"
            response += "-" * 30 + "\n"

        await message.answer(response)

    @dp.message_handler(Command('unban_group'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def unban_group_command(message: types.Message):
        try:
            group_id = int(message.text.split()[1])
            db.unban_group(group_id)
            await message.answer(f"Группа {group_id} разблокирована.")
        except (IndexError, ValueError):
            await message.answer("Использование: /unban_group <ID_группы>")

    @dp.message_handler(Command('reset_group_videos'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def reset_group_videos_command(message: types.Message, state: FSMContext):
        chat_id = message.chat.id
        db.reset_group_viewed_videos(chat_id)
        await message.answer("Прогресс группы сброшен. Теперь можно выбрать стартовое видео заново.")

    @dp.message_handler(Command('add_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def add_season_command(message: types.Message, state: FSMContext):
        print('add_season_command вызван')
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("Centris Towers", callback_data="add_project_centris"),
            InlineKeyboardButton("Golden Lake", callback_data="add_project_golden")
        )
        await message.answer("Выберите проект для нового сезона:", reply_markup=kb)
        await state.set_state(AddSeasonStates.waiting_for_project.state)

    @dp.callback_query_handler(lambda c: c.data.startswith("add_project_"), state=AddSeasonStates.waiting_for_project.state)
    async def add_season_project(callback_query: types.CallbackQuery, state: FSMContext):
        project = callback_query.data.replace("add_project_", "")
        
        # Автокоррекция названий проектов
        if project == "centr":
            project = "centris"
        elif project == "golden":
            project = "golden"
        
        logger.info(f"Выбран проект: {project}")
        await state.update_data(project=project)
        await safe_edit_text(callback_query, "Введите название сезона:")
        await state.set_state(AddSeasonStates.waiting_for_season_name.state)

    @dp.message_handler(state=AddSeasonStates.waiting_for_season_name)
    async def add_season_name(message: types.Message, state: FSMContext):
        await state.update_data(season_name=message.text.strip())
        await message.answer("Отправьте список ссылок на видео (каждая ссылка с новой строки):")
        await state.set_state(AddSeasonStates.waiting_for_video_links.state)

    @dp.message_handler(state=AddSeasonStates.waiting_for_video_links)
    async def add_season_video_links(message: types.Message, state: FSMContext):
        links = [l.strip() for l in message.text.strip().splitlines() if l.strip()]
        await state.update_data(video_links=links)
        await message.answer("Отправьте список названий видео (каждое название с новой строки, порядок должен совпадать со ссылками):")
        await state.set_state(AddSeasonStates.waiting_for_video_titles.state)

    @dp.message_handler(state=AddSeasonStates.waiting_for_video_titles)
    async def add_season_video_titles(message: types.Message, state: FSMContext):
        titles = [t.strip() for t in message.text.strip().splitlines() if t.strip()]
        data = await state.get_data()
        links = data.get("video_links", [])
        if len(links) != len(titles):
            await message.answer(f"Количество ссылок ({len(links)}) и названий ({len(titles)}) не совпадает! Попробуйте снова. Отправьте список названий видео:")
            return
        
        logger.info(f"Начинаем добавление сезона: project={data.get('project')}, season_name={data.get('season_name')}")
        
        # Сохраняем сезон и видео в базу
        project = data.get("project")
        season_name = data.get("season_name")
        
        # Финальная проверка и коррекция названия проекта
        if project == "centr":
            project = "centris"
            logger.info(f"Исправлено название проекта с 'centr' на 'centris'")
        
        logger.info(f"Финальное название проекта: {project}")
        season_info = db.add_season_with_videos(project, season_name, links, titles)
        
        if season_info:
            logger.info(f"Сезон успешно добавлен в БД: {season_info}")
            
            # Обновляем клавиатуру сезонов для всех активных чатов
            logger.info(f"Вызываем update_season_keyboards_for_all_chats для проекта {project}")
            await update_season_keyboards_for_all_chats(project)
            
            # ДОПОЛНИТЕЛЬНО: Принудительно очищаем кэш для гарантии
            try:
                from handlers.users.video_selector import clear_season_keyboard_cache
                logger.info(f"Дополнительная принудительная очистка кэша для проекта {project}")
                clear_season_keyboard_cache(project)
                logger.info(f"✅ Дополнительная очистка кэша завершена для проекта {project}")
            except Exception as e:
                logger.error(f"❌ Ошибка при дополнительной очистке кэша: {e}")
            
            # ПРИНУДИТЕЛЬНО: Очищаем весь кэш для всех проектов
            try:
                logger.info("Принудительная очистка всего кэша для всех проектов")
                clear_season_keyboard_cache()  # Без параметров - очищает весь кэш
                logger.info("✅ Весь кэш очищен")
            except Exception as e:
                logger.error(f"❌ Ошибка при очистке всего кэша: {e}")
            
            # Отправляем уведомление о новом сезоне в активные группы
            logger.info(f"Вызываем notify_active_groups_about_new_season для проекта {project}")
            await notify_active_groups_about_new_season(project, season_name, len(links))
            
            # ОБНОВЛЯЕМ ГЛАВНОЕ МЕНЮ для всех активных чатов
            try:
                from handlers.users.video_selector import force_update_main_menu
                logger.info("🔄 Принудительно обновляем главное меню для всех активных чатов...")
                
                # Принудительно обновляем главное меню
                updated_main_menu = force_update_main_menu()
                
                if updated_main_menu:
                    logger.info("✅ Главное меню принудительно обновлено")
                    
                    # Отправляем обновленное меню пользователю
                    await message.answer(
                        "🔄 **Главное меню принудительно обновлено!** Теперь выберите проект:",
                        reply_markup=updated_main_menu
                    )
                    
                    # Если меню успешно обновлено, отправляем краткое сообщение
                    await message.answer(
                        f"✅ Сезон '{season_name}' успешно добавлен в проект '{project}'!\n\n"
                        f"📊 ID сезона: {season_info['season_id']}\n"
                        f"🎬 Количество видео: {season_info['video_count']}\n\n"
                        "🔄 **Главное меню обновлено!** Выберите проект выше для просмотра нового сезона."
                    )
                else:
                    logger.error("❌ Не удалось обновить главное меню")
                    # Если не удалось обновить меню, отправляем обычное сообщение
                    await message.answer(
                        f"✅ Сезон '{season_name}' успешно добавлен в проект '{project}'!\n\n"
                        f"📊 ID сезона: {season_info['season_id']}\n"
                        f"🎬 Количество видео: {season_info['video_count']}\n\n"
                        "💡 **Кэш полностью очищен!** Новый сезон будет виден сразу.\n\n"
                        "🔧 **Для проверки используйте:**\n"
                        "   /test_cache - проверить состояние\n"
                        "   /sync_keyboards - синхронизировать\n"
                        "   /force_refresh_seasons - принудительно обновить\n"
                        "   /update_main_menu - обновить главное меню\n\n"
                        "📱 **Теперь выберите проект в главном меню - новый сезон должен отобразиться!**"
                    )
                
            except Exception as e:
                logger.error(f"❌ Ошибка при обновлении главного меню: {e}")
                # Если не удалось обновить меню, отправляем обычное сообщение
                await message.answer(
                    f"✅ Сезон '{season_name}' успешно добавлен в проект '{project}'!\n\n"
                    f"📊 ID сезона: {season_info['season_id']}\n"
                    f"🎬 Количество видео: {season_info['video_count']}\n\n"
                    "💡 **Кэш полностью очищен!** Новый сезон будет виден сразу.\n\n"
                    "🔧 **Для проверки используйте:**\n"
                    "   /test_cache - проверить состояние\n"
                    "   /sync_keyboards - синхронизировать\n"
                    "   /force_refresh_seasons - принудительно обновить\n"
                    "   /update_main_menu - обновить главное меню\n\n"
                    "📱 **Теперь выберите проект в главном меню - новый сезон должен отобразиться!**"
                )
        else:
            logger.error(f"Ошибка при добавлении сезона в БД")
            await message.answer("❌ Ошибка при добавлении сезона. Попробуйте снова.")
        
        await state.finish()

    @dp.message_handler(Command('refresh_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def refresh_seasons_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры сезонов во всех активных чатах
        """
        try:
            from handlers.users.video_selector import clear_season_keyboard_cache
            
            # Очищаем кэш для всех проектов
            clear_season_keyboard_cache()
            
            await message.answer("✅ Кэш клавиатуры сезонов очищен для всех проектов.\n\n"
                               "Теперь при выборе проекта 'Centris towers' или 'Golden lake' "
                               "пользователи увидят обновленный список сезонов.")
            
        except Exception as e:
            await message.answer(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")

    @dp.message_handler(Command('cache_status'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def cache_status_command(message: types.Message):
        """
        Команда для просмотра статуса кэша клавиатуры сезонов
        """
        try:
            from handlers.users.video_selector import _season_keyboard_cache, _cache_timestamp
            import time
            
            current_time = time.time()
            
            if not _season_keyboard_cache:
                await message.answer("📋 Кэш клавиатуры сезонов пуст.")
                return
            
            status_text = "📋 Статус кэша клавиатуры сезонов:\n\n"
            
            for cache_key, keyboard in _season_keyboard_cache.items():
                if cache_key in _cache_timestamp:
                    age = current_time - _cache_timestamp[cache_key]
                    age_minutes = int(age // 60)
                    age_seconds = int(age % 60)
                    
                    status_text += f"🔑 {cache_key}:\n"
                    status_text += f"   ⏰ Возраст: {age_minutes}м {age_seconds}с\n"
                    status_text += f"   📱 Кнопок: {len(keyboard.keyboard)}\n\n"
            
            await message.answer(status_text)
            
        except Exception as e:
            await message.answer(f"❌ Ошибка при получении статуса кэша: {e}")

    @dp.message_handler(Command('test_cache'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def test_cache_command(message: types.Message):
        """
        Команда для тестирования системы кэширования и отображения сезонов
        """
        try:
            from handlers.users.video_selector import get_season_keyboard, clear_season_keyboard_cache, _season_keyboard_cache, _cache_timestamp
            
            logger.info("=== НАЧАЛО ТЕСТИРОВАНИЯ КЭША ===")
            
            # Проверяем текущий кэш
            current_cache_size = len(_season_keyboard_cache)
            current_timestamp_size = len(_cache_timestamp)
            
            response = f"🧪 **ТЕСТ СИСТЕМЫ КЭШИРОВАНИЯ**\n\n"
            response += f"📊 **Текущее состояние кэша:**\n"
            response += f"   • Размер кэша: {current_cache_size}\n"
            response += f"   • Размер временных меток: {current_timestamp_size}\n"
            
            if current_cache_size > 0:
                response += f"   • Ключи в кэше: {list(_season_keyboard_cache.keys())}\n"
            
            # Очищаем кэш
            logger.info("Очищаем кэш для тестирования")
            clear_season_keyboard_cache()
            
            # Получаем свежие клавиатуры
            logger.info("Получаем свежие клавиатуры для тестирования")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Проверяем количество сезонов
            centris_seasons_count = len(centris_keyboard.keyboard) - 1  # минус кнопка "Orqaga qaytish"
            golden_seasons_count = len(golden_keyboard.keyboard) - 1   # минус кнопка "Orqaga qaytish"
            
            response += f"\n🔄 **После очистки кэша:**\n"
            response += f"   • Centris Towers: {centris_seasons_count} сезонов\n"
            response += f"   • Golden Lake: {golden_seasons_count} сезонов\n"
            response += f"   • Новый размер кэша: {len(_season_keyboard_cache)}\n"
            
            # Проверяем БД напрямую
            logger.info("Проверяем БД напрямую")
            centris_seasons_db = db.get_seasons_by_project("centris")
            golden_seasons_db = db.get_seasons_by_project("golden")
            
            response += f"\n🗄️ **Прямая проверка БД:**\n"
            response += f"   • Centris Towers в БД: {len(centris_seasons_db)} сезонов\n"
            response += f"   • Golden Lake в БД: {len(golden_seasons_db)} сезонов\n"
            
            if centris_seasons_db:
                response += f"   • Centris сезоны: {[name for _, name in centris_seasons_db]}\n"
            if golden_seasons_db:
                response += f"   • Golden сезоны: {[name for _, name in golden_seasons_db]}\n"
            
            # Проверяем соответствие
            if centris_seasons_count == len(centris_seasons_db) and golden_seasons_count == len(golden_seasons_db):
                response += f"\n✅ **РЕЗУЛЬТАТ: Кэш работает корректно!**\n"
                response += f"Количество сезонов в кэше соответствует БД."
            else:
                response += f"\n❌ **РЕЗУЛЬТАТ: Обнаружено несоответствие!**\n"
                response += f"Кэш не синхронизирован с БД."
            
            logger.info("=== КОНЕЦ ТЕСТИРОВАНИЯ КЭША ===")
            
            await message.answer(response, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при тестировании кэша: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при тестировании кэша: {e}")

    @dp.message_handler(Command('sync_keyboards'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def sync_keyboards_command(message: types.Message):
        """
        Команда для принудительной синхронизации всех клавиатур с базой данных
        """
        try:
            from handlers.users.video_selector import clear_season_keyboard_cache, get_season_keyboard
            
            logger.info("=== НАЧАЛО sync_keyboards ===")
            
            # Очищаем весь кэш
            logger.info("Очищаем весь кэш клавиатур")
            clear_season_keyboard_cache()
            
            # Получаем свежие данные из БД
            logger.info("Получаем свежие данные из БД")
            centris_seasons_db = db.get_seasons_by_project("centris")
            golden_seasons_db = db.get_seasons_by_project("golden")
            
            # Создаем новые клавиатуры
            logger.info("Создаем новые клавиатуры")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Проверяем синхронизацию
            centris_count = len(centris_keyboard.keyboard) - 1
            golden_count = len(golden_keyboard.keyboard) - 1
            
            response = f"🔄 **СИНХРОНИЗАЦИЯ КЛАВИАТУР ЗАВЕРШЕНА!**\n\n"
            response += f"📊 **Результат синхронизации:**\n"
            response += f"   • Centris Towers: {centris_count} сезонов (БД: {len(centris_seasons_db)})\n"
            response += f"   • Golden Lake: {golden_count} сезонов (БД: {len(golden_seasons_db)})\n\n"
            
            # Проверяем соответствие
            centris_sync = centris_count == len(centris_seasons_db)
            golden_sync = golden_count == len(golden_seasons_db)
            
            if centris_sync and golden_sync:
                response += f"✅ **ВСЕ КЛАВИАТУРЫ СИНХРОНИЗИРОВАНЫ!**\n"
                response += f"Кэш полностью соответствует базе данных."
            else:
                response += f"⚠️ **ОБНАРУЖЕНЫ НЕСООТВЕТСТВИЯ:**\n"
                if not centris_sync:
                    response += f"   • Centris Towers: кэш {centris_count} vs БД {len(centris_seasons_db)}\n"
                if not golden_sync:
                    response += f"   • Golden Lake: кэш {golden_count} vs БД {len(golden_seasons_db)}\n"
                response += f"\n🔧 Попробуйте использовать /force_refresh_seasons"
            
            response += f"\n\n💡 **Теперь пользователи увидят актуальные сезоны!**"
            
            await message.answer(response, parse_mode="Markdown")
            
            logger.info(f"=== КОНЕЦ sync_keyboards ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при синхронизации клавиатур: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при синхронизации клавиатур: {e}")

    @dp.message_handler(Command('simple_cache_status'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def simple_cache_status_command(message: types.Message):
        """
        Простая команда для проверки состояния кэша
        """
        try:
            await message.answer("🔍 Проверяем состояние кэша...")
            
            # Проверяем, можем ли мы импортировать модуль
            try:
                from handlers.users.video_selector import _season_keyboard_cache, _cache_timestamp
                await message.answer("✅ Модуль video_selector импортирован успешно")
                
                if not _season_keyboard_cache:
                    await message.answer("📋 Кэш пуст - это хорошо!")
                else:
                    cache_size = len(_season_keyboard_cache)
                    await message.answer(f"📋 В кэше {cache_size} элементов")
                    
            except ImportError as e:
                await message.answer(f"❌ Ошибка импорта: {e}")
            except Exception as e:
                await message.answer(f"❌ Ошибка при проверке кэша: {e}")
                
        except Exception as e:
            await message.answer(f"❌ Общая ошибка: {e}")

    @dp.message_handler(Command('test_commands'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def test_commands_command(message: types.Message):
        """
        Простая тестовая команда для проверки работы
        """
        try:
            await message.answer("✅ Команды работают! Бот функционирует нормально.")
            logger.info("Тестовая команда выполнена успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка в тестовой команде: {e}")
            await message.answer(f"❌ Ошибка: {e}")

    @dp.message_handler(Command('instant_refresh'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def instant_refresh_command(message: types.Message):
        """
        Команда для мгновенного обновления клавиатуры в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard
            
            logger.info("=== НАЧАЛО instant_refresh ===")
            
            # Получаем свежие клавиатуры напрямую из БД (без кэша)
            logger.info("Получаем свежие клавиатуры напрямую из БД")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1
            golden_seasons = len(golden_keyboard.keyboard) - 1
            
            response = f"⚡ **МГНОВЕННОЕ ОБНОВЛЕНИЕ КЛАВИАТУРЫ!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Мгновенное обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 **Клавиатуры обновлены напрямую из БД!**\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ instant_refresh ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при мгновенном обновлении: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при мгновенном обновлении: {e}")

    @dp.message_handler(Command('force_refresh_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def force_refresh_seasons_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры сезонов в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard, clear_season_keyboard_cache
            
            logger.info("=== НАЧАЛО force_refresh_seasons ===")
            
            # Очищаем кэш для всех проектов
            logger.info("Очищаем кэш для всех проектов")
            clear_season_keyboard_cache()
            
            # Создаем обновленные клавиатуры
            logger.info("Создаем обновленные клавиатуры")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1  # минус кнопка "Orqaga qaytish"
            golden_seasons = len(golden_keyboard.keyboard) - 1   # минус кнопка "Orqaga qaytish"
            
            response = f"🔄 **Клавиатуры сезонов обновлены!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 Теперь пользователи увидят актуальный список сезонов.\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ force_refresh_seasons ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")

    @dp.message_handler(Command('list_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def list_seasons_command(message: types.Message):
        try:
            # Получаем сезоны с количеством видео для Centris Towers
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            # Получаем сезоны с количеством видео для Golden Lake
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            response = "📋 Список добавленных сезонов:\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
            
            if not centris_seasons and not golden_seasons:
                response += "Пока нет добавленных сезонов."
            
            await message.answer(response)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(Command('edit_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def edit_season_command(message: types.Message, state: FSMContext):
        try:
            # Получаем все сезоны с количеством видео
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            if not centris_seasons and not golden_seasons:
                await message.answer("Нет сезонов для редактирования.")
                return
            
            response = "📝 Выберите сезон для редактирования (введите ID):\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_season_id.state)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_season_id)
    async def process_season_id_for_edit(message: types.Message, state: FSMContext):
        try:
            season_id = int(message.text.strip())
            season_data = db.get_season_by_id(season_id)
            
            if not season_data:
                await message.answer("Сезон с таким ID не найден. Попробуйте снова:")
                return
            
            season_id, project, season_name = season_data
            videos = db.get_videos_with_ids_by_season(season_id)
            
            await state.update_data(season_id=season_id, project=project, season_name=season_name)
            
            response = f"📝 Редактирование сезона:\n"
            response += f"ID: {season_id}\n"
            response += f"Проект: {project}\n"
            response += f"Название: {season_name}\n"
            response += f"Количество видео: {len(videos)}\n\n"
            
            if videos:
                response += "Видео в сезоне:\n"
                for video_id, url, title, position in videos:
                    response += f"  ID {video_id}: {title} (позиция {position})\n"
            
            response += "\nВыберите действие:\n"
            response += "1. Изменить название сезона\n"
            response += "2. Редактировать видео\n"
            response += "3. Удалить отдельные видео\n"
            response += "4. Удалить весь сезон\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_action.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID сезона (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_action)
    async def process_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if action == "1":
            await message.answer("Введите новое название сезона:")
            await state.set_state(EditSeasonStates.waiting_for_new_name.state)
        elif action == "2":
            await message.answer("Введите ID видео для редактирования:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "3":
            await message.answer("Введите ID видео для удаления:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "4":
            # Подтверждение удаления сезона
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да, удалить", callback_data=f"confirm_delete_season_{season_id}"),
                InlineKeyboardButton("Отмена", callback_data="cancel_delete")
            )
            await message.answer("⚠️ Вы уверены, что хотите удалить весь сезон и все его видео?", reply_markup=kb)
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditSeasonStates.waiting_for_new_name)
    async def process_new_season_name(message: types.Message, state: FSMContext):
        new_name = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if db.update_season(season_id, new_name):
            await message.answer(f"✅ Название сезона успешно изменено на: {new_name}")
        else:
            await message.answer("❌ Ошибка при обновлении названия сезона.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_video_id)
    async def process_video_id_for_edit(message: types.Message, state: FSMContext):
        try:
            video_id = int(message.text.strip())
            video_data = db.get_video_by_id(video_id)
            
            if not video_data:
                await message.answer("Видео с таким ID не найдено. Попробуйте снова:")
                return
            
            video_id, season_id, url, title, position = video_data
            await state.update_data(video_id=video_id, season_id=season_id, url=url, title=title, position=position)
            
            response = f"📹 Редактирование видео:\n"
            response += f"ID: {video_id}\n"
            response += f"Название: {title}\n"
            response += f"Позиция: {position}\n"
            response += f"URL: {url}\n\n"
            response += "Выберите действие:\n"
            response += "1. Изменить URL\n"
            response += "2. Изменить название\n"
            response += "3. Изменить позицию\n"
            response += "4. Удалить видео\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID видео (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_video_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        
        if action == "1":
            await message.answer("Введите новый URL видео:")
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        elif action == "2":
            await message.answer("Введите новое название видео:")
            await state.set_state(EditVideoStates.waiting_for_new_title.state)
        elif action == "3":
            await message.answer("Введите новую позицию видео (число):")
            await state.set_state(EditVideoStates.waiting_for_new_position.state)
        elif action == "4":
            video_id = data.get("video_id")
            if db.delete_video(video_id):
                await message.answer("✅ Видео успешно удалено.")
            else:
                await message.answer("❌ Ошибка при удалении видео.")
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование видео отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_new_video_url(message: types.Message, state: FSMContext):
        new_url = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        title = data.get("title")
        position = data.get("position")
        
        if db.update_video(video_id, new_url, title, position):
            await message.answer(f"✅ URL видео успешно изменен на: {new_url}")
        else:
            await message.answer("❌ Ошибка при обновлении URL видео.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_new_title)
    async def process_new_video_title(message: types.Message, state: FSMContext):
        new_title = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        url = data.get("url")
        position = data.get("position")
        
        if db.update_video(video_id, url, new_title, position):
            await message.answer(f"✅ Название видео успешно изменено на: {new_title}")
        else:
            await message.answer("❌ Ошибка при обновлении названия видео.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_new_position)
    async def process_new_video_position(message: types.Message, state: FSMContext):
        try:
            new_position = int(message.text.strip())
            data = await state.get_data()
            video_id = data.get("video_id")
            url = data.get("url")
            title = data.get("title")
            
            if db.update_video(video_id, url, title, new_position):
                await message.answer(f"✅ Позиция видео успешно изменена на: {new_position}")
            else:
                await message.answer("❌ Ошибка при обновлении позиции видео.")
        except ValueError:
            await message.answer("Пожалуйста, введите корректную позицию (число):")
            return
        
        await state.finish()

    @dp.callback_query_handler(lambda c: c.data.startswith("confirm_delete_season_"))
    async def confirm_delete_season(callback_query: types.CallbackQuery):
        season_id = int(callback_query.data.replace("confirm_delete_season_", ""))
        
        if db.delete_season(season_id):
            await safe_edit_text(callback_query, "✅ Сезон и все его видео успешно удалены.")
        else:
            await safe_edit_text(callback_query, "❌ Ошибка при удалении сезона.")
        
        await callback_query.answer()

    @dp.callback_query_handler(lambda c: c.data == "cancel_delete")
    async def cancel_delete_season(callback_query: types.CallbackQuery):
        await safe_edit_text(callback_query, "❌ Удаление отменено.")
        await callback_query.answer()

    @dp.message_handler(Command('delete_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def delete_season_command(message: types.Message):
        try:
            # Парсим ID сезона из команды
            args = message.text.split()
            if len(args) != 2:
                await message.answer("Использование: /delete_season <ID_сезона>")
                return
            
            season_id = int(args[1])
            season_data = db.get_season_by_id(season_id)
            
            if not season_data:
                await message.answer("Сезон с таким ID не найден.")
                return
            
            season_id, project, season_name = season_data
            videos = db.get_videos_by_season(season_id)
            
            response = f"⚠️ Подтвердите удаление сезона:\n"
            response += f"ID: {season_id}\n"
            response += f"Проект: {project}\n"
            response += f"Название: {season_name}\n"
            response += f"Количество видео: {len(videos)}\n\n"
            response += "Все видео будут удалены безвозвратно!"
            
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да, удалить", callback_data=f"confirm_delete_season_{season_id}"),
                InlineKeyboardButton("Отмена", callback_data="cancel_delete")
            )
            
            await message.answer(response, reply_markup=kb)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID сезона (число).")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(Command('season_help'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def season_help_command(message: types.Message):
        help_text = """
📋 **Команды для управления сезонами:**

**Добавление:**
• `/add_season` - Добавить новый сезон
• `/list_seasons` - Показать все сезоны

**Редактирование:**
• `/edit_season` - Редактировать существующий сезон
  - Изменить название сезона
  - Редактировать видео (URL, название, позиция)
  - Удалить отдельные видео

**Удаление:**
• `/delete_season <ID>` - Удалить сезон по ID

**Утилиты:**
• `/migrate_old_seasons` - Перенести старые сезоны в базу данных
• `/fix_season_order` - Исправить порядок сезонов (Яқинлар I Ташриф будет последним)

**Примеры использования:**
1. Добавить сезон: `/add_season`
2. Посмотреть сезоны: `/list_seasons`
3. Редактировать сезон: `/edit_season` (затем выбрать ID)
4. Удалить сезон: `/delete_season 5`
5. Исправить порядок: `/fix_season_order`

⚠️ **Внимание:** Удаление сезона удаляет все его видео безвозвратно!

📝 **Особенности:**
• Сезон "Яқинлар I Ташриф Centris Towers" всегда будет последним в меню
• Новые сезоны добавляются в правильном порядке автоматически
        """
        await message.answer(help_text)

    @dp.message_handler(Command('migrate_old_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def migrate_old_seasons_command(message: types.Message):
        """Миграция старых сезонов в базу данных"""
        try:
            # Проверяем, есть ли уже сезоны в базе
            centris_seasons = db.get_seasons_by_project("centris")
            golden_seasons = db.get_seasons_by_project("golden")
            
            if centris_seasons or golden_seasons:
                await message.answer("Сезоны уже есть в базе данных. Миграция не требуется.")
                return
            
            # Добавляем старые сезоны Centris Towers
            old_centris_seasons = [
                ("centris", "Яқинлар 1.0 I I Иброҳим Мамасаидов", VIDEO_LIST_1, CAPTION_LIST_1),
                ("centris", "Яқинлар 2.0 I I Иброҳим Мамасаидов", VIDEO_LIST_2, CAPTION_LIST_2),
                ("centris", "Яқинлар 3.0 I I Иброҳим Мамасаидов", VIDEO_LIST_3, CAPTION_LIST_3),
                ("centris", "Яқинлар 4.0 I I Иброҳим Мамасаидов", VIDEO_LIST_4, CAPTION_LIST_4),
                ("centris", "Яқинлар 5.0 I I Иброҳим Мамасаидов", VIDEO_LIST_5, CAPTION_LIST_5),
                ("centris", "Яқинлар I Ташриф Centris Towers", VIDEO_LIST_6, CAPTION_LIST_6),
            ]
            
            # Добавляем старые сезоны Golden Lake
            old_golden_seasons = [
                ("golden", "Golden lake 1", VIDEO_LIST_GOLDEN_1, GOLDEN_LIST),
            ]
            
            migrated_count = 0
            
            # Мигрируем Centris Towers
            for project, season_name, video_list, caption_list in old_centris_seasons:
                if len(video_list) == len(caption_list):
                    db.add_season_with_videos(project, season_name, video_list, caption_list)
                    migrated_count += 1
            
            # Мигрируем Golden Lake
            for project, season_name, video_list, caption_list in old_golden_seasons:
                if len(video_list) == len(caption_list):
                    db.add_season_with_videos(project, season_name, video_list, caption_list)
                    migrated_count += 1
            
            await message.answer(f"✅ Миграция завершена! Добавлено {migrated_count} сезонов.")
            
        except Exception as e:
            await message.answer(f"❌ Ошибка при миграции: {e}")

    @dp.message_handler(Command('fix_season_order'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def fix_season_order_command(message: types.Message):
        """Исправить порядок сезонов, чтобы 'Яқинлар I Ташриф Centris Towers' был последним"""
        try:
            # Получаем все сезоны Centris Towers
            centris_seasons = db.get_seasons_by_project("centris")
            
            if not centris_seasons:
                await message.answer("Нет сезонов Centris Towers для исправления порядка.")
                return
            
            # Проверяем, есть ли сезон "Яқинлар I Ташриф Centris Towers"
            tour_season = None
            other_seasons = []
            
            for season_id, season_name in centris_seasons:
                if season_name == "Яқинлар I Ташриф Centris Towers":
                    tour_season = (season_id, season_name)
                else:
                    other_seasons.append((season_id, season_name))
            
            if not tour_season:
                await message.answer("Сезон 'Яқинлар I Ташриф Centris Towers' не найден в базе данных.")
                return
            
            # Удаляем сезон "Яқинлар I Ташриф Centris Towers" и добавляем его заново
            # Это обеспечит, что он будет последним по ID
            tour_season_id, tour_season_name = tour_season
            
            # Получаем видео этого сезона
            videos = db.get_videos_by_season(tour_season_id)
            if not videos:
                await message.answer("В сезоне 'Яқинлар I Ташриф Centris Towers' нет видео.")
                return
            
            # Сохраняем данные видео
            video_data = [(url, title, position) for url, title, position in videos]
            
            # Удаляем старый сезон (видео удалятся каскадно)
            if db.delete_season(tour_season_id):
                # Добавляем сезон заново
                urls = [data[0] for data in video_data]
                titles = [data[1] for data in video_data]
                db.add_season_with_videos("centris", tour_season_name, urls, titles)
                
                await message.answer("✅ Порядок сезонов исправлен! Сезон 'Яқинлар I Ташриф Centris Towers' теперь будет последним.")
            else:
                await message.answer("❌ Ошибка при исправлении порядка сезонов.")
                
        except Exception as e:
            await message.answer(f"❌ Ошибка при исправлении порядка сезонов: {e}")

    @dp.message_handler(commands=['fix_season_project'], user_id=ADMINS + [SUPER_ADMIN_ID])
    async def fix_season_project_command(message: types.Message):
        try:
            args = message.text.split()
            if len(args) != 3:
                await message.answer("Использование: /fix_season_project <season_id> <project>")
                return
            season_id = int(args[1])
            new_project = args[2]
            if db.update_season_project(season_id, new_project):
                await message.answer(f"Project сезона {season_id} успешно изменён на '{new_project}'")
            else:
                await message.answer("Ошибка при обновлении project сезона.")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(Command('force_update_keyboards'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def force_update_keyboards_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры без кэша
        """
        try:
            await message.answer("🔄 Принудительное обновление клавиатуры...")
            
            # Импортируем функцию напрямую из БД
            try:
                from db import db
                
                # Получаем сезоны напрямую из БД
                centris_seasons = db.get_seasons_by_project("centris")
                golden_seasons = db.get_seasons_by_project("golden")
                
                centris_count = len(centris_seasons)
                golden_count = len(golden_seasons)
                
                response = f"📊 **Данные из БД (без кэша):**\n\n"
                response += f"🏢 **Centris Towers**: {centris_count} сезонов\n"
                for season_id, season_name in centris_seasons:
                    response += f"   • {season_name} (ID: {season_id})\n"
                
                response += f"\n🏖️ **Golden Lake**: {golden_count} сезонов\n"
                for season_id, season_name in golden_seasons:
                    response += f"   • {season_name} (ID: {season_id})\n"
                
                await message.answer(response)
                
                # Теперь принудительно очищаем кэш
                try:
                    from handlers.users.video_selector import clear_season_keyboard_cache
                    clear_season_keyboard_cache()
                    await message.answer("✅ Кэш очищен! Теперь выберите проект в главном меню.")
                except Exception as e:
                    await message.answer(f"⚠️ Кэш не очищен: {e}")
                
            except Exception as e:
                await message.answer(f"❌ Ошибка при получении данных из БД: {e}")
                
        except Exception as e:
            await message.answer(f"❌ Общая ошибка: {e}")

    @dp.message_handler(Command('simple_cache_status'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def simple_cache_status_command(message: types.Message):
        """
        Простая команда для проверки состояния кэша
        """
        try:
            await message.answer("🔍 Проверяем состояние кэша...")
            
            # Проверяем, можем ли мы импортировать модуль
            try:
                from handlers.users.video_selector import _season_keyboard_cache, _cache_timestamp
                await message.answer("✅ Модуль video_selector импортирован успешно")
                
                if not _season_keyboard_cache:
                    await message.answer("📋 Кэш пуст - это хорошо!")
                else:
                    cache_size = len(_season_keyboard_cache)
                    await message.answer(f"📋 В кэше {cache_size} элементов")
                    
            except ImportError as e:
                await message.answer(f"❌ Ошибка импорта: {e}")
            except Exception as e:
                await message.answer(f"❌ Ошибка при проверке кэша: {e}")
                
        except Exception as e:
            await message.answer(f"❌ Общая ошибка: {e}")

    @dp.message_handler(Command('test_commands'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def test_commands_command(message: types.Message):
        """
        Простая тестовая команда для проверки работы
        """
        try:
            await message.answer("✅ Команды работают! Бот функционирует нормально.")
            logger.info("Тестовая команда выполнена успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка в тестовой команде: {e}")
            await message.answer(f"❌ Ошибка: {e}")

    @dp.message_handler(Command('instant_refresh'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def instant_refresh_command(message: types.Message):
        """
        Команда для мгновенного обновления клавиатуры в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard
            
            logger.info("=== НАЧАЛО instant_refresh ===")
            
            # Получаем свежие клавиатуры напрямую из БД (без кэша)
            logger.info("Получаем свежие клавиатуры напрямую из БД")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1
            golden_seasons = len(golden_keyboard.keyboard) - 1
            
            response = f"⚡ **МГНОВЕННОЕ ОБНОВЛЕНИЕ КЛАВИАТУРЫ!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Мгновенное обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 **Клавиатуры обновлены напрямую из БД!**\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ instant_refresh ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при мгновенном обновлении: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при мгновенном обновлении: {e}")

    @dp.message_handler(Command('force_refresh_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def force_refresh_seasons_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры сезонов в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard, clear_season_keyboard_cache
            
            logger.info("=== НАЧАЛО force_refresh_seasons ===")
            
            # Очищаем кэш для всех проектов
            logger.info("Очищаем кэш для всех проектов")
            clear_season_keyboard_cache()
            
            # Создаем обновленные клавиатуры
            logger.info("Создаем обновленные клавиатуры")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1  # минус кнопка "Orqaga qaytish"
            golden_seasons = len(golden_keyboard.keyboard) - 1   # минус кнопка "Orqaga qaytish"
            
            response = f"🔄 **Клавиатуры сезонов обновлены!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 Теперь пользователи увидят актуальный список сезонов.\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ force_refresh_seasons ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")

    @dp.message_handler(Command('list_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def list_seasons_command(message: types.Message):
        try:
            # Получаем сезоны с количеством видео для Centris Towers
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            # Получаем сезоны с количеством видео для Golden Lake
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            response = "📋 Список добавленных сезонов:\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
            
            if not centris_seasons and not golden_seasons:
                response += "Пока нет добавленных сезонов."
            
            await message.answer(response)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(Command('edit_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def edit_season_command(message: types.Message, state: FSMContext):
        try:
            # Получаем все сезоны с количеством видео
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            if not centris_seasons and not golden_seasons:
                await message.answer("Нет сезонов для редактирования.")
                return
            
            response = "📝 Выберите сезон для редактирования (введите ID):\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_season_id.state)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_season_id)
    async def process_season_id_for_edit(message: types.Message, state: FSMContext):
        try:
            season_id = int(message.text.strip())
            season_data = db.get_season_by_id(season_id)
            
            if not season_data:
                await message.answer("Сезон с таким ID не найден. Попробуйте снова:")
                return
            
            season_id, project, season_name = season_data
            videos = db.get_videos_with_ids_by_season(season_id)
            
            await state.update_data(season_id=season_id, project=project, season_name=season_name)
            
            response = f"📝 Редактирование сезона:\n"
            response += f"ID: {season_id}\n"
            response += f"Проект: {project}\n"
            response += f"Название: {season_name}\n"
            response += f"Количество видео: {len(videos)}\n\n"
            
            if videos:
                response += "Видео в сезоне:\n"
                for video_id, url, title, position in videos:
                    response += f"  ID {video_id}: {title} (позиция {position})\n"
            
            response += "\nВыберите действие:\n"
            response += "1. Изменить название сезона\n"
            response += "2. Редактировать видео\n"
            response += "3. Удалить отдельные видео\n"
            response += "4. Удалить весь сезон\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_action.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID сезона (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_action)
    async def process_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if action == "1":
            await message.answer("Введите новое название сезона:")
            await state.set_state(EditSeasonStates.waiting_for_new_name.state)
        elif action == "2":
            await message.answer("Введите ID видео для редактирования:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "3":
            await message.answer("Введите ID видео для удаления:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "4":
            # Подтверждение удаления сезона
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да, удалить", callback_data=f"confirm_delete_season_{season_id}"),
                InlineKeyboardButton("Отмена", callback_data="cancel_delete")
            )
            await message.answer("⚠️ Вы уверены, что хотите удалить весь сезон и все его видео?", reply_markup=kb)
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditSeasonStates.waiting_for_new_name)
    async def process_new_season_name(message: types.Message, state: FSMContext):
        new_name = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if db.update_season(season_id, new_name):
            await message.answer(f"✅ Название сезона успешно изменено на: {new_name}")
        else:
            await message.answer("❌ Ошибка при обновлении названия сезона.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_video_id)
    async def process_video_id_for_edit(message: types.Message, state: FSMContext):
        try:
            video_id = int(message.text.strip())
            video_data = db.get_video_by_id(video_id)
            
            if not video_data:
                await message.answer("Видео с таким ID не найдено. Попробуйте снова:")
                return
            
            video_id, season_id, url, title, position = video_data
            await state.update_data(video_id=video_id, season_id=season_id, url=url, title=title, position=position)
            
            response = f"📹 Редактирование видео:\n"
            response += f"ID: {video_id}\n"
            response += f"Название: {title}\n"
            response += f"Позиция: {position}\n"
            response += f"URL: {url}\n\n"
            response += "Выберите действие:\n"
            response += "1. Изменить URL\n"
            response += "2. Изменить название\n"
            response += "3. Изменить позицию\n"
            response += "4. Удалить видео\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID видео (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_video_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        
        if action == "1":
            await message.answer("Введите новый URL видео:")
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        elif action == "2":
            await message.answer("Введите новое название видео:")
            await state.set_state(EditVideoStates.waiting_for_new_title.state)
        elif action == "3":
            await message.answer("Введите новую позицию видео (число):")
            await state.set_state(EditVideoStates.waiting_for_new_position.state)
        elif action == "4":
            video_id = data.get("video_id")
            if db.delete_video(video_id):
                await message.answer("✅ Видео успешно удалено.")
            else:
                await message.answer("❌ Ошибка при удалении видео.")
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование видео отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_new_video_url(message: types.Message, state: FSMContext):
        new_url = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        title = data.get("title")
        position = data.get("position")
        
        if db.update_video(video_id, new_url, title, position):
            await message.answer(f"✅ URL видео успешно изменен на: {new_url}")
        else:
            await message.answer("❌ Ошибка при обновлении URL видео.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_new_title)
    async def process_new_video_title(message: types.Message, state: FSMContext):
        new_title = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        url = data.get("url")
        position = data.get("position")
        
        if db.update_video(video_id, url, new_title, position):
            await message.answer(f"✅ Название видео успешно изменено на: {new_title}")
        else:
            await message.answer("❌ Ошибка при обновлении названия видео.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_new_position)
    async def process_new_video_position(message: types.Message, state: FSMContext):
        try:
            new_position = int(message.text.strip())
            data = await state.get_data()
            video_id = data.get("video_id")
            url = data.get("url")
            title = data.get("title")
            
            if db.update_video(video_id, url, title, new_position):
                await message.answer(f"✅ Позиция видео успешно изменена на: {new_position}")
            else:
                await message.answer("❌ Ошибка при обновлении позиции видео.")
        except ValueError:
            await message.answer("Пожалуйста, введите корректную позицию (число):")
            return
        
        await state.finish()

    @dp.callback_query_handler(lambda c: c.data.startswith("confirm_delete_season_"))
    async def confirm_delete_season(callback_query: types.CallbackQuery):
        season_id = int(callback_query.data.replace("confirm_delete_season_", ""))
        
        if db.delete_season(season_id):
            await safe_edit_text(callback_query, "✅ Сезон и все его видео успешно удалены.")
        else:
            await safe_edit_text(callback_query, "❌ Ошибка при удалении сезона.")
        
        await callback_query.answer()

    @dp.callback_query_handler(lambda c: c.data == "cancel_delete")
    async def cancel_delete_season(callback_query: types.CallbackQuery):
        await safe_edit_text(callback_query, "❌ Удаление отменено.")
        await callback_query.answer()

    @dp.message_handler(Command('delete_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def delete_season_command(message: types.Message):
        try:
            # Парсим ID сезона из команды
            args = message.text.split()
            if len(args) != 2:
                await message.answer("Использование: /delete_season <ID_сезона>")
                return
            
            season_id = int(args[1])
            season_data = db.get_season_by_id(season_id)
            
            if not season_data:
                await message.answer("Сезон с таким ID не найден.")
                return
            
            season_id, project, season_name = season_data
            videos = db.get_videos_by_season(season_id)
            
            response = f"⚠️ Подтвердите удаление сезона:\n"
            response += f"ID: {season_id}\n"
            response += f"Проект: {project}\n"
            response += f"Название: {season_name}\n"
            response += f"Количество видео: {len(videos)}\n\n"
            response += "Все видео будут удалены безвозвратно!"
            
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да, удалить", callback_data=f"confirm_delete_season_{season_id}"),
                InlineKeyboardButton("Отмена", callback_data="cancel_delete")
            )
            
            await message.answer(response, reply_markup=kb)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID сезона (число).")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(Command('season_help'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def season_help_command(message: types.Message):
        help_text = """
📋 **Команды для управления сезонами:**

**Добавление:**
• `/add_season` - Добавить новый сезон
• `/list_seasons` - Показать все сезоны

**Редактирование:**
• `/edit_season` - Редактировать существующий сезон
  - Изменить название сезона
  - Редактировать видео (URL, название, позиция)
  - Удалить отдельные видео

**Удаление:**
• `/delete_season <ID>` - Удалить сезон по ID

**Утилиты:**
• `/migrate_old_seasons` - Перенести старые сезоны в базу данных
• `/fix_season_order` - Исправить порядок сезонов (Яқинлар I Ташриф будет последним)

**Примеры использования:**
1. Добавить сезон: `/add_season`
2. Посмотреть сезоны: `/list_seasons`
3. Редактировать сезон: `/edit_season` (затем выбрать ID)
4. Удалить сезон: `/delete_season 5`
5. Исправить порядок: `/fix_season_order`

⚠️ **Внимание:** Удаление сезона удаляет все его видео безвозвратно!

📝 **Особенности:**
• Сезон "Яқинлар I Ташриф Centris Towers" всегда будет последним в меню
• Новые сезоны добавляются в правильном порядке автоматически
        """
        await message.answer(help_text)

    @dp.message_handler(Command('migrate_old_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def migrate_old_seasons_command(message: types.Message):
        """Миграция старых сезонов в базу данных"""
        try:
            # Проверяем, есть ли уже сезоны в базе
            centris_seasons = db.get_seasons_by_project("centris")
            golden_seasons = db.get_seasons_by_project("golden")
            
            if centris_seasons or golden_seasons:
                await message.answer("Сезоны уже есть в базе данных. Миграция не требуется.")
                return
            
            # Добавляем старые сезоны Centris Towers
            old_centris_seasons = [
                ("centris", "Яқинлар 1.0 I I Иброҳим Мамасаидов", VIDEO_LIST_1, CAPTION_LIST_1),
                ("centris", "Яқинлар 2.0 I I Иброҳим Мамасаидов", VIDEO_LIST_2, CAPTION_LIST_2),
                ("centris", "Яқинлар 3.0 I I Иброҳим Мамасаидов", VIDEO_LIST_3, CAPTION_LIST_3),
                ("centris", "Яқинлар 4.0 I I Иброҳим Мамасаидов", VIDEO_LIST_4, CAPTION_LIST_4),
                ("centris", "Яқинлар 5.0 I I Иброҳим Мамасаидов", VIDEO_LIST_5, CAPTION_LIST_5),
                ("centris", "Яқинлар I Ташриф Centris Towers", VIDEO_LIST_6, CAPTION_LIST_6),
            ]
            
            # Добавляем старые сезоны Golden Lake
            old_golden_seasons = [
                ("golden", "Golden lake 1", VIDEO_LIST_GOLDEN_1, GOLDEN_LIST),
            ]
            
            migrated_count = 0
            
            # Мигрируем Centris Towers
            for project, season_name, video_list, caption_list in old_centris_seasons:
                if len(video_list) == len(caption_list):
                    db.add_season_with_videos(project, season_name, video_list, caption_list)
                    migrated_count += 1
            
            # Мигрируем Golden Lake
            for project, season_name, video_list, caption_list in old_golden_seasons:
                if len(video_list) == len(caption_list):
                    db.add_season_with_videos(project, season_name, video_list, caption_list)
                    migrated_count += 1
            
            await message.answer(f"✅ Миграция завершена! Добавлено {migrated_count} сезонов.")
            
        except Exception as e:
            await message.answer(f"❌ Ошибка при миграции: {e}")

    @dp.message_handler(Command('fix_season_order'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def fix_season_order_command(message: types.Message):
        """Исправить порядок сезонов, чтобы 'Яқинлар I Ташриф Centris Towers' был последним"""
        try:
            # Получаем все сезоны Centris Towers
            centris_seasons = db.get_seasons_by_project("centris")
            
            if not centris_seasons:
                await message.answer("Нет сезонов Centris Towers для исправления порядка.")
                return
            
            # Проверяем, есть ли сезон "Яқинлар I Ташриф Centris Towers"
            tour_season = None
            other_seasons = []
            
            for season_id, season_name in centris_seasons:
                if season_name == "Яқинлар I Ташриф Centris Towers":
                    tour_season = (season_id, season_name)
                else:
                    other_seasons.append((season_id, season_name))
            
            if not tour_season:
                await message.answer("Сезон 'Яқинлар I Ташриф Centris Towers' не найден в базе данных.")
                return
            
            # Удаляем сезон "Яқинлар I Ташриф Centris Towers" и добавляем его заново
            # Это обеспечит, что он будет последним по ID
            tour_season_id, tour_season_name = tour_season
            
            # Получаем видео этого сезона
            videos = db.get_videos_by_season(tour_season_id)
            if not videos:
                await message.answer("В сезоне 'Яқинлар I Ташриф Centris Towers' нет видео.")
                return
            
            # Сохраняем данные видео
            video_data = [(url, title, position) for url, title, position in videos]
            
            # Удаляем старый сезон (видео удалятся каскадно)
            if db.delete_season(tour_season_id):
                # Добавляем сезон заново
                urls = [data[0] for data in video_data]
                titles = [data[1] for data in video_data]
                db.add_season_with_videos("centris", tour_season_name, urls, titles)
                
                await message.answer("✅ Порядок сезонов исправлен! Сезон 'Яқинлар I Ташриф Centris Towers' теперь будет последним.")
            else:
                await message.answer("❌ Ошибка при исправлении порядка сезонов.")
                
        except Exception as e:
            await message.answer(f"❌ Ошибка при исправлении порядка сезонов: {e}")

    @dp.message_handler(commands=['fix_season_project'], user_id=ADMINS + [SUPER_ADMIN_ID])
    async def fix_season_project_command(message: types.Message):
        try:
            args = message.text.split()
            if len(args) != 3:
                await message.answer("Использование: /fix_season_project <season_id> <project>")
                return
            season_id = int(args[1])
            new_project = args[2]
            if db.update_season_project(season_id, new_project):
                await message.answer(f"Project сезона {season_id} успешно изменён на '{new_project}'")
            else:
                await message.answer("Ошибка при обновлении project сезона.")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(Command('force_update_keyboards'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def force_update_keyboards_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры без кэша
        """
        try:
            await message.answer("🔄 Принудительное обновление клавиатуры...")
            
            # Импортируем функцию напрямую из БД
            try:
                from db import db
                
                # Получаем сезоны напрямую из БД
                centris_seasons = db.get_seasons_by_project("centris")
                golden_seasons = db.get_seasons_by_project("golden")
                
                centris_count = len(centris_seasons)
                golden_count = len(golden_seasons)
                
                response = f"📊 **Данные из БД (без кэша):**\n\n"
                response += f"🏢 **Centris Towers**: {centris_count} сезонов\n"
                for season_id, season_name in centris_seasons:
                    response += f"   • {season_name} (ID: {season_id})\n"
                
                response += f"\n🏖️ **Golden Lake**: {golden_count} сезонов\n"
                for season_id, season_name in golden_seasons:
                    response += f"   • {season_name} (ID: {season_id})\n"
                
                await message.answer(response)
                
                # Теперь принудительно очищаем кэш
                try:
                    from handlers.users.video_selector import clear_season_keyboard_cache
                    clear_season_keyboard_cache()
                    await message.answer("✅ Кэш очищен! Теперь выберите проект в главном меню.")
                except Exception as e:
                    await message.answer(f"⚠️ Кэш не очищен: {e}")
                
            except Exception as e:
                await message.answer(f"❌ Ошибка при получении данных из БД: {e}")
                
        except Exception as e:
            await message.answer(f"❌ Общая ошибка: {e}")

    @dp.message_handler(Command('simple_cache_status'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def simple_cache_status_command(message: types.Message):
        """
        Простая команда для проверки состояния кэша
        """
        try:
            await message.answer("🔍 Проверяем состояние кэша...")
            
            # Проверяем, можем ли мы импортировать модуль
            try:
                from handlers.users.video_selector import _season_keyboard_cache, _cache_timestamp
                await message.answer("✅ Модуль video_selector импортирован успешно")
                
                if not _season_keyboard_cache:
                    await message.answer("📋 Кэш пуст - это хорошо!")
                else:
                    cache_size = len(_season_keyboard_cache)
                    await message.answer(f"📋 В кэше {cache_size} элементов")
                    
            except ImportError as e:
                await message.answer(f"❌ Ошибка импорта: {e}")
            except Exception as e:
                await message.answer(f"❌ Ошибка при проверке кэша: {e}")
                
        except Exception as e:
            await message.answer(f"❌ Общая ошибка: {e}")

    @dp.message_handler(Command('test_commands'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def test_commands_command(message: types.Message):
        """
        Простая тестовая команда для проверки работы
        """
        try:
            await message.answer("✅ Команды работают! Бот функционирует нормально.")
            logger.info("Тестовая команда выполнена успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка в тестовой команде: {e}")
            await message.answer(f"❌ Ошибка: {e}")

    @dp.message_handler(Command('instant_refresh'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def instant_refresh_command(message: types.Message):
        """
        Команда для мгновенного обновления клавиатуры в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard
            
            logger.info("=== НАЧАЛО instant_refresh ===")
            
            # Получаем свежие клавиатуры напрямую из БД (без кэша)
            logger.info("Получаем свежие клавиатуры напрямую из БД")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1
            golden_seasons = len(golden_keyboard.keyboard) - 1
            
            response = f"⚡ **МГНОВЕННОЕ ОБНОВЛЕНИЕ КЛАВИАТУРЫ!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Мгновенное обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 **Клавиатуры обновлены напрямую из БД!**\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ instant_refresh ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при мгновенном обновлении: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при мгновенном обновлении: {e}")

    @dp.message_handler(Command('force_refresh_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def force_refresh_seasons_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры сезонов в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard, clear_season_keyboard_cache
            
            logger.info("=== НАЧАЛО force_refresh_seasons ===")
            
            # Очищаем кэш для всех проектов
            logger.info("Очищаем кэш для всех проектов")
            clear_season_keyboard_cache()
            
            # Создаем обновленные клавиатуры
            logger.info("Создаем обновленные клавиатуры")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1  # минус кнопка "Orqaga qaytish"
            golden_seasons = len(golden_keyboard.keyboard) - 1   # минус кнопка "Orqaga qaytish"
            
            response = f"🔄 **Клавиатуры сезонов обновлены!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 Теперь пользователи увидят актуальный список сезонов.\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ force_refresh_seasons ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")

    @dp.message_handler(Command('list_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def list_seasons_command(message: types.Message):
        try:
            # Получаем сезоны с количеством видео для Centris Towers
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            # Получаем сезоны с количеством видео для Golden Lake
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            response = "📋 Список добавленных сезонов:\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
            
            if not centris_seasons and not golden_seasons:
                response += "Пока нет добавленных сезонов."
            
            await message.answer(response)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(Command('edit_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def edit_season_command(message: types.Message, state: FSMContext):
        try:
            # Получаем все сезоны с количеством видео
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            if not centris_seasons and not golden_seasons:
                await message.answer("Нет сезонов для редактирования.")
                return
            
            response = "📝 Выберите сезон для редактирования (введите ID):\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_season_id.state)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_season_id)
    async def process_season_id_for_edit(message: types.Message, state: FSMContext):
        try:
            season_id = int(message.text.strip())
            season_data = db.get_season_by_id(season_id)
            
            if not season_data:
                await message.answer("Сезон с таким ID не найден. Попробуйте снова:")
                return
            
            season_id, project, season_name = season_data
            videos = db.get_videos_with_ids_by_season(season_id)
            
            await state.update_data(season_id=season_id, project=project, season_name=season_name)
            
            response = f"📝 Редактирование сезона:\n"
            response += f"ID: {season_id}\n"
            response += f"Проект: {project}\n"
            response += f"Название: {season_name}\n"
            response += f"Количество видео: {len(videos)}\n\n"
            
            if videos:
                response += "Видео в сезоне:\n"
                for video_id, url, title, position in videos:
                    response += f"  ID {video_id}: {title} (позиция {position})\n"
            
            response += "\nВыберите действие:\n"
            response += "1. Изменить название сезона\n"
            response += "2. Редактировать видео\n"
            response += "3. Удалить отдельные видео\n"
            response += "4. Удалить весь сезон\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_action.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID сезона (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_action)
    async def process_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if action == "1":
            await message.answer("Введите новое название сезона:")
            await state.set_state(EditSeasonStates.waiting_for_new_name.state)
        elif action == "2":
            await message.answer("Введите ID видео для редактирования:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "3":
            await message.answer("Введите ID видео для удаления:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "4":
            # Подтверждение удаления сезона
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да, удалить", callback_data=f"confirm_delete_season_{season_id}"),
                InlineKeyboardButton("Отмена", callback_data="cancel_delete")
            )
            await message.answer("⚠️ Вы уверены, что хотите удалить весь сезон и все его видео?", reply_markup=kb)
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditSeasonStates.waiting_for_new_name)
    async def process_new_season_name(message: types.Message, state: FSMContext):
        new_name = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if db.update_season(season_id, new_name):
            await message.answer(f"✅ Название сезона успешно изменено на: {new_name}")
        else:
            await message.answer("❌ Ошибка при обновлении названия сезона.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_video_id)
    async def process_video_id_for_edit(message: types.Message, state: FSMContext):
        try:
            video_id = int(message.text.strip())
            video_data = db.get_video_by_id(video_id)
            
            if not video_data:
                await message.answer("Видео с таким ID не найдено. Попробуйте снова:")
                return
            
            video_id, season_id, url, title, position = video_data
            await state.update_data(video_id=video_id, season_id=season_id, url=url, title=title, position=position)
            
            response = f"📹 Редактирование видео:\n"
            response += f"ID: {video_id}\n"
            response += f"Название: {title}\n"
            response += f"Позиция: {position}\n"
            response += f"URL: {url}\n\n"
            response += "Выберите действие:\n"
            response += "1. Изменить URL\n"
            response += "2. Изменить название\n"
            response += "3. Изменить позицию\n"
            response += "4. Удалить видео\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID видео (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_video_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        
        if action == "1":
            await message.answer("Введите новый URL видео:")
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        elif action == "2":
            await message.answer("Введите новое название видео:")
            await state.set_state(EditVideoStates.waiting_for_new_title.state)
        elif action == "3":
            await message.answer("Введите новую позицию видео (число):")
            await state.set_state(EditVideoStates.waiting_for_new_position.state)
        elif action == "4":
            video_id = data.get("video_id")
            if db.delete_video(video_id):
                await message.answer("✅ Видео успешно удалено.")
            else:
                await message.answer("❌ Ошибка при удалении видео.")
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование видео отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_new_video_url(message: types.Message, state: FSMContext):
        new_url = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        title = data.get("title")
        position = data.get("position")
        
        if db.update_video(video_id, new_url, title, position):
            await message.answer(f"✅ URL видео успешно изменен на: {new_url}")
        else:
            await message.answer("❌ Ошибка при обновлении URL видео.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_new_title)
    async def process_new_video_title(message: types.Message, state: FSMContext):
        new_title = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        url = data.get("url")
        position = data.get("position")
        
        if db.update_video(video_id, url, new_title, position):
            await message.answer(f"✅ Название видео успешно изменено на: {new_title}")
        else:
            await message.answer("❌ Ошибка при обновлении названия видео.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_new_position)
    async def process_new_video_position(message: types.Message, state: FSMContext):
        try:
            new_position = int(message.text.strip())
            data = await state.get_data()
            video_id = data.get("video_id")
            url = data.get("url")
            title = data.get("title")
            
            if db.update_video(video_id, url, title, new_position):
                await message.answer(f"✅ Позиция видео успешно изменена на: {new_position}")
            else:
                await message.answer("❌ Ошибка при обновлении позиции видео.")
        except ValueError:
            await message.answer("Пожалуйста, введите корректную позицию (число):")
            return
        
        await state.finish()

    @dp.callback_query_handler(lambda c: c.data.startswith("confirm_delete_season_"))
    async def confirm_delete_season(callback_query: types.CallbackQuery):
        season_id = int(callback_query.data.replace("confirm_delete_season_", ""))
        
        if db.delete_season(season_id):
            await safe_edit_text(callback_query, "✅ Сезон и все его видео успешно удалены.")
        else:
            await safe_edit_text(callback_query, "❌ Ошибка при удалении сезона.")
        
        await callback_query.answer()

    @dp.callback_query_handler(lambda c: c.data == "cancel_delete")
    async def cancel_delete_season(callback_query: types.CallbackQuery):
        await safe_edit_text(callback_query, "❌ Удаление отменено.")
        await callback_query.answer()

    @dp.message_handler(Command('delete_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def delete_season_command(message: types.Message):
        try:
            # Парсим ID сезона из команды
            args = message.text.split()
            if len(args) != 2:
                await message.answer("Использование: /delete_season <ID_сезона>")
                return
            
            season_id = int(args[1])
            season_data = db.get_season_by_id(season_id)
            
            if not season_data:
                await message.answer("Сезон с таким ID не найден.")
                return
            
            season_id, project, season_name = season_data
            videos = db.get_videos_by_season(season_id)
            
            response = f"⚠️ Подтвердите удаление сезона:\n"
            response += f"ID: {season_id}\n"
            response += f"Проект: {project}\n"
            response += f"Название: {season_name}\n"
            response += f"Количество видео: {len(videos)}\n\n"
            response += "Все видео будут удалены безвозвратно!"
            
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да, удалить", callback_data=f"confirm_delete_season_{season_id}"),
                InlineKeyboardButton("Отмена", callback_data="cancel_delete")
            )
            
            await message.answer(response, reply_markup=kb)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID сезона (число).")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(Command('season_help'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def season_help_command(message: types.Message):
        help_text = """
📋 **Команды для управления сезонами:**

**Добавление:**
• `/add_season` - Добавить новый сезон
• `/list_seasons` - Показать все сезоны

**Редактирование:**
• `/edit_season` - Редактировать существующий сезон
  - Изменить название сезона
  - Редактировать видео (URL, название, позиция)
  - Удалить отдельные видео

**Удаление:**
• `/delete_season <ID>` - Удалить сезон по ID

**Утилиты:**
• `/migrate_old_seasons` - Перенести старые сезоны в базу данных
• `/fix_season_order` - Исправить порядок сезонов (Яқинлар I Ташриф будет последним)

**Примеры использования:**
1. Добавить сезон: `/add_season`
2. Посмотреть сезоны: `/list_seasons`
3. Редактировать сезон: `/edit_season` (затем выбрать ID)
4. Удалить сезон: `/delete_season 5`
5. Исправить порядок: `/fix_season_order`

⚠️ **Внимание:** Удаление сезона удаляет все его видео безвозвратно!

📝 **Особенности:**
• Сезон "Яқинлар I Ташриф Centris Towers" всегда будет последним в меню
• Новые сезоны добавляются в правильном порядке автоматически
        """
        await message.answer(help_text)

    @dp.message_handler(Command('migrate_old_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def migrate_old_seasons_command(message: types.Message):
        """Миграция старых сезонов в базу данных"""
        try:
            # Проверяем, есть ли уже сезоны в базе
            centris_seasons = db.get_seasons_by_project("centris")
            golden_seasons = db.get_seasons_by_project("golden")
            
            if centris_seasons or golden_seasons:
                await message.answer("Сезоны уже есть в базе данных. Миграция не требуется.")
                return
            
            # Добавляем старые сезоны Centris Towers
            old_centris_seasons = [
                ("centris", "Яқинлар 1.0 I I Иброҳим Мамасаидов", VIDEO_LIST_1, CAPTION_LIST_1),
                ("centris", "Яқинлар 2.0 I I Иброҳим Мамасаидов", VIDEO_LIST_2, CAPTION_LIST_2),
                ("centris", "Яқинлар 3.0 I I Иброҳим Мамасаидов", VIDEO_LIST_3, CAPTION_LIST_3),
                ("centris", "Яқинлар 4.0 I I Иброҳим Мамасаидов", VIDEO_LIST_4, CAPTION_LIST_4),
                ("centris", "Яқинлар 5.0 I I Иброҳим Мамасаидов", VIDEO_LIST_5, CAPTION_LIST_5),
                ("centris", "Яқинлар I Ташриф Centris Towers", VIDEO_LIST_6, CAPTION_LIST_6),
            ]
            
            # Добавляем старые сезоны Golden Lake
            old_golden_seasons = [
                ("golden", "Golden lake 1", VIDEO_LIST_GOLDEN_1, GOLDEN_LIST),
            ]
            
            migrated_count = 0
            
            # Мигрируем Centris Towers
            for project, season_name, video_list, caption_list in old_centris_seasons:
                if len(video_list) == len(caption_list):
                    db.add_season_with_videos(project, season_name, video_list, caption_list)
                    migrated_count += 1
            
            # Мигрируем Golden Lake
            for project, season_name, video_list, caption_list in old_golden_seasons:
                if len(video_list) == len(caption_list):
                    db.add_season_with_videos(project, season_name, video_list, caption_list)
                    migrated_count += 1
            
            await message.answer(f"✅ Миграция завершена! Добавлено {migrated_count} сезонов.")
            
        except Exception as e:
            await message.answer(f"❌ Ошибка при миграции: {e}")

    @dp.message_handler(Command('fix_season_order'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def fix_season_order_command(message: types.Message):
        """Исправить порядок сезонов, чтобы 'Яқинлар I Ташриф Centris Towers' был последним"""
        try:
            # Получаем все сезоны Centris Towers
            centris_seasons = db.get_seasons_by_project("centris")
            
            if not centris_seasons:
                await message.answer("Нет сезонов Centris Towers для исправления порядка.")
                return
            
            # Проверяем, есть ли сезон "Яқинлар I Ташриф Centris Towers"
            tour_season = None
            other_seasons = []
            
            for season_id, season_name in centris_seasons:
                if season_name == "Яқинлар I Ташриф Centris Towers":
                    tour_season = (season_id, season_name)
                else:
                    other_seasons.append((season_id, season_name))
            
            if not tour_season:
                await message.answer("Сезон 'Яқинлар I Ташриф Centris Towers' не найден в базе данных.")
                return
            
            # Удаляем сезон "Яқинлар I Ташриф Centris Towers" и добавляем его заново
            # Это обеспечит, что он будет последним по ID
            tour_season_id, tour_season_name = tour_season
            
            # Получаем видео этого сезона
            videos = db.get_videos_by_season(tour_season_id)
            if not videos:
                await message.answer("В сезоне 'Яқинлар I Ташриф Centris Towers' нет видео.")
                return
            
            # Сохраняем данные видео
            video_data = [(url, title, position) for url, title, position in videos]
            
            # Удаляем старый сезон (видео удалятся каскадно)
            if db.delete_season(tour_season_id):
                # Добавляем сезон заново
                urls = [data[0] for data in video_data]
                titles = [data[1] for data in video_data]
                db.add_season_with_videos("centris", tour_season_name, urls, titles)
                
                await message.answer("✅ Порядок сезонов исправлен! Сезон 'Яқинлар I Ташриф Centris Towers' теперь будет последним.")
            else:
                await message.answer("❌ Ошибка при исправлении порядка сезонов.")
                
        except Exception as e:
            await message.answer(f"❌ Ошибка при исправлении порядка сезонов: {e}")

    @dp.message_handler(commands=['fix_season_project'], user_id=ADMINS + [SUPER_ADMIN_ID])
    async def fix_season_project_command(message: types.Message):
        try:
            args = message.text.split()
            if len(args) != 3:
                await message.answer("Использование: /fix_season_project <season_id> <project>")
                return
            season_id = int(args[1])
            new_project = args[2]
            if db.update_season_project(season_id, new_project):
                await message.answer(f"Project сезона {season_id} успешно изменён на '{new_project}'")
            else:
                await message.answer("Ошибка при обновлении project сезона.")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(Command('force_update_keyboards'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def force_update_keyboards_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры без кэша
        """
        try:
            await message.answer("🔄 Принудительное обновление клавиатуры...")
            
            # Импортируем функцию напрямую из БД
            try:
                from db import db
                
                # Получаем сезоны напрямую из БД
                centris_seasons = db.get_seasons_by_project("centris")
                golden_seasons = db.get_seasons_by_project("golden")
                
                centris_count = len(centris_seasons)
                golden_count = len(golden_seasons)
                
                response = f"📊 **Данные из БД (без кэша):**\n\n"
                response += f"🏢 **Centris Towers**: {centris_count} сезонов\n"
                for season_id, season_name in centris_seasons:
                    response += f"   • {season_name} (ID: {season_id})\n"
                
                response += f"\n🏖️ **Golden Lake**: {golden_count} сезонов\n"
                for season_id, season_name in golden_seasons:
                    response += f"   • {season_name} (ID: {season_id})\n"
                
                await message.answer(response)
                
                # Теперь принудительно очищаем кэш
                try:
                    from handlers.users.video_selector import clear_season_keyboard_cache
                    clear_season_keyboard_cache()
                    await message.answer("✅ Кэш очищен! Теперь выберите проект в главном меню.")
                except Exception as e:
                    await message.answer(f"⚠️ Кэш не очищен: {e}")
                
            except Exception as e:
                await message.answer(f"❌ Ошибка при получении данных из БД: {e}")
                
        except Exception as e:
            await message.answer(f"❌ Общая ошибка: {e}")

    @dp.message_handler(Command('simple_cache_status'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def simple_cache_status_command(message: types.Message):
        """
        Простая команда для проверки состояния кэша
        """
        try:
            await message.answer("🔍 Проверяем состояние кэша...")
            
            # Проверяем, можем ли мы импортировать модуль
            try:
                from handlers.users.video_selector import _season_keyboard_cache, _cache_timestamp
                await message.answer("✅ Модуль video_selector импортирован успешно")
                
                if not _season_keyboard_cache:
                    await message.answer("📋 Кэш пуст - это хорошо!")
                else:
                    cache_size = len(_season_keyboard_cache)
                    await message.answer(f"📋 В кэше {cache_size} элементов")
                    
            except ImportError as e:
                await message.answer(f"❌ Ошибка импорта: {e}")
            except Exception as e:
                await message.answer(f"❌ Ошибка при проверке кэша: {e}")
                
        except Exception as e:
            await message.answer(f"❌ Общая ошибка: {e}")

    @dp.message_handler(Command('test_commands'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def test_commands_command(message: types.Message):
        """
        Простая тестовая команда для проверки работы
        """
        try:
            await message.answer("✅ Команды работают! Бот функционирует нормально.")
            logger.info("Тестовая команда выполнена успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка в тестовой команде: {e}")
            await message.answer(f"❌ Ошибка: {e}")

    @dp.message_handler(Command('instant_refresh'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def instant_refresh_command(message: types.Message):
        """
        Команда для мгновенного обновления клавиатуры в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard
            
            logger.info("=== НАЧАЛО instant_refresh ===")
            
            # Получаем свежие клавиатуры напрямую из БД (без кэша)
            logger.info("Получаем свежие клавиатуры напрямую из БД")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1
            golden_seasons = len(golden_keyboard.keyboard) - 1
            
            response = f"⚡ **МГНОВЕННОЕ ОБНОВЛЕНИЕ КЛАВИАТУРЫ!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Мгновенное обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 **Клавиатуры обновлены напрямую из БД!**\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ instant_refresh ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при мгновенном обновлении: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при мгновенном обновлении: {e}")

    @dp.message_handler(Command('force_refresh_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def force_refresh_seasons_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры сезонов в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard, clear_season_keyboard_cache
            
            logger.info("=== НАЧАЛО force_refresh_seasons ===")
            
            # Очищаем кэш для всех проектов
            logger.info("Очищаем кэш для всех проектов")
            clear_season_keyboard_cache()
            
            # Создаем обновленные клавиатуры
            logger.info("Создаем обновленные клавиатуры")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1  # минус кнопка "Orqaga qaytish"
            golden_seasons = len(golden_keyboard.keyboard) - 1   # минус кнопка "Orqaga qaytish"
            
            response = f"🔄 **Клавиатуры сезонов обновлены!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 Теперь пользователи увидят актуальный список сезонов.\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ force_refresh_seasons ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")

    @dp.message_handler(Command('list_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def list_seasons_command(message: types.Message):
        try:
            # Получаем сезоны с количеством видео для Centris Towers
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            # Получаем сезоны с количеством видео для Golden Lake
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            response = "📋 Список добавленных сезонов:\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
            
            if not centris_seasons and not golden_seasons:
                response += "Пока нет добавленных сезонов."
            
            await message.answer(response)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(Command('edit_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def edit_season_command(message: types.Message, state: FSMContext):
        try:
            # Получаем все сезоны с количеством видео
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            if not centris_seasons and not golden_seasons:
                await message.answer("Нет сезонов для редактирования.")
                return
            
            response = "📝 Выберите сезон для редактирования (введите ID):\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_season_id.state)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_season_id)
    async def process_season_id_for_edit(message: types.Message, state: FSMContext):
        try:
            season_id = int(message.text.strip())
            season_data = db.get_season_by_id(season_id)
            
            if not season_data:
                await message.answer("Сезон с таким ID не найден. Попробуйте снова:")
                return
            
            season_id, project, season_name = season_data
            videos = db.get_videos_with_ids_by_season(season_id)
            
            await state.update_data(season_id=season_id, project=project, season_name=season_name)
            
            response = f"📝 Редактирование сезона:\n"
            response += f"ID: {season_id}\n"
            response += f"Проект: {project}\n"
            response += f"Название: {season_name}\n"
            response += f"Количество видео: {len(videos)}\n\n"
            
            if videos:
                response += "Видео в сезоне:\n"
                for video_id, url, title, position in videos:
                    response += f"  ID {video_id}: {title} (позиция {position})\n"
            
            response += "\nВыберите действие:\n"
            response += "1. Изменить название сезона\n"
            response += "2. Редактировать видео\n"
            response += "3. Удалить отдельные видео\n"
            response += "4. Удалить весь сезон\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_action.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID сезона (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_action)
    async def process_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if action == "1":
            await message.answer("Введите новое название сезона:")
            await state.set_state(EditSeasonStates.waiting_for_new_name.state)
        elif action == "2":
            await message.answer("Введите ID видео для редактирования:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "3":
            await message.answer("Введите ID видео для удаления:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "4":
            # Подтверждение удаления сезона
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да, удалить", callback_data=f"confirm_delete_season_{season_id}"),
                InlineKeyboardButton("Отмена", callback_data="cancel_delete")
            )
            await message.answer("⚠️ Вы уверены, что хотите удалить весь сезон и все его видео?", reply_markup=kb)
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditSeasonStates.waiting_for_new_name)
    async def process_new_season_name(message: types.Message, state: FSMContext):
        new_name = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if db.update_season(season_id, new_name):
            await message.answer(f"✅ Название сезона успешно изменено на: {new_name}")
        else:
            await message.answer("❌ Ошибка при обновлении названия сезона.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_video_id)
    async def process_video_id_for_edit(message: types.Message, state: FSMContext):
        try:
            video_id = int(message.text.strip())
            video_data = db.get_video_by_id(video_id)
            
            if not video_data:
                await message.answer("Видео с таким ID не найдено. Попробуйте снова:")
                return
            
            video_id, season_id, url, title, position = video_data
            await state.update_data(video_id=video_id, season_id=season_id, url=url, title=title, position=position)
            
            response = f"📹 Редактирование видео:\n"
            response += f"ID: {video_id}\n"
            response += f"Название: {title}\n"
            response += f"Позиция: {position}\n"
            response += f"URL: {url}\n\n"
            response += "Выберите действие:\n"
            response += "1. Изменить URL\n"
            response += "2. Изменить название\n"
            response += "3. Изменить позицию\n"
            response += "4. Удалить видео\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID видео (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_video_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        
        if action == "1":
            await message.answer("Введите новый URL видео:")
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        elif action == "2":
            await message.answer("Введите новое название видео:")
            await state.set_state(EditVideoStates.waiting_for_new_title.state)
        elif action == "3":
            await message.answer("Введите новую позицию видео (число):")
            await state.set_state(EditVideoStates.waiting_for_new_position.state)
        elif action == "4":
            video_id = data.get("video_id")
            if db.delete_video(video_id):
                await message.answer("✅ Видео успешно удалено.")
            else:
                await message.answer("❌ Ошибка при удалении видео.")
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование видео отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_new_video_url(message: types.Message, state: FSMContext):
        new_url = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        title = data.get("title")
        position = data.get("position")
        
        if db.update_video(video_id, new_url, title, position):
            await message.answer(f"✅ URL видео успешно изменен на: {new_url}")
        else:
            await message.answer("❌ Ошибка при обновлении URL видео.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_new_title)
    async def process_new_video_title(message: types.Message, state: FSMContext):
        new_title = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        url = data.get("url")
        position = data.get("position")
        
        if db.update_video(video_id, url, new_title, position):
            await message.answer(f"✅ Название видео успешно изменено на: {new_title}")
        else:
            await message.answer("❌ Ошибка при обновлении названия видео.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_new_position)
    async def process_new_video_position(message: types.Message, state: FSMContext):
        try:
            new_position = int(message.text.strip())
            data = await state.get_data()
            video_id = data.get("video_id")
            url = data.get("url")
            title = data.get("title")
            
            if db.update_video(video_id, url, title, new_position):
                await message.answer(f"✅ Позиция видео успешно изменена на: {new_position}")
            else:
                await message.answer("❌ Ошибка при обновлении позиции видео.")
        except ValueError:
            await message.answer("Пожалуйста, введите корректную позицию (число):")
            return
        
        await state.finish()

    @dp.callback_query_handler(lambda c: c.data.startswith("confirm_delete_season_"))
    async def confirm_delete_season(callback_query: types.CallbackQuery):
        season_id = int(callback_query.data.replace("confirm_delete_season_", ""))
        
        if db.delete_season(season_id):
            await safe_edit_text(callback_query, "✅ Сезон и все его видео успешно удалены.")
        else:
            await safe_edit_text(callback_query, "❌ Ошибка при удалении сезона.")
        
        await callback_query.answer()

    @dp.callback_query_handler(lambda c: c.data == "cancel_delete")
    async def cancel_delete_season(callback_query: types.CallbackQuery):
        await safe_edit_text(callback_query, "❌ Удаление отменено.")
        await callback_query.answer()

    @dp.message_handler(Command('delete_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def delete_season_command(message: types.Message):
        try:
            # Парсим ID сезона из команды
            args = message.text.split()
            if len(args) != 2:
                await message.answer("Использование: /delete_season <ID_сезона>")
                return
            
            season_id = int(args[1])
            season_data = db.get_season_by_id(season_id)
            
            if not season_data:
                await message.answer("Сезон с таким ID не найден.")
                return
            
            season_id, project, season_name = season_data
            videos = db.get_videos_by_season(season_id)
            
            response = f"⚠️ Подтвердите удаление сезона:\n"
            response += f"ID: {season_id}\n"
            response += f"Проект: {project}\n"
            response += f"Название: {season_name}\n"
            response += f"Количество видео: {len(videos)}\n\n"
            response += "Все видео будут удалены безвозвратно!"
            
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да, удалить", callback_data=f"confirm_delete_season_{season_id}"),
                InlineKeyboardButton("Отмена", callback_data="cancel_delete")
            )
            
            await message.answer(response, reply_markup=kb)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID сезона (число).")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(Command('season_help'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def season_help_command(message: types.Message):
        help_text = """
📋 **Команды для управления сезонами:**

**Добавление:**
• `/add_season` - Добавить новый сезон
• `/list_seasons` - Показать все сезоны

**Редактирование:**
• `/edit_season` - Редактировать существующий сезон
  - Изменить название сезона
  - Редактировать видео (URL, название, позиция)
  - Удалить отдельные видео

**Удаление:**
• `/delete_season <ID>` - Удалить сезон по ID

**Утилиты:**
• `/migrate_old_seasons` - Перенести старые сезоны в базу данных
• `/fix_season_order` - Исправить порядок сезонов (Яқинлар I Ташриф будет последним)

**Примеры использования:**
1. Добавить сезон: `/add_season`
2. Посмотреть сезоны: `/list_seasons`
3. Редактировать сезон: `/edit_season` (затем выбрать ID)
4. Удалить сезон: `/delete_season 5`
5. Исправить порядок: `/fix_season_order`

⚠️ **Внимание:** Удаление сезона удаляет все его видео безвозвратно!

📝 **Особенности:**
• Сезон "Яқинлар I Ташриф Centris Towers" всегда будет последним в меню
• Новые сезоны добавляются в правильном порядке автоматически
        """
        await message.answer(help_text)

    @dp.message_handler(Command('migrate_old_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def migrate_old_seasons_command(message: types.Message):
        """Миграция старых сезонов в базу данных"""
        try:
            # Проверяем, есть ли уже сезоны в базе
            centris_seasons = db.get_seasons_by_project("centris")
            golden_seasons = db.get_seasons_by_project("golden")
            
            if centris_seasons or golden_seasons:
                await message.answer("Сезоны уже есть в базе данных. Миграция не требуется.")
                return
            
            # Добавляем старые сезоны Centris Towers
            old_centris_seasons = [
                ("centris", "Яқинлар 1.0 I I Иброҳим Мамасаидов", VIDEO_LIST_1, CAPTION_LIST_1),
                ("centris", "Яқинлар 2.0 I I Иброҳим Мамасаидов", VIDEO_LIST_2, CAPTION_LIST_2),
                ("centris", "Яқинлар 3.0 I I Иброҳим Мамасаидов", VIDEO_LIST_3, CAPTION_LIST_3),
                ("centris", "Яқинлар 4.0 I I Иброҳим Мамасаидов", VIDEO_LIST_4, CAPTION_LIST_4),
                ("centris", "Яқинлар 5.0 I I Иброҳим Мамасаидов", VIDEO_LIST_5, CAPTION_LIST_5),
                ("centris", "Яқинлар I Ташриф Centris Towers", VIDEO_LIST_6, CAPTION_LIST_6),
            ]
            
            # Добавляем старые сезоны Golden Lake
            old_golden_seasons = [
                ("golden", "Golden lake 1", VIDEO_LIST_GOLDEN_1, GOLDEN_LIST),
            ]
            
            migrated_count = 0
            
            # Мигрируем Centris Towers
            for project, season_name, video_list, caption_list in old_centris_seasons:
                if len(video_list) == len(caption_list):
                    db.add_season_with_videos(project, season_name, video_list, caption_list)
                    migrated_count += 1
            
            # Мигрируем Golden Lake
            for project, season_name, video_list, caption_list in old_golden_seasons:
                if len(video_list) == len(caption_list):
                    db.add_season_with_videos(project, season_name, video_list, caption_list)
                    migrated_count += 1
            
            await message.answer(f"✅ Миграция завершена! Добавлено {migrated_count} сезонов.")
            
        except Exception as e:
            await message.answer(f"❌ Ошибка при миграции: {e}")

    @dp.message_handler(Command('fix_season_order'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def fix_season_order_command(message: types.Message):
        """Исправить порядок сезонов, чтобы 'Яқинлар I Ташриф Centris Towers' был последним"""
        try:
            # Получаем все сезоны Centris Towers
            centris_seasons = db.get_seasons_by_project("centris")
            
            if not centris_seasons:
                await message.answer("Нет сезонов Centris Towers для исправления порядка.")
                return
            
            # Проверяем, есть ли сезон "Яқинлар I Ташриф Centris Towers"
            tour_season = None
            other_seasons = []
            
            for season_id, season_name in centris_seasons:
                if season_name == "Яқинлар I Ташриф Centris Towers":
                    tour_season = (season_id, season_name)
                else:
                    other_seasons.append((season_id, season_name))
            
            if not tour_season:
                await message.answer("Сезон 'Яқинлар I Ташриф Centris Towers' не найден в базе данных.")
                return
            
            # Удаляем сезон "Яқинлар I Ташриф Centris Towers" и добавляем его заново
            # Это обеспечит, что он будет последним по ID
            tour_season_id, tour_season_name = tour_season
            
            # Получаем видео этого сезона
            videos = db.get_videos_by_season(tour_season_id)
            if not videos:
                await message.answer("В сезоне 'Яқинлар I Ташриф Centris Towers' нет видео.")
                return
            
            # Сохраняем данные видео
            video_data = [(url, title, position) for url, title, position in videos]
            
            # Удаляем старый сезон (видео удалятся каскадно)
            if db.delete_season(tour_season_id):
                # Добавляем сезон заново
                urls = [data[0] for data in video_data]
                titles = [data[1] for data in video_data]
                db.add_season_with_videos("centris", tour_season_name, urls, titles)
                
                await message.answer("✅ Порядок сезонов исправлен! Сезон 'Яқинлар I Ташриф Centris Towers' теперь будет последним.")
            else:
                await message.answer("❌ Ошибка при исправлении порядка сезонов.")
                
        except Exception as e:
            await message.answer(f"❌ Ошибка при исправлении порядка сезонов: {e}")

    @dp.message_handler(commands=['fix_season_project'], user_id=ADMINS + [SUPER_ADMIN_ID])
    async def fix_season_project_command(message: types.Message):
        try:
            args = message.text.split()
            if len(args) != 3:
                await message.answer("Использование: /fix_season_project <season_id> <project>")
                return
            season_id = int(args[1])
            new_project = args[2]
            if db.update_season_project(season_id, new_project):
                await message.answer(f"Project сезона {season_id} успешно изменён на '{new_project}'")
            else:
                await message.answer("Ошибка при обновлении project сезона.")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(Command('force_update_keyboards'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def force_update_keyboards_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры без кэша
        """
        try:
            await message.answer("🔄 Принудительное обновление клавиатуры...")
            
            # Импортируем функцию напрямую из БД
            try:
                from db import db
                
                # Получаем сезоны напрямую из БД
                centris_seasons = db.get_seasons_by_project("centris")
                golden_seasons = db.get_seasons_by_project("golden")
                
                centris_count = len(centris_seasons)
                golden_count = len(golden_seasons)
                
                response = f"📊 **Данные из БД (без кэша):**\n\n"
                response += f"🏢 **Centris Towers**: {centris_count} сезонов\n"
                for season_id, season_name in centris_seasons:
                    response += f"   • {season_name} (ID: {season_id})\n"
                
                response += f"\n🏖️ **Golden Lake**: {golden_count} сезонов\n"
                for season_id, season_name in golden_seasons:
                    response += f"   • {season_name} (ID: {season_id})\n"
                
                await message.answer(response)
                
                # Теперь принудительно очищаем кэш
                try:
                    from handlers.users.video_selector import clear_season_keyboard_cache
                    clear_season_keyboard_cache()
                    await message.answer("✅ Кэш очищен! Теперь выберите проект в главном меню.")
                except Exception as e:
                    await message.answer(f"⚠️ Кэш не очищен: {e}")
                
            except Exception as e:
                await message.answer(f"❌ Ошибка при получении данных из БД: {e}")
                
        except Exception as e:
            await message.answer(f"❌ Общая ошибка: {e}")

    @dp.message_handler(Command('simple_cache_status'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def simple_cache_status_command(message: types.Message):
        """
        Простая команда для проверки состояния кэша
        """
        try:
            await message.answer("🔍 Проверяем состояние кэша...")
            
            # Проверяем, можем ли мы импортировать модуль
            try:
                from handlers.users.video_selector import _season_keyboard_cache, _cache_timestamp
                await message.answer("✅ Модуль video_selector импортирован успешно")
                
                if not _season_keyboard_cache:
                    await message.answer("📋 Кэш пуст - это хорошо!")
                else:
                    cache_size = len(_season_keyboard_cache)
                    await message.answer(f"📋 В кэше {cache_size} элементов")
                    
            except ImportError as e:
                await message.answer(f"❌ Ошибка импорта: {e}")
            except Exception as e:
                await message.answer(f"❌ Ошибка при проверке кэша: {e}")
                
        except Exception as e:
            await message.answer(f"❌ Общая ошибка: {e}")

    @dp.message_handler(Command('test_commands'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def test_commands_command(message: types.Message):
        """
        Простая тестовая команда для проверки работы
        """
        try:
            await message.answer("✅ Команды работают! Бот функционирует нормально.")
            logger.info("Тестовая команда выполнена успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка в тестовой команде: {e}")
            await message.answer(f"❌ Ошибка: {e}")

    @dp.message_handler(Command('instant_refresh'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def instant_refresh_command(message: types.Message):
        """
        Команда для мгновенного обновления клавиатуры в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard
            
            logger.info("=== НАЧАЛО instant_refresh ===")
            
            # Получаем свежие клавиатуры напрямую из БД (без кэша)
            logger.info("Получаем свежие клавиатуры напрямую из БД")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1
            golden_seasons = len(golden_keyboard.keyboard) - 1
            
            response = f"⚡ **МГНОВЕННОЕ ОБНОВЛЕНИЕ КЛАВИАТУРЫ!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Мгновенное обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 **Клавиатуры обновлены напрямую из БД!**\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ instant_refresh ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при мгновенном обновлении: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при мгновенном обновлении: {e}")

    @dp.message_handler(Command('force_refresh_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def force_refresh_seasons_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры сезонов в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard, clear_season_keyboard_cache
            
            logger.info("=== НАЧАЛО force_refresh_seasons ===")
            
            # Очищаем кэш для всех проектов
            logger.info("Очищаем кэш для всех проектов")
            clear_season_keyboard_cache()
            
            # Создаем обновленные клавиатуры
            logger.info("Создаем обновленные клавиатуры")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1  # минус кнопка "Orqaga qaytish"
            golden_seasons = len(golden_keyboard.keyboard) - 1   # минус кнопка "Orqaga qaytish"
            
            response = f"🔄 **Клавиатуры сезонов обновлены!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 Теперь пользователи увидят актуальный список сезонов.\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ force_refresh_seasons ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")

    @dp.message_handler(Command('list_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def list_seasons_command(message: types.Message):
        try:
            # Получаем сезоны с количеством видео для Centris Towers
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            # Получаем сезоны с количеством видео для Golden Lake
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            response = "📋 Список добавленных сезонов:\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
            
            if not centris_seasons and not golden_seasons:
                response += "Пока нет добавленных сезонов."
            
            await message.answer(response)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(Command('edit_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def edit_season_command(message: types.Message, state: FSMContext):
        try:
            # Получаем все сезоны с количеством видео
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            if not centris_seasons and not golden_seasons:
                await message.answer("Нет сезонов для редактирования.")
                return
            
            response = "📝 Выберите сезон для редактирования (введите ID):\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_season_id.state)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_season_id)
    async def process_season_id_for_edit(message: types.Message, state: FSMContext):
        try:
            season_id = int(message.text.strip())
            season_data = db.get_season_by_id(season_id)
            
            if not season_data:
                await message.answer("Сезон с таким ID не найден. Попробуйте снова:")
                return
            
            season_id, project, season_name = season_data
            videos = db.get_videos_with_ids_by_season(season_id)
            
            await state.update_data(season_id=season_id, project=project, season_name=season_name)
            
            response = f"📝 Редактирование сезона:\n"
            response += f"ID: {season_id}\n"
            response += f"Проект: {project}\n"
            response += f"Название: {season_name}\n"
            response += f"Количество видео: {len(videos)}\n\n"
            
            if videos:
                response += "Видео в сезоне:\n"
                for video_id, url, title, position in videos:
                    response += f"  ID {video_id}: {title} (позиция {position})\n"
            
            response += "\nВыберите действие:\n"
            response += "1. Изменить название сезона\n"
            response += "2. Редактировать видео\n"
            response += "3. Удалить отдельные видео\n"
            response += "4. Удалить весь сезон\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_action.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID сезона (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_action)
    async def process_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if action == "1":
            await message.answer("Введите новое название сезона:")
            await state.set_state(EditSeasonStates.waiting_for_new_name.state)
        elif action == "2":
            await message.answer("Введите ID видео для редактирования:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "3":
            await message.answer("Введите ID видео для удаления:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "4":
            # Подтверждение удаления сезона
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да, удалить", callback_data=f"confirm_delete_season_{season_id}"),
                InlineKeyboardButton("Отмена", callback_data="cancel_delete")
            )
            await message.answer("⚠️ Вы уверены, что хотите удалить весь сезон и все его видео?", reply_markup=kb)
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditSeasonStates.waiting_for_new_name)
    async def process_new_season_name(message: types.Message, state: FSMContext):
        new_name = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if db.update_season(season_id, new_name):
            await message.answer(f"✅ Название сезона успешно изменено на: {new_name}")
        else:
            await message.answer("❌ Ошибка при обновлении названия сезона.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_video_id)
    async def process_video_id_for_edit(message: types.Message, state: FSMContext):
        try:
            video_id = int(message.text.strip())
            video_data = db.get_video_by_id(video_id)
            
            if not video_data:
                await message.answer("Видео с таким ID не найдено. Попробуйте снова:")
                return
            
            video_id, season_id, url, title, position = video_data
            await state.update_data(video_id=video_id, season_id=season_id, url=url, title=title, position=position)
            
            response = f"📹 Редактирование видео:\n"
            response += f"ID: {video_id}\n"
            response += f"Название: {title}\n"
            response += f"Позиция: {position}\n"
            response += f"URL: {url}\n\n"
            response += "Выберите действие:\n"
            response += "1. Изменить URL\n"
            response += "2. Изменить название\n"
            response += "3. Изменить позицию\n"
            response += "4. Удалить видео\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID видео (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_video_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        
        if action == "1":
            await message.answer("Введите новый URL видео:")
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        elif action == "2":
            await message.answer("Введите новое название видео:")
            await state.set_state(EditVideoStates.waiting_for_new_title.state)
        elif action == "3":
            await message.answer("Введите новую позицию видео (число):")
            await state.set_state(EditVideoStates.waiting_for_new_position.state)
        elif action == "4":
            video_id = data.get("video_id")
            if db.delete_video(video_id):
                await message.answer("✅ Видео успешно удалено.")
            else:
                await message.answer("❌ Ошибка при удалении видео.")
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование видео отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_new_video_url(message: types.Message, state: FSMContext):
        new_url = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        title = data.get("title")
        position = data.get("position")
        
        if db.update_video(video_id, new_url, title, position):
            await message.answer(f"✅ URL видео успешно изменен на: {new_url}")
        else:
            await message.answer("❌ Ошибка при обновлении URL видео.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_new_title)
    async def process_new_video_title(message: types.Message, state: FSMContext):
        new_title = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        url = data.get("url")
        position = data.get("position")
        
        if db.update_video(video_id, url, new_title, position):
            await message.answer(f"✅ Название видео успешно изменено на: {new_title}")
        else:
            await message.answer("❌ Ошибка при обновлении названия видео.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_new_position)
    async def process_new_video_position(message: types.Message, state: FSMContext):
        try:
            new_position = int(message.text.strip())
            data = await state.get_data()
            video_id = data.get("video_id")
            url = data.get("url")
            title = data.get("title")
            
            if db.update_video(video_id, url, title, new_position):
                await message.answer(f"✅ Позиция видео успешно изменена на: {new_position}")
            else:
                await message.answer("❌ Ошибка при обновлении позиции видео.")
        except ValueError:
            await message.answer("Пожалуйста, введите корректную позицию (число):")
            return
        
        await state.finish()

    @dp.callback_query_handler(lambda c: c.data.startswith("confirm_delete_season_"))
    async def confirm_delete_season(callback_query: types.CallbackQuery):
        season_id = int(callback_query.data.replace("confirm_delete_season_", ""))
        
        if db.delete_season(season_id):
            await safe_edit_text(callback_query, "✅ Сезон и все его видео успешно удалены.")
        else:
            await safe_edit_text(callback_query, "❌ Ошибка при удалении сезона.")
        
        await callback_query.answer()

    @dp.callback_query_handler(lambda c: c.data == "cancel_delete")
    async def cancel_delete_season(callback_query: types.CallbackQuery):
        await safe_edit_text(callback_query, "❌ Удаление отменено.")
        await callback_query.answer()

    @dp.message_handler(Command('delete_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def delete_season_command(message: types.Message):
        try:
            # Парсим ID сезона из команды
            args = message.text.split()
            if len(args) != 2:
                await message.answer("Использование: /delete_season <ID_сезона>")
                return
            
            season_id = int(args[1])
            season_data = db.get_season_by_id(season_id)
            
            if not season_data:
                await message.answer("Сезон с таким ID не найден.")
                return
            
            season_id, project, season_name = season_data
            videos = db.get_videos_by_season(season_id)
            
            response = f"⚠️ Подтвердите удаление сезона:\n"
            response += f"ID: {season_id}\n"
            response += f"Проект: {project}\n"
            response += f"Название: {season_name}\n"
            response += f"Количество видео: {len(videos)}\n\n"
            response += "Все видео будут удалены безвозвратно!"
            
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да, удалить", callback_data=f"confirm_delete_season_{season_id}"),
                InlineKeyboardButton("Отмена", callback_data="cancel_delete")
            )
            
            await message.answer(response, reply_markup=kb)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID сезона (число).")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(Command('season_help'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def season_help_command(message: types.Message):
        help_text = """
📋 **Команды для управления сезонами:**

**Добавление:**
• `/add_season` - Добавить новый сезон
• `/list_seasons` - Показать все сезоны

**Редактирование:**
• `/edit_season` - Редактировать существующий сезон
  - Изменить название сезона
  - Редактировать видео (URL, название, позиция)
  - Удалить отдельные видео

**Удаление:**
• `/delete_season <ID>` - Удалить сезон по ID

**Утилиты:**
• `/migrate_old_seasons` - Перенести старые сезоны в базу данных
• `/fix_season_order` - Исправить порядок сезонов (Яқинлар I Ташриф будет последним)

**Примеры использования:**
1. Добавить сезон: `/add_season`
2. Посмотреть сезоны: `/list_seasons`
3. Редактировать сезон: `/edit_season` (затем выбрать ID)
4. Удалить сезон: `/delete_season 5`
5. Исправить порядок: `/fix_season_order`

⚠️ **Внимание:** Удаление сезона удаляет все его видео безвозвратно!

📝 **Особенности:**
• Сезон "Яқинлар I Ташриф Centris Towers" всегда будет последним в меню
• Новые сезоны добавляются в правильном порядке автоматически
        """
        await message.answer(help_text)

    @dp.message_handler(Command('migrate_old_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def migrate_old_seasons_command(message: types.Message):
        """Миграция старых сезонов в базу данных"""
        try:
            # Проверяем, есть ли уже сезоны в базе
            centris_seasons = db.get_seasons_by_project("centris")
            golden_seasons = db.get_seasons_by_project("golden")
            
            if centris_seasons or golden_seasons:
                await message.answer("Сезоны уже есть в базе данных. Миграция не требуется.")
                return
            
            # Добавляем старые сезоны Centris Towers
            old_centris_seasons = [
                ("centris", "Яқинлар 1.0 I I Иброҳим Мамасаидов", VIDEO_LIST_1, CAPTION_LIST_1),
                ("centris", "Яқинлар 2.0 I I Иброҳим Мамасаидов", VIDEO_LIST_2, CAPTION_LIST_2),
                ("centris", "Яқинлар 3.0 I I Иброҳим Мамасаидов", VIDEO_LIST_3, CAPTION_LIST_3),
                ("centris", "Яқинлар 4.0 I I Иброҳим Мамасаидов", VIDEO_LIST_4, CAPTION_LIST_4),
                ("centris", "Яқинлар 5.0 I I Иброҳим Мамасаидов", VIDEO_LIST_5, CAPTION_LIST_5),
                ("centris", "Яқинлар I Ташриф Centris Towers", VIDEO_LIST_6, CAPTION_LIST_6),
            ]
            
            # Добавляем старые сезоны Golden Lake
            old_golden_seasons = [
                ("golden", "Golden lake 1", VIDEO_LIST_GOLDEN_1, GOLDEN_LIST),
            ]
            
            migrated_count = 0
            
            # Мигрируем Centris Towers
            for project, season_name, video_list, caption_list in old_centris_seasons:
                if len(video_list) == len(caption_list):
                    db.add_season_with_videos(project, season_name, video_list, caption_list)
                    migrated_count += 1
            
            # Мигрируем Golden Lake
            for project, season_name, video_list, caption_list in old_golden_seasons:
                if len(video_list) == len(caption_list):
                    db.add_season_with_videos(project, season_name, video_list, caption_list)
                    migrated_count += 1
            
            await message.answer(f"✅ Миграция завершена! Добавлено {migrated_count} сезонов.")
            
        except Exception as e:
            await message.answer(f"❌ Ошибка при миграции: {e}")

    @dp.message_handler(Command('fix_season_order'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def fix_season_order_command(message: types.Message):
        """Исправить порядок сезонов, чтобы 'Яқинлар I Ташриф Centris Towers' был последним"""
        try:
            # Получаем все сезоны Centris Towers
            centris_seasons = db.get_seasons_by_project("centris")
            
            if not centris_seasons:
                await message.answer("Нет сезонов Centris Towers для исправления порядка.")
                return
            
            # Проверяем, есть ли сезон "Яқинлар I Ташриф Centris Towers"
            tour_season = None
            other_seasons = []
            
            for season_id, season_name in centris_seasons:
                if season_name == "Яқинлар I Ташриф Centris Towers":
                    tour_season = (season_id, season_name)
                else:
                    other_seasons.append((season_id, season_name))
            
            if not tour_season:
                await message.answer("Сезон 'Яқинлар I Ташриф Centris Towers' не найден в базе данных.")
                return
            
            # Удаляем сезон "Яқинлар I Ташриф Centris Towers" и добавляем его заново
            # Это обеспечит, что он будет последним по ID
            tour_season_id, tour_season_name = tour_season
            
            # Получаем видео этого сезона
            videos = db.get_videos_by_season(tour_season_id)
            if not videos:
                await message.answer("В сезоне 'Яқинлар I Ташриф Centris Towers' нет видео.")
                return
            
            # Сохраняем данные видео
            video_data = [(url, title, position) for url, title, position in videos]
            
            # Удаляем старый сезон (видео удалятся каскадно)
            if db.delete_season(tour_season_id):
                # Добавляем сезон заново
                urls = [data[0] for data in video_data]
                titles = [data[1] for data in video_data]
                db.add_season_with_videos("centris", tour_season_name, urls, titles)
                
                await message.answer("✅ Порядок сезонов исправлен! Сезон 'Яқинлар I Ташриф Centris Towers' теперь будет последним.")
            else:
                await message.answer("❌ Ошибка при исправлении порядка сезонов.")
                
        except Exception as e:
            await message.answer(f"❌ Ошибка при исправлении порядка сезонов: {e}")

    @dp.message_handler(commands=['fix_season_project'], user_id=ADMINS + [SUPER_ADMIN_ID])
    async def fix_season_project_command(message: types.Message):
        try:
            args = message.text.split()
            if len(args) != 3:
                await message.answer("Использование: /fix_season_project <season_id> <project>")
                return
            season_id = int(args[1])
            new_project = args[2]
            if db.update_season_project(season_id, new_project):
                await message.answer(f"Project сезона {season_id} успешно изменён на '{new_project}'")
            else:
                await message.answer("Ошибка при обновлении project сезона.")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(Command('force_update_keyboards'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def force_update_keyboards_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры без кэша
        """
        try:
            await message.answer("🔄 Принудительное обновление клавиатуры...")
            
            # Импортируем функцию напрямую из БД
            try:
                from db import db
                
                # Получаем сезоны напрямую из БД
                centris_seasons = db.get_seasons_by_project("centris")
                golden_seasons = db.get_seasons_by_project("golden")
                
                centris_count = len(centris_seasons)
                golden_count = len(golden_seasons)
                
                response = f"📊 **Данные из БД (без кэша):**\n\n"
                response += f"🏢 **Centris Towers**: {centris_count} сезонов\n"
                for season_id, season_name in centris_seasons:
                    response += f"   • {season_name} (ID: {season_id})\n"
                
                response += f"\n🏖️ **Golden Lake**: {golden_count} сезонов\n"
                for season_id, season_name in golden_seasons:
                    response += f"   • {season_name} (ID: {season_id})\n"
                
                await message.answer(response)
                
                # Теперь принудительно очищаем кэш
                try:
                    from handlers.users.video_selector import clear_season_keyboard_cache
                    clear_season_keyboard_cache()
                    await message.answer("✅ Кэш очищен! Теперь выберите проект в главном меню.")
                except Exception as e:
                    await message.answer(f"⚠️ Кэш не очищен: {e}")
                
            except Exception as e:
                await message.answer(f"❌ Ошибка при получении данных из БД: {e}")
                
        except Exception as e:
            await message.answer(f"❌ Общая ошибка: {e}")

    @dp.message_handler(Command('simple_cache_status'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def simple_cache_status_command(message: types.Message):
        """
        Простая команда для проверки состояния кэша
        """
        try:
            await message.answer("🔍 Проверяем состояние кэша...")
            
            # Проверяем, можем ли мы импортировать модуль
            try:
                from handlers.users.video_selector import _season_keyboard_cache, _cache_timestamp
                await message.answer("✅ Модуль video_selector импортирован успешно")
                
                if not _season_keyboard_cache:
                    await message.answer("📋 Кэш пуст - это хорошо!")
                else:
                    cache_size = len(_season_keyboard_cache)
                    await message.answer(f"📋 В кэше {cache_size} элементов")
                    
            except ImportError as e:
                await message.answer(f"❌ Ошибка импорта: {e}")
            except Exception as e:
                await message.answer(f"❌ Ошибка при проверке кэша: {e}")
                
        except Exception as e:
            await message.answer(f"❌ Общая ошибка: {e}")

    @dp.message_handler(Command('test_commands'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def test_commands_command(message: types.Message):
        """
        Простая тестовая команда для проверки работы
        """
        try:
            await message.answer("✅ Команды работают! Бот функционирует нормально.")
            logger.info("Тестовая команда выполнена успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка в тестовой команде: {e}")
            await message.answer(f"❌ Ошибка: {e}")

    @dp.message_handler(Command('instant_refresh'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def instant_refresh_command(message: types.Message):
        """
        Команда для мгновенного обновления клавиатуры в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard
            
            logger.info("=== НАЧАЛО instant_refresh ===")
            
            # Получаем свежие клавиатуры напрямую из БД (без кэша)
            logger.info("Получаем свежие клавиатуры напрямую из БД")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1
            golden_seasons = len(golden_keyboard.keyboard) - 1
            
            response = f"⚡ **МГНОВЕННОЕ ОБНОВЛЕНИЕ КЛАВИАТУРЫ!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Мгновенное обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 **Клавиатуры обновлены напрямую из БД!**\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ instant_refresh ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при мгновенном обновлении: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при мгновенном обновлении: {e}")

    @dp.message_handler(Command('force_refresh_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def force_refresh_seasons_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры сезонов в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard, clear_season_keyboard_cache
            
            logger.info("=== НАЧАЛО force_refresh_seasons ===")
            
            # Очищаем кэш для всех проектов
            logger.info("Очищаем кэш для всех проектов")
            clear_season_keyboard_cache()
            
            # Создаем обновленные клавиатуры
            logger.info("Создаем обновленные клавиатуры")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1  # минус кнопка "Orqaga qaytish"
            golden_seasons = len(golden_keyboard.keyboard) - 1   # минус кнопка "Orqaga qaytish"
            
            response = f"🔄 **Клавиатуры сезонов обновлены!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 Теперь пользователи увидят актуальный список сезонов.\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ force_refresh_seasons ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")

    @dp.message_handler(Command('list_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def list_seasons_command(message: types.Message):
        try:
            # Получаем сезоны с количеством видео для Centris Towers
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            # Получаем сезоны с количеством видео для Golden Lake
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            response = "📋 Список добавленных сезонов:\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
            
            if not centris_seasons and not golden_seasons:
                response += "Пока нет добавленных сезонов."
            
            await message.answer(response)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(Command('edit_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def edit_season_command(message: types.Message, state: FSMContext):
        try:
            # Получаем все сезоны с количеством видео
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            if not centris_seasons and not golden_seasons:
                await message.answer("Нет сезонов для редактирования.")
                return
            
            response = "📝 Выберите сезон для редактирования (введите ID):\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_season_id.state)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_season_id)
    async def process_season_id_for_edit(message: types.Message, state: FSMContext):
        try:
            season_id = int(message.text.strip())
            season_data = db.get_season_by_id(season_id)
            
            if not season_data:
                await message.answer("Сезон с таким ID не найден. Попробуйте снова:")
                return
            
            season_id, project, season_name = season_data
            videos = db.get_videos_with_ids_by_season(season_id)
            
            await state.update_data(season_id=season_id, project=project, season_name=season_name)
            
            response = f"📝 Редактирование сезона:\n"
            response += f"ID: {season_id}\n"
            response += f"Проект: {project}\n"
            response += f"Название: {season_name}\n"
            response += f"Количество видео: {len(videos)}\n\n"
            
            if videos:
                response += "Видео в сезоне:\n"
                for video_id, url, title, position in videos:
                    response += f"  ID {video_id}: {title} (позиция {position})\n"
            
            response += "\nВыберите действие:\n"
            response += "1. Изменить название сезона\n"
            response += "2. Редактировать видео\n"
            response += "3. Удалить отдельные видео\n"
            response += "4. Удалить весь сезон\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_action.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID сезона (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_action)
    async def process_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if action == "1":
            await message.answer("Введите новое название сезона:")
            await state.set_state(EditSeasonStates.waiting_for_new_name.state)
        elif action == "2":
            await message.answer("Введите ID видео для редактирования:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "3":
            await message.answer("Введите ID видео для удаления:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "4":
            # Подтверждение удаления сезона
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да, удалить", callback_data=f"confirm_delete_season_{season_id}"),
                InlineKeyboardButton("Отмена", callback_data="cancel_delete")
            )
            await message.answer("⚠️ Вы уверены, что хотите удалить весь сезон и все его видео?", reply_markup=kb)
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditSeasonStates.waiting_for_new_name)
    async def process_new_season_name(message: types.Message, state: FSMContext):
        new_name = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if db.update_season(season_id, new_name):
            await message.answer(f"✅ Название сезона успешно изменено на: {new_name}")
        else:
            await message.answer("❌ Ошибка при обновлении названия сезона.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_video_id)
    async def process_video_id_for_edit(message: types.Message, state: FSMContext):
        try:
            video_id = int(message.text.strip())
            video_data = db.get_video_by_id(video_id)
            
            if not video_data:
                await message.answer("Видео с таким ID не найдено. Попробуйте снова:")
                return
            
            video_id, season_id, url, title, position = video_data
            await state.update_data(video_id=video_id, season_id=season_id, url=url, title=title, position=position)
            
            response = f"📹 Редактирование видео:\n"
            response += f"ID: {video_id}\n"
            response += f"Название: {title}\n"
            response += f"Позиция: {position}\n"
            response += f"URL: {url}\n\n"
            response += "Выберите действие:\n"
            response += "1. Изменить URL\n"
            response += "2. Изменить название\n"
            response += "3. Изменить позицию\n"
            response += "4. Удалить видео\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID видео (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_video_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        
        if action == "1":
            await message.answer("Введите новый URL видео:")
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        elif action == "2":
            await message.answer("Введите новое название видео:")
            await state.set_state(EditVideoStates.waiting_for_new_title.state)
        elif action == "3":
            await message.answer("Введите новую позицию видео (число):")
            await state.set_state(EditVideoStates.waiting_for_new_position.state)
        elif action == "4":
            video_id = data.get("video_id")
            if db.delete_video(video_id):
                await message.answer("✅ Видео успешно удалено.")
            else:
                await message.answer("❌ Ошибка при удалении видео.")
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование видео отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_new_video_url(message: types.Message, state: FSMContext):
        new_url = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        title = data.get("title")
        position = data.get("position")
        
        if db.update_video(video_id, new_url, title, position):
            await message.answer(f"✅ URL видео успешно изменен на: {new_url}")
        else:
            await message.answer("❌ Ошибка при обновлении URL видео.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_new_title)
    async def process_new_video_title(message: types.Message, state: FSMContext):
        new_title = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        url = data.get("url")
        position = data.get("position")
        
        if db.update_video(video_id, url, new_title, position):
            await message.answer(f"✅ Название видео успешно изменено на: {new_title}")
        else:
            await message.answer("❌ Ошибка при обновлении названия видео.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_new_position)
    async def process_new_video_position(message: types.Message, state: FSMContext):
        try:
            new_position = int(message.text.strip())
            data = await state.get_data()
            video_id = data.get("video_id")
            url = data.get("url")
            title = data.get("title")
            
            if db.update_video(video_id, url, title, new_position):
                await message.answer(f"✅ Позиция видео успешно изменена на: {new_position}")
            else:
                await message.answer("❌ Ошибка при обновлении позиции видео.")
        except ValueError:
            await message.answer("Пожалуйста, введите корректную позицию (число):")
            return
        
        await state.finish()

    @dp.callback_query_handler(lambda c: c.data.startswith("confirm_delete_season_"))
    async def confirm_delete_season(callback_query: types.CallbackQuery):
        season_id = int(callback_query.data.replace("confirm_delete_season_", ""))
        
        if db.delete_season(season_id):
            await safe_edit_text(callback_query, "✅ Сезон и все его видео успешно удалены.")
        else:
            await safe_edit_text(callback_query, "❌ Ошибка при удалении сезона.")
        
        await callback_query.answer()

    @dp.callback_query_handler(lambda c: c.data == "cancel_delete")
    async def cancel_delete_season(callback_query: types.CallbackQuery):
        await safe_edit_text(callback_query, "❌ Удаление отменено.")
        await callback_query.answer()

    @dp.message_handler(Command('delete_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def delete_season_command(message: types.Message):
        try:
            # Парсим ID сезона из команды
            args = message.text.split()
            if len(args) != 2:
                await message.answer("Использование: /delete_season <ID_сезона>")
                return
            
            season_id = int(args[1])
            season_data = db.get_season_by_id(season_id)
            
            if not season_data:
                await message.answer("Сезон с таким ID не найден.")
                return
            
            season_id, project, season_name = season_data
            videos = db.get_videos_by_season(season_id)
            
            response = f"⚠️ Подтвердите удаление сезона:\n"
            response += f"ID: {season_id}\n"
            response += f"Проект: {project}\n"
            response += f"Название: {season_name}\n"
            response += f"Количество видео: {len(videos)}\n\n"
            response += "Все видео будут удалены безвозвратно!"
            
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да, удалить", callback_data=f"confirm_delete_season_{season_id}"),
                InlineKeyboardButton("Отмена", callback_data="cancel_delete")
            )
            
            await message.answer(response, reply_markup=kb)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID сезона (число).")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(Command('season_help'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def season_help_command(message: types.Message):
        help_text = """
📋 **Команды для управления сезонами:**

**Добавление:**
• `/add_season` - Добавить новый сезон
• `/list_seasons` - Показать все сезоны

**Редактирование:**
• `/edit_season` - Редактировать существующий сезон
  - Изменить название сезона
  - Редактировать видео (URL, название, позиция)
  - Удалить отдельные видео

**Удаление:**
• `/delete_season <ID>` - Удалить сезон по ID

**Утилиты:**
• `/migrate_old_seasons` - Перенести старые сезоны в базу данных
• `/fix_season_order` - Исправить порядок сезонов (Яқинлар I Ташриф будет последним)

**Примеры использования:**
1. Добавить сезон: `/add_season`
2. Посмотреть сезоны: `/list_seasons`
3. Редактировать сезон: `/edit_season` (затем выбрать ID)
4. Удалить сезон: `/delete_season 5`
5. Исправить порядок: `/fix_season_order`

⚠️ **Внимание:** Удаление сезона удаляет все его видео безвозвратно!

📝 **Особенности:**
• Сезон "Яқинлар I Ташриф Centris Towers" всегда будет последним в меню
• Новые сезоны добавляются в правильном порядке автоматически
        """
        await message.answer(help_text)

    @dp.message_handler(Command('migrate_old_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def migrate_old_seasons_command(message: types.Message):
        """Миграция старых сезонов в базу данных"""
        try:
            # Проверяем, есть ли уже сезоны в базе
            centris_seasons = db.get_seasons_by_project("centris")
            golden_seasons = db.get_seasons_by_project("golden")
            
            if centris_seasons or golden_seasons:
                await message.answer("Сезоны уже есть в базе данных. Миграция не требуется.")
                return
            
            # Добавляем старые сезоны Centris Towers
            old_centris_seasons = [
                ("centris", "Яқинлар 1.0 I I Иброҳим Мамасаидов", VIDEO_LIST_1, CAPTION_LIST_1),
                ("centris", "Яқинлар 2.0 I I Иброҳим Мамасаидов", VIDEO_LIST_2, CAPTION_LIST_2),
                ("centris", "Яқинлар 3.0 I I Иброҳим Мамасаидов", VIDEO_LIST_3, CAPTION_LIST_3),
                ("centris", "Яқинлар 4.0 I I Иброҳим Мамасаидов", VIDEO_LIST_4, CAPTION_LIST_4),
                ("centris", "Яқинлар 5.0 I I Иброҳим Мамасаидов", VIDEO_LIST_5, CAPTION_LIST_5),
                ("centris", "Яқинлар I Ташриф Centris Towers", VIDEO_LIST_6, CAPTION_LIST_6),
            ]
            
            # Добавляем старые сезоны Golden Lake
            old_golden_seasons = [
                ("golden", "Golden lake 1", VIDEO_LIST_GOLDEN_1, GOLDEN_LIST),
            ]
            
            migrated_count = 0
            
            # Мигрируем Centris Towers
            for project, season_name, video_list, caption_list in old_centris_seasons:
                if len(video_list) == len(caption_list):
                    db.add_season_with_videos(project, season_name, video_list, caption_list)
                    migrated_count += 1
            
            # Мигрируем Golden Lake
            for project, season_name, video_list, caption_list in old_golden_seasons:
                if len(video_list) == len(caption_list):
                    db.add_season_with_videos(project, season_name, video_list, caption_list)
                    migrated_count += 1
            
            await message.answer(f"✅ Миграция завершена! Добавлено {migrated_count} сезонов.")
            
        except Exception as e:
            await message.answer(f"❌ Ошибка при миграции: {e}")

    @dp.message_handler(Command('fix_season_order'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def fix_season_order_command(message: types.Message):
        """Исправить порядок сезонов, чтобы 'Яқинлар I Ташриф Centris Towers' был последним"""
        try:
            # Получаем все сезоны Centris Towers
            centris_seasons = db.get_seasons_by_project("centris")
            
            if not centris_seasons:
                await message.answer("Нет сезонов Centris Towers для исправления порядка.")
                return
            
            # Проверяем, есть ли сезон "Яқинлар I Ташриф Centris Towers"
            tour_season = None
            other_seasons = []
            
            for season_id, season_name in centris_seasons:
                if season_name == "Яқинлар I Ташриф Centris Towers":
                    tour_season = (season_id, season_name)
                else:
                    other_seasons.append((season_id, season_name))
            
            if not tour_season:
                await message.answer("Сезон 'Яқинлар I Ташриф Centris Towers' не найден в базе данных.")
                return
            
            # Удаляем сезон "Яқинлар I Ташриф Centris Towers" и добавляем его заново
            # Это обеспечит, что он будет последним по ID
            tour_season_id, tour_season_name = tour_season
            
            # Получаем видео этого сезона
            videos = db.get_videos_by_season(tour_season_id)
            if not videos:
                await message.answer("В сезоне 'Яқинлар I Ташриф Centris Towers' нет видео.")
                return
            
            # Сохраняем данные видео
            video_data = [(url, title, position) for url, title, position in videos]
            
            # Удаляем старый сезон (видео удалятся каскадно)
            if db.delete_season(tour_season_id):
                # Добавляем сезон заново
                urls = [data[0] for data in video_data]
                titles = [data[1] for data in video_data]
                db.add_season_with_videos("centris", tour_season_name, urls, titles)
                
                await message.answer("✅ Порядок сезонов исправлен! Сезон 'Яқинлар I Ташриф Centris Towers' теперь будет последним.")
            else:
                await message.answer("❌ Ошибка при исправлении порядка сезонов.")
                
        except Exception as e:
            await message.answer(f"❌ Ошибка при исправлении порядка сезонов: {e}")

    @dp.message_handler(commands=['fix_season_project'], user_id=ADMINS + [SUPER_ADMIN_ID])
    async def fix_season_project_command(message: types.Message):
        try:
            args = message.text.split()
            if len(args) != 3:
                await message.answer("Использование: /fix_season_project <season_id> <project>")
                return
            season_id = int(args[1])
            new_project = args[2]
            if db.update_season_project(season_id, new_project):
                await message.answer(f"Project сезона {season_id} успешно изменён на '{new_project}'")
            else:
                await message.answer("Ошибка при обновлении project сезона.")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(Command('force_update_keyboards'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def force_update_keyboards_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры без кэша
        """
        try:
            await message.answer("🔄 Принудительное обновление клавиатуры...")
            
            # Импортируем функцию напрямую из БД
            try:
                from db import db
                
                # Получаем сезоны напрямую из БД
                centris_seasons = db.get_seasons_by_project("centris")
                golden_seasons = db.get_seasons_by_project("golden")
                
                centris_count = len(centris_seasons)
                golden_count = len(golden_seasons)
                
                response = f"📊 **Данные из БД (без кэша):**\n\n"
                response += f"🏢 **Centris Towers**: {centris_count} сезонов\n"
                for season_id, season_name in centris_seasons:
                    response += f"   • {season_name} (ID: {season_id})\n"
                
                response += f"\n🏖️ **Golden Lake**: {golden_count} сезонов\n"
                for season_id, season_name in golden_seasons:
                    response += f"   • {season_name} (ID: {season_id})\n"
                
                await message.answer(response)
                
                # Теперь принудительно очищаем кэш
                try:
                    from handlers.users.video_selector import clear_season_keyboard_cache
                    clear_season_keyboard_cache()
                    await message.answer("✅ Кэш очищен! Теперь выберите проект в главном меню.")
                except Exception as e:
                    await message.answer(f"⚠️ Кэш не очищен: {e}")
                
            except Exception as e:
                await message.answer(f"❌ Ошибка при получении данных из БД: {e}")
                
        except Exception as e:
            await message.answer(f"❌ Общая ошибка: {e}")

    @dp.message_handler(Command('simple_cache_status'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def simple_cache_status_command(message: types.Message):
        """
        Простая команда для проверки состояния кэша
        """
        try:
            await message.answer("🔍 Проверяем состояние кэша...")
            
            # Проверяем, можем ли мы импортировать модуль
            try:
                from handlers.users.video_selector import _season_keyboard_cache, _cache_timestamp
                await message.answer("✅ Модуль video_selector импортирован успешно")
                
                if not _season_keyboard_cache:
                    await message.answer("📋 Кэш пуст - это хорошо!")
                else:
                    cache_size = len(_season_keyboard_cache)
                    await message.answer(f"📋 В кэше {cache_size} элементов")
                    
            except ImportError as e:
                await message.answer(f"❌ Ошибка импорта: {e}")
            except Exception as e:
                await message.answer(f"❌ Ошибка при проверке кэша: {e}")
                
        except Exception as e:
            await message.answer(f"❌ Общая ошибка: {e}")

    @dp.message_handler(Command('test_commands'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def test_commands_command(message: types.Message):
        """
        Простая тестовая команда для проверки работы
        """
        try:
            await message.answer("✅ Команды работают! Бот функционирует нормально.")
            logger.info("Тестовая команда выполнена успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка в тестовой команде: {e}")
            await message.answer(f"❌ Ошибка: {e}")

    @dp.message_handler(Command('instant_refresh'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def instant_refresh_command(message: types.Message):
        """
        Команда для мгновенного обновления клавиатуры в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard
            
            logger.info("=== НАЧАЛО instant_refresh ===")
            
            # Получаем свежие клавиатуры напрямую из БД (без кэша)
            logger.info("Получаем свежие клавиатуры напрямую из БД")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1
            golden_seasons = len(golden_keyboard.keyboard) - 1
            
            response = f"⚡ **МГНОВЕННОЕ ОБНОВЛЕНИЕ КЛАВИАТУРЫ!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Мгновенное обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 **Клавиатуры обновлены напрямую из БД!**\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ instant_refresh ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при мгновенном обновлении: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при мгновенном обновлении: {e}")

    @dp.message_handler(Command('force_refresh_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def force_refresh_seasons_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры сезонов в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard, clear_season_keyboard_cache
            
            logger.info("=== НАЧАЛО force_refresh_seasons ===")
            
            # Очищаем кэш для всех проектов
            logger.info("Очищаем кэш для всех проектов")
            clear_season_keyboard_cache()
            
            # Создаем обновленные клавиатуры
            logger.info("Создаем обновленные клавиатуры")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1  # минус кнопка "Orqaga qaytish"
            golden_seasons = len(golden_keyboard.keyboard) - 1   # минус кнопка "Orqaga qaytish"
            
            response = f"🔄 **Клавиатуры сезонов обновлены!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 Теперь пользователи увидят актуальный список сезонов.\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ force_refresh_seasons ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")

    @dp.message_handler(Command('list_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def list_seasons_command(message: types.Message):
        try:
            # Получаем сезоны с количеством видео для Centris Towers
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            # Получаем сезоны с количеством видео для Golden Lake
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            response = "📋 Список добавленных сезонов:\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
            
            if not centris_seasons and not golden_seasons:
                response += "Пока нет добавленных сезонов."
            
            await message.answer(response)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(Command('edit_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def edit_season_command(message: types.Message, state: FSMContext):
        try:
            # Получаем все сезоны с количеством видео
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            if not centris_seasons and not golden_seasons:
                await message.answer("Нет сезонов для редактирования.")
                return
            
            response = "📝 Выберите сезон для редактирования (введите ID):\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_season_id.state)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_season_id)
    async def process_season_id_for_edit(message: types.Message, state: FSMContext):
        try:
            season_id = int(message.text.strip())
            season_data = db.get_season_by_id(season_id)
            
            if not season_data:
                await message.answer("Сезон с таким ID не найден. Попробуйте снова:")
                return
            
            season_id, project, season_name = season_data
            videos = db.get_videos_with_ids_by_season(season_id)
            
            await state.update_data(season_id=season_id, project=project, season_name=season_name)
            
            response = f"📝 Редактирование сезона:\n"
            response += f"ID: {season_id}\n"
            response += f"Проект: {project}\n"
            response += f"Название: {season_name}\n"
            response += f"Количество видео: {len(videos)}\n\n"
            
            if videos:
                response += "Видео в сезоне:\n"
                for video_id, url, title, position in videos:
                    response += f"  ID {video_id}: {title} (позиция {position})\n"
            
            response += "\nВыберите действие:\n"
            response += "1. Изменить название сезона\n"
            response += "2. Редактировать видео\n"
            response += "3. Удалить отдельные видео\n"
            response += "4. Удалить весь сезон\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_action.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID сезона (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_action)
    async def process_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if action == "1":
            await message.answer("Введите новое название сезона:")
            await state.set_state(EditSeasonStates.waiting_for_new_name.state)
        elif action == "2":
            await message.answer("Введите ID видео для редактирования:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "3":
            await message.answer("Введите ID видео для удаления:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "4":
            # Подтверждение удаления сезона
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да, удалить", callback_data=f"confirm_delete_season_{season_id}"),
                InlineKeyboardButton("Отмена", callback_data="cancel_delete")
            )
            await message.answer("⚠️ Вы уверены, что хотите удалить весь сезон и все его видео?", reply_markup=kb)
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditSeasonStates.waiting_for_new_name)
    async def process_new_season_name(message: types.Message, state: FSMContext):
        new_name = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if db.update_season(season_id, new_name):
            await message.answer(f"✅ Название сезона успешно изменено на: {new_name}")
        else:
            await message.answer("❌ Ошибка при обновлении названия сезона.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_video_id)
    async def process_video_id_for_edit(message: types.Message, state: FSMContext):
        try:
            video_id = int(message.text.strip())
            video_data = db.get_video_by_id(video_id)
            
            if not video_data:
                await message.answer("Видео с таким ID не найдено. Попробуйте снова:")
                return
            
            video_id, season_id, url, title, position = video_data
            await state.update_data(video_id=video_id, season_id=season_id, url=url, title=title, position=position)
            
            response = f"📹 Редактирование видео:\n"
            response += f"ID: {video_id}\n"
            response += f"Название: {title}\n"
            response += f"Позиция: {position}\n"
            response += f"URL: {url}\n\n"
            response += "Выберите действие:\n"
            response += "1. Изменить URL\n"
            response += "2. Изменить название\n"
            response += "3. Изменить позицию\n"
            response += "4. Удалить видео\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID видео (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_video_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        
        if action == "1":
            await message.answer("Введите новый URL видео:")
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        elif action == "2":
            await message.answer("Введите новое название видео:")
            await state.set_state(EditVideoStates.waiting_for_new_title.state)
        elif action == "3":
            await message.answer("Введите новую позицию видео (число):")
            await state.set_state(EditVideoStates.waiting_for_new_position.state)
        elif action == "4":
            video_id = data.get("video_id")
            if db.delete_video(video_id):
                await message.answer("✅ Видео успешно удалено.")
            else:
                await message.answer("❌ Ошибка при удалении видео.")
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование видео отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_new_video_url(message: types.Message, state: FSMContext):
        new_url = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        title = data.get("title")
        position = data.get("position")
        
        if db.update_video(video_id, new_url, title, position):
            await message.answer(f"✅ URL видео успешно изменен на: {new_url}")
        else:
            await message.answer("❌ Ошибка при обновлении URL видео.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_new_title)
    async def process_new_video_title(message: types.Message, state: FSMContext):
        new_title = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        url = data.get("url")
        position = data.get("position")
        
        if db.update_video(video_id, url, new_title, position):
            await message.answer(f"✅ Название видео успешно изменено на: {new_title}")
        else:
            await message.answer("❌ Ошибка при обновлении названия видео.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_new_position)
    async def process_new_video_position(message: types.Message, state: FSMContext):
        try:
            new_position = int(message.text.strip())
            data = await state.get_data()
            video_id = data.get("video_id")
            url = data.get("url")
            title = data.get("title")
            
            if db.update_video(video_id, url, title, new_position):
                await message.answer(f"✅ Позиция видео успешно изменена на: {new_position}")
            else:
                await message.answer("❌ Ошибка при обновлении позиции видео.")
        except ValueError:
            await message.answer("Пожалуйста, введите корректную позицию (число):")
            return
        
        await state.finish()

    @dp.callback_query_handler(lambda c: c.data.startswith("confirm_delete_season_"))
    async def confirm_delete_season(callback_query: types.CallbackQuery):
        season_id = int(callback_query.data.replace("confirm_delete_season_", ""))
        
        if db.delete_season(season_id):
            await safe_edit_text(callback_query, "✅ Сезон и все его видео успешно удалены.")
        else:
            await safe_edit_text(callback_query, "❌ Ошибка при удалении сезона.")
        
        await callback_query.answer()

    @dp.callback_query_handler(lambda c: c.data == "cancel_delete")
    async def cancel_delete_season(callback_query: types.CallbackQuery):
        await safe_edit_text(callback_query, "❌ Удаление отменено.")
        await callback_query.answer()

    @dp.message_handler(Command('delete_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def delete_season_command(message: types.Message):
        try:
            # Парсим ID сезона из команды
            args = message.text.split()
            if len(args) != 2:
                await message.answer("Использование: /delete_season <ID_сезона>")
                return
            
            season_id = int(args[1])
            season_data = db.get_season_by_id(season_id)
            
            if not season_data:
                await message.answer("Сезон с таким ID не найден.")
                return
            
            season_id, project, season_name = season_data
            videos = db.get_videos_by_season(season_id)
            
            response = f"⚠️ Подтвердите удаление сезона:\n"
            response += f"ID: {season_id}\n"
            response += f"Проект: {project}\n"
            response += f"Название: {season_name}\n"
            response += f"Количество видео: {len(videos)}\n\n"
            response += "Все видео будут удалены безвозвратно!"
            
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да, удалить", callback_data=f"confirm_delete_season_{season_id}"),
                InlineKeyboardButton("Отмена", callback_data="cancel_delete")
            )
            
            await message.answer(response, reply_markup=kb)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID сезона (число).")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(Command('season_help'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def season_help_command(message: types.Message):
        help_text = """
📋 **Команды для управления сезонами:**

**Добавление:**
• `/add_season` - Добавить новый сезон
• `/list_seasons` - Показать все сезоны

**Редактирование:**
• `/edit_season` - Редактировать существующий сезон
  - Изменить название сезона
  - Редактировать видео (URL, название, позиция)
  - Удалить отдельные видео

**Удаление:**
• `/delete_season <ID>` - Удалить сезон по ID

**Утилиты:**
• `/migrate_old_seasons` - Перенести старые сезоны в базу данных
• `/fix_season_order` - Исправить порядок сезонов (Яқинлар I Ташриф будет последним)

**Примеры использования:**
1. Добавить сезон: `/add_season`
2. Посмотреть сезоны: `/list_seasons`
3. Редактировать сезон: `/edit_season` (затем выбрать ID)
4. Удалить сезон: `/delete_season 5`
5. Исправить порядок: `/fix_season_order`

⚠️ **Внимание:** Удаление сезона удаляет все его видео безвозвратно!

📝 **Особенности:**
• Сезон "Яқинлар I Ташриф Centris Towers" всегда будет последним в меню
• Новые сезоны добавляются в правильном порядке автоматически
        """
        await message.answer(help_text)

    @dp.message_handler(Command('migrate_old_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def migrate_old_seasons_command(message: types.Message):
        """Миграция старых сезонов в базу данных"""
        try:
            # Проверяем, есть ли уже сезоны в базе
            centris_seasons = db.get_seasons_by_project("centris")
            golden_seasons = db.get_seasons_by_project("golden")
            
            if centris_seasons or golden_seasons:
                await message.answer("Сезоны уже есть в базе данных. Миграция не требуется.")
                return
            
            # Добавляем старые сезоны Centris Towers
            old_centris_seasons = [
                ("centris", "Яқинлар 1.0 I I Иброҳим Мамасаидов", VIDEO_LIST_1, CAPTION_LIST_1),
                ("centris", "Яқинлар 2.0 I I Иброҳим Мамасаидов", VIDEO_LIST_2, CAPTION_LIST_2),
                ("centris", "Яқинлар 3.0 I I Иброҳим Мамасаидов", VIDEO_LIST_3, CAPTION_LIST_3),
                ("centris", "Яқинлар 4.0 I I Иброҳим Мамасаидов", VIDEO_LIST_4, CAPTION_LIST_4),
                ("centris", "Яқинлар 5.0 I I Иброҳим Мамасаидов", VIDEO_LIST_5, CAPTION_LIST_5),
                ("centris", "Яқинлар I Ташриф Centris Towers", VIDEO_LIST_6, CAPTION_LIST_6),
            ]
            
            # Добавляем старые сезоны Golden Lake
            old_golden_seasons = [
                ("golden", "Golden lake 1", VIDEO_LIST_GOLDEN_1, GOLDEN_LIST),
            ]
            
            migrated_count = 0
            
            # Мигрируем Centris Towers
            for project, season_name, video_list, caption_list in old_centris_seasons:
                if len(video_list) == len(caption_list):
                    db.add_season_with_videos(project, season_name, video_list, caption_list)
                    migrated_count += 1
            
            # Мигрируем Golden Lake
            for project, season_name, video_list, caption_list in old_golden_seasons:
                if len(video_list) == len(caption_list):
                    db.add_season_with_videos(project, season_name, video_list, caption_list)
                    migrated_count += 1
            
            await message.answer(f"✅ Миграция завершена! Добавлено {migrated_count} сезонов.")
            
        except Exception as e:
            await message.answer(f"❌ Ошибка при миграции: {e}")

    @dp.message_handler(Command('fix_season_order'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def fix_season_order_command(message: types.Message):
        """Исправить порядок сезонов, чтобы 'Яқинлар I Ташриф Centris Towers' был последним"""
        try:
            # Получаем все сезоны Centris Towers
            centris_seasons = db.get_seasons_by_project("centris")
            
            if not centris_seasons:
                await message.answer("Нет сезонов Centris Towers для исправления порядка.")
                return
            
            # Проверяем, есть ли сезон "Яқинлар I Ташриф Centris Towers"
            tour_season = None
            other_seasons = []
            
            for season_id, season_name in centris_seasons:
                if season_name == "Яқинлар I Ташриф Centris Towers":
                    tour_season = (season_id, season_name)
                else:
                    other_seasons.append((season_id, season_name))
            
            if not tour_season:
                await message.answer("Сезон 'Яқинлар I Ташриф Centris Towers' не найден в базе данных.")
                return
            
            # Удаляем сезон "Яқинлар I Ташриф Centris Towers" и добавляем его заново
            # Это обеспечит, что он будет последним по ID
            tour_season_id, tour_season_name = tour_season
            
            # Получаем видео этого сезона
            videos = db.get_videos_by_season(tour_season_id)
            if not videos:
                await message.answer("В сезоне 'Яқинлар I Ташриф Centris Towers' нет видео.")
                return
            
            # Сохраняем данные видео
            video_data = [(url, title, position) for url, title, position in videos]
            
            # Удаляем старый сезон (видео удалятся каскадно)
            if db.delete_season(tour_season_id):
                # Добавляем сезон заново
                urls = [data[0] for data in video_data]
                titles = [data[1] for data in video_data]
                db.add_season_with_videos("centris", tour_season_name, urls, titles)
                
                await message.answer("✅ Порядок сезонов исправлен! Сезон 'Яқинлар I Ташриф Centris Towers' теперь будет последним.")
            else:
                await message.answer("❌ Ошибка при исправлении порядка сезонов.")
                
        except Exception as e:
            await message.answer(f"❌ Ошибка при исправлении порядка сезонов: {e}")

    @dp.message_handler(commands=['fix_season_project'], user_id=ADMINS + [SUPER_ADMIN_ID])
    async def fix_season_project_command(message: types.Message):
        try:
            args = message.text.split()
            if len(args) != 3:
                await message.answer("Использование: /fix_season_project <season_id> <project>")
                return
            season_id = int(args[1])
            new_project = args[2]
            if db.update_season_project(season_id, new_project):
                await message.answer(f"Project сезона {season_id} успешно изменён на '{new_project}'")
            else:
                await message.answer("Ошибка при обновлении project сезона.")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(Command('force_update_keyboards'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def force_update_keyboards_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры без кэша
        """
        try:
            await message.answer("🔄 Принудительное обновление клавиатуры...")
            
            # Импортируем функцию напрямую из БД
            try:
                from db import db
                
                # Получаем сезоны напрямую из БД
                centris_seasons = db.get_seasons_by_project("centris")
                golden_seasons = db.get_seasons_by_project("golden")
                
                centris_count = len(centris_seasons)
                golden_count = len(golden_seasons)
                
                response = f"📊 **Данные из БД (без кэша):**\n\n"
                response += f"🏢 **Centris Towers**: {centris_count} сезонов\n"
                for season_id, season_name in centris_seasons:
                    response += f"   • {season_name} (ID: {season_id})\n"
                
                response += f"\n🏖️ **Golden Lake**: {golden_count} сезонов\n"
                for season_id, season_name in golden_seasons:
                    response += f"   • {season_name} (ID: {season_id})\n"
                
                await message.answer(response)
                
                # Теперь принудительно очищаем кэш
                try:
                    from handlers.users.video_selector import clear_season_keyboard_cache
                    clear_season_keyboard_cache()
                    await message.answer("✅ Кэш очищен! Теперь выберите проект в главном меню.")
                except Exception as e:
                    await message.answer(f"⚠️ Кэш не очищен: {e}")
                
            except Exception as e:
                await message.answer(f"❌ Ошибка при получении данных из БД: {e}")
                
        except Exception as e:
            await message.answer(f"❌ Общая ошибка: {e}")

    @dp.message_handler(Command('simple_cache_status'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def simple_cache_status_command(message: types.Message):
        """
        Простая команда для проверки состояния кэша
        """
        try:
            await message.answer("🔍 Проверяем состояние кэша...")
            
            # Проверяем, можем ли мы импортировать модуль
            try:
                from handlers.users.video_selector import _season_keyboard_cache, _cache_timestamp
                await message.answer("✅ Модуль video_selector импортирован успешно")
                
                if not _season_keyboard_cache:
                    await message.answer("📋 Кэш пуст - это хорошо!")
                else:
                    cache_size = len(_season_keyboard_cache)
                    await message.answer(f"📋 В кэше {cache_size} элементов")
                    
            except ImportError as e:
                await message.answer(f"❌ Ошибка импорта: {e}")
            except Exception as e:
                await message.answer(f"❌ Ошибка при проверке кэша: {e}")
                
        except Exception as e:
            await message.answer(f"❌ Общая ошибка: {e}")

    @dp.message_handler(Command('test_commands'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def test_commands_command(message: types.Message):
        """
        Простая тестовая команда для проверки работы
        """
        try:
            await message.answer("✅ Команды работают! Бот функционирует нормально.")
            logger.info("Тестовая команда выполнена успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка в тестовой команде: {e}")
            await message.answer(f"❌ Ошибка: {e}")

    @dp.message_handler(Command('instant_refresh'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def instant_refresh_command(message: types.Message):
        """
        Команда для мгновенного обновления клавиатуры в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard
            
            logger.info("=== НАЧАЛО instant_refresh ===")
            
            # Получаем свежие клавиатуры напрямую из БД (без кэша)
            logger.info("Получаем свежие клавиатуры напрямую из БД")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1
            golden_seasons = len(golden_keyboard.keyboard) - 1
            
            response = f"⚡ **МГНОВЕННОЕ ОБНОВЛЕНИЕ КЛАВИАТУРЫ!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Мгновенное обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 **Клавиатуры обновлены напрямую из БД!**\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ instant_refresh ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при мгновенном обновлении: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при мгновенном обновлении: {e}")

    @dp.message_handler(Command('force_refresh_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def force_refresh_seasons_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры сезонов в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard, clear_season_keyboard_cache
            
            logger.info("=== НАЧАЛО force_refresh_seasons ===")
            
            # Очищаем кэш для всех проектов
            logger.info("Очищаем кэш для всех проектов")
            clear_season_keyboard_cache()
            
            # Создаем обновленные клавиатуры
            logger.info("Создаем обновленные клавиатуры")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1  # минус кнопка "Orqaga qaytish"
            golden_seasons = len(golden_keyboard.keyboard) - 1   # минус кнопка "Orqaga qaytish"
            
            response = f"🔄 **Клавиатуры сезонов обновлены!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 Теперь пользователи увидят актуальный список сезонов.\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ force_refresh_seasons ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")

    @dp.message_handler(Command('list_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def list_seasons_command(message: types.Message):
        try:
            # Получаем сезоны с количеством видео для Centris Towers
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            # Получаем сезоны с количеством видео для Golden Lake
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            response = "📋 Список добавленных сезонов:\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
            
            if not centris_seasons and not golden_seasons:
                response += "Пока нет добавленных сезонов."
            
            await message.answer(response)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(Command('edit_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def edit_season_command(message: types.Message, state: FSMContext):
        try:
            # Получаем все сезоны с количеством видео
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            if not centris_seasons and not golden_seasons:
                await message.answer("Нет сезонов для редактирования.")
                return
            
            response = "📝 Выберите сезон для редактирования (введите ID):\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_season_id.state)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_season_id)
    async def process_season_id_for_edit(message: types.Message, state: FSMContext):
        try:
            season_id = int(message.text.strip())
            season_data = db.get_season_by_id(season_id)
            
            if not season_data:
                await message.answer("Сезон с таким ID не найден. Попробуйте снова:")
                return
            
            season_id, project, season_name = season_data
            videos = db.get_videos_with_ids_by_season(season_id)
            
            await state.update_data(season_id=season_id, project=project, season_name=season_name)
            
            response = f"📝 Редактирование сезона:\n"
            response += f"ID: {season_id}\n"
            response += f"Проект: {project}\n"
            response += f"Название: {season_name}\n"
            response += f"Количество видео: {len(videos)}\n\n"
            
            if videos:
                response += "Видео в сезоне:\n"
                for video_id, url, title, position in videos:
                    response += f"  ID {video_id}: {title} (позиция {position})\n"
            
            response += "\nВыберите действие:\n"
            response += "1. Изменить название сезона\n"
            response += "2. Редактировать видео\n"
            response += "3. Удалить отдельные видео\n"
            response += "4. Удалить весь сезон\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_action.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID сезона (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_action)
    async def process_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if action == "1":
            await message.answer("Введите новое название сезона:")
            await state.set_state(EditSeasonStates.waiting_for_new_name.state)
        elif action == "2":
            await message.answer("Введите ID видео для редактирования:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "3":
            await message.answer("Введите ID видео для удаления:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "4":
            # Подтверждение удаления сезона
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да, удалить", callback_data=f"confirm_delete_season_{season_id}"),
                InlineKeyboardButton("Отмена", callback_data="cancel_delete")
            )
            await message.answer("⚠️ Вы уверены, что хотите удалить весь сезон и все его видео?", reply_markup=kb)
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditSeasonStates.waiting_for_new_name)
    async def process_new_season_name(message: types.Message, state: FSMContext):
        new_name = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if db.update_season(season_id, new_name):
            await message.answer(f"✅ Название сезона успешно изменено на: {new_name}")
        else:
            await message.answer("❌ Ошибка при обновлении названия сезона.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_video_id)
    async def process_video_id_for_edit(message: types.Message, state: FSMContext):
        try:
            video_id = int(message.text.strip())
            video_data = db.get_video_by_id(video_id)
            
            if not video_data:
                await message.answer("Видео с таким ID не найдено. Попробуйте снова:")
                return
            
            video_id, season_id, url, title, position = video_data
            await state.update_data(video_id=video_id, season_id=season_id, url=url, title=title, position=position)
            
            response = f"📹 Редактирование видео:\n"
            response += f"ID: {video_id}\n"
            response += f"Название: {title}\n"
            response += f"Позиция: {position}\n"
            response += f"URL: {url}\n\n"
            response += "Выберите действие:\n"
            response += "1. Изменить URL\n"
            response += "2. Изменить название\n"
            response += "3. Изменить позицию\n"
            response += "4. Удалить видео\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID видео (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_video_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        
        if action == "1":
            await message.answer("Введите новый URL видео:")
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        elif action == "2":
            await message.answer("Введите новое название видео:")
            await state.set_state(EditVideoStates.waiting_for_new_title.state)
        elif action == "3":
            await message.answer("Введите новую позицию видео (число):")
            await state.set_state(EditVideoStates.waiting_for_new_position.state)
        elif action == "4":
            video_id = data.get("video_id")
            if db.delete_video(video_id):
                await message.answer("✅ Видео успешно удалено.")
            else:
                await message.answer("❌ Ошибка при удалении видео.")
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование видео отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_new_video_url(message: types.Message, state: FSMContext):
        new_url = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        title = data.get("title")
        position = data.get("position")
        
        if db.update_video(video_id, new_url, title, position):
            await message.answer(f"✅ URL видео успешно изменен на: {new_url}")
        else:
            await message.answer("❌ Ошибка при обновлении URL видео.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_new_title)
    async def process_new_video_title(message: types.Message, state: FSMContext):
        new_title = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        url = data.get("url")
        position = data.get("position")
        
        if db.update_video(video_id, url, new_title, position):
            await message.answer(f"✅ Название видео успешно изменено на: {new_title}")
        else:
            await message.answer("❌ Ошибка при обновлении названия видео.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_new_position)
    async def process_new_video_position(message: types.Message, state: FSMContext):
        try:
            new_position = int(message.text.strip())
            data = await state.get_data()
            video_id = data.get("video_id")
            url = data.get("url")
            title = data.get("title")
            
            if db.update_video(video_id, url, title, new_position):
                await message.answer(f"✅ Позиция видео успешно изменена на: {new_position}")
            else:
                await message.answer("❌ Ошибка при обновлении позиции видео.")
        except ValueError:
            await message.answer("Пожалуйста, введите корректную позицию (число):")
            return
        
        await state.finish()

    @dp.callback_query_handler(lambda c: c.data.startswith("confirm_delete_season_"))
    async def confirm_delete_season(callback_query: types.CallbackQuery):
        season_id = int(callback_query.data.replace("confirm_delete_season_", ""))
        
        if db.delete_season(season_id):
            await safe_edit_text(callback_query, "✅ Сезон и все его видео успешно удалены.")
        else:
            await safe_edit_text(callback_query, "❌ Ошибка при удалении сезона.")
        
        await callback_query.answer()

    @dp.callback_query_handler(lambda c: c.data == "cancel_delete")
    async def cancel_delete_season(callback_query: types.CallbackQuery):
        await safe_edit_text(callback_query, "❌ Удаление отменено.")
        await callback_query.answer()

    @dp.message_handler(Command('delete_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def delete_season_command(message: types.Message):
        try:
            # Парсим ID сезона из команды
            args = message.text.split()
            if len(args) != 2:
                await message.answer("Использование: /delete_season <ID_сезона>")
                return
            
            season_id = int(args[1])
            season_data = db.get_season_by_id(season_id)
            
            if not season_data:
                await message.answer("Сезон с таким ID не найден.")
                return
            
            season_id, project, season_name = season_data
            videos = db.get_videos_by_season(season_id)
            
            response = f"⚠️ Подтвердите удаление сезона:\n"
            response += f"ID: {season_id}\n"
            response += f"Проект: {project}\n"
            response += f"Название: {season_name}\n"
            response += f"Количество видео: {len(videos)}\n\n"
            response += "Все видео будут удалены безвозвратно!"
            
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да, удалить", callback_data=f"confirm_delete_season_{season_id}"),
                InlineKeyboardButton("Отмена", callback_data="cancel_delete")
            )
            
            await message.answer(response, reply_markup=kb)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID сезона (число).")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(Command('season_help'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def season_help_command(message: types.Message):
        help_text = """
📋 **Команды для управления сезонами:**

**Добавление:**
• `/add_season` - Добавить новый сезон
• `/list_seasons` - Показать все сезоны

**Редактирование:**
• `/edit_season` - Редактировать существующий сезон
  - Изменить название сезона
  - Редактировать видео (URL, название, позиция)
  - Удалить отдельные видео

**Удаление:**
• `/delete_season <ID>` - Удалить сезон по ID

**Утилиты:**
• `/migrate_old_seasons` - Перенести старые сезоны в базу данных
• `/fix_season_order` - Исправить порядок сезонов (Яқинлар I Ташриф будет последним)

**Примеры использования:**
1. Добавить сезон: `/add_season`
2. Посмотреть сезоны: `/list_seasons`
3. Редактировать сезон: `/edit_season` (затем выбрать ID)
4. Удалить сезон: `/delete_season 5`
5. Исправить порядок: `/fix_season_order`

⚠️ **Внимание:** Удаление сезона удаляет все его видео безвозвратно!

📝 **Особенности:**
• Сезон "Яқинлар I Ташриф Centris Towers" всегда будет последним в меню
• Новые сезоны добавляются в правильном порядке автоматически
        """
        await message.answer(help_text)

    @dp.message_handler(Command('migrate_old_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def migrate_old_seasons_command(message: types.Message):
        """Миграция старых сезонов в базу данных"""
        try:
            # Проверяем, есть ли уже сезоны в базе
            centris_seasons = db.get_seasons_by_project("centris")
            golden_seasons = db.get_seasons_by_project("golden")
            
            if centris_seasons or golden_seasons:
                await message.answer("Сезоны уже есть в базе данных. Миграция не требуется.")
                return
            
            # Добавляем старые сезоны Centris Towers
            old_centris_seasons = [
                ("centris", "Яқинлар 1.0 I I Иброҳим Мамасаидов", VIDEO_LIST_1, CAPTION_LIST_1),
                ("centris", "Яқинлар 2.0 I I Иброҳим Мамасаидов", VIDEO_LIST_2, CAPTION_LIST_2),
                ("centris", "Яқинлар 3.0 I I Иброҳим Мамасаидов", VIDEO_LIST_3, CAPTION_LIST_3),
                ("centris", "Яқинлар 4.0 I I Иброҳим Мамасаидов", VIDEO_LIST_4, CAPTION_LIST_4),
                ("centris", "Яқинлар 5.0 I I Иброҳим Мамасаидов", VIDEO_LIST_5, CAPTION_LIST_5),
                ("centris", "Яқинлар I Ташриф Centris Towers", VIDEO_LIST_6, CAPTION_LIST_6),
            ]
            
            # Добавляем старые сезоны Golden Lake
            old_golden_seasons = [
                ("golden", "Golden lake 1", VIDEO_LIST_GOLDEN_1, GOLDEN_LIST),
            ]
            
            migrated_count = 0
            
            # Мигрируем Centris Towers
            for project, season_name, video_list, caption_list in old_centris_seasons:
                if len(video_list) == len(caption_list):
                    db.add_season_with_videos(project, season_name, video_list, caption_list)
                    migrated_count += 1
            
            # Мигрируем Golden Lake
            for project, season_name, video_list, caption_list in old_golden_seasons:
                if len(video_list) == len(caption_list):
                    db.add_season_with_videos(project, season_name, video_list, caption_list)
                    migrated_count += 1
            
            await message.answer(f"✅ Миграция завершена! Добавлено {migrated_count} сезонов.")
            
        except Exception as e:
            await message.answer(f"❌ Ошибка при миграции: {e}")

    @dp.message_handler(Command('fix_season_order'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def fix_season_order_command(message: types.Message):
        """Исправить порядок сезонов, чтобы 'Яқинлар I Ташриф Centris Towers' был последним"""
        try:
            # Получаем все сезоны Centris Towers
            centris_seasons = db.get_seasons_by_project("centris")
            
            if not centris_seasons:
                await message.answer("Нет сезонов Centris Towers для исправления порядка.")
                return
            
            # Проверяем, есть ли сезон "Яқинлар I Ташриф Centris Towers"
            tour_season = None
            other_seasons = []
            
            for season_id, season_name in centris_seasons:
                if season_name == "Яқинлар I Ташриф Centris Towers":
                    tour_season = (season_id, season_name)
                else:
                    other_seasons.append((season_id, season_name))
            
            if not tour_season:
                await message.answer("Сезон 'Яқинлар I Ташриф Centris Towers' не найден в базе данных.")
                return
            
            # Удаляем сезон "Яқинлар I Ташриф Centris Towers" и добавляем его заново
            # Это обеспечит, что он будет последним по ID
            tour_season_id, tour_season_name = tour_season
            
            # Получаем видео этого сезона
            videos = db.get_videos_by_season(tour_season_id)
            if not videos:
                await message.answer("В сезоне 'Яқинлар I Ташриф Centris Towers' нет видео.")
                return
            
            # Сохраняем данные видео
            video_data = [(url, title, position) for url, title, position in videos]
            
            # Удаляем старый сезон (видео удалятся каскадно)
            if db.delete_season(tour_season_id):
                # Добавляем сезон заново
                urls = [data[0] for data in video_data]
                titles = [data[1] for data in video_data]
                db.add_season_with_videos("centris", tour_season_name, urls, titles)
                
                await message.answer("✅ Порядок сезонов исправлен! Сезон 'Яқинлар I Ташриф Centris Towers' теперь будет последним.")
            else:
                await message.answer("❌ Ошибка при исправлении порядка сезонов.")
                
        except Exception as e:
            await message.answer(f"❌ Ошибка при исправлении порядка сезонов: {e}")

    @dp.message_handler(commands=['fix_season_project'], user_id=ADMINS + [SUPER_ADMIN_ID])
    async def fix_season_project_command(message: types.Message):
        try:
            args = message.text.split()
            if len(args) != 3:
                await message.answer("Использование: /fix_season_project <season_id> <project>")
                return
            season_id = int(args[1])
            new_project = args[2]
            if db.update_season_project(season_id, new_project):
                await message.answer(f"Project сезона {season_id} успешно изменён на '{new_project}'")
            else:
                await message.answer("Ошибка при обновлении project сезона.")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(Command('force_update_keyboards'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def force_update_keyboards_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры без кэша
        """
        try:
            await message.answer("🔄 Принудительное обновление клавиатуры...")
            
            # Импортируем функцию напрямую из БД
            try:
                from db import db
                
                # Получаем сезоны напрямую из БД
                centris_seasons = db.get_seasons_by_project("centris")
                golden_seasons = db.get_seasons_by_project("golden")
                
                centris_count = len(centris_seasons)
                golden_count = len(golden_seasons)
                
                response = f"📊 **Данные из БД (без кэша):**\n\n"
                response += f"🏢 **Centris Towers**: {centris_count} сезонов\n"
                for season_id, season_name in centris_seasons:
                    response += f"   • {season_name} (ID: {season_id})\n"
                
                response += f"\n🏖️ **Golden Lake**: {golden_count} сезонов\n"
                for season_id, season_name in golden_seasons:
                    response += f"   • {season_name} (ID: {season_id})\n"
                
                await message.answer(response)
                
                # Теперь принудительно очищаем кэш
                try:
                    from handlers.users.video_selector import clear_season_keyboard_cache
                    clear_season_keyboard_cache()
                    await message.answer("✅ Кэш очищен! Теперь выберите проект в главном меню.")
                except Exception as e:
                    await message.answer(f"⚠️ Кэш не очищен: {e}")
                
            except Exception as e:
                await message.answer(f"❌ Ошибка при получении данных из БД: {e}")
                
        except Exception as e:
            await message.answer(f"❌ Общая ошибка: {e}")

    @dp.message_handler(Command('simple_cache_status'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def simple_cache_status_command(message: types.Message):
        """
        Простая команда для проверки состояния кэша
        """
        try:
            await message.answer("🔍 Проверяем состояние кэша...")
            
            # Проверяем, можем ли мы импортировать модуль
            try:
                from handlers.users.video_selector import _season_keyboard_cache, _cache_timestamp
                await message.answer("✅ Модуль video_selector импортирован успешно")
                
                if not _season_keyboard_cache:
                    await message.answer("📋 Кэш пуст - это хорошо!")
                else:
                    cache_size = len(_season_keyboard_cache)
                    await message.answer(f"📋 В кэше {cache_size} элементов")
                    
            except ImportError as e:
                await message.answer(f"❌ Ошибка импорта: {e}")
            except Exception as e:
                await message.answer(f"❌ Ошибка при проверке кэша: {e}")
                
        except Exception as e:
            await message.answer(f"❌ Общая ошибка: {e}")

    @dp.message_handler(Command('test_commands'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def test_commands_command(message: types.Message):
        """
        Простая тестовая команда для проверки работы
        """
        try:
            await message.answer("✅ Команды работают! Бот функционирует нормально.")
            logger.info("Тестовая команда выполнена успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка в тестовой команде: {e}")
            await message.answer(f"❌ Ошибка: {e}")

    @dp.message_handler(Command('instant_refresh'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def instant_refresh_command(message: types.Message):
        """
        Команда для мгновенного обновления клавиатуры в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard
            
            logger.info("=== НАЧАЛО instant_refresh ===")
            
            # Получаем свежие клавиатуры напрямую из БД (без кэша)
            logger.info("Получаем свежие клавиатуры напрямую из БД")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1
            golden_seasons = len(golden_keyboard.keyboard) - 1
            
            response = f"⚡ **МГНОВЕННОЕ ОБНОВЛЕНИЕ КЛАВИАТУРЫ!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Мгновенное обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 **Клавиатуры обновлены напрямую из БД!**\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ instant_refresh ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при мгновенном обновлении: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при мгновенном обновлении: {e}")

    @dp.message_handler(Command('force_refresh_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def force_refresh_seasons_command(message: types.Message):
        """
        Команда для принудительного обновления клавиатуры сезонов в текущем чате
        """
        try:
            from handlers.users.video_selector import get_season_keyboard, clear_season_keyboard_cache
            
            logger.info("=== НАЧАЛО force_refresh_seasons ===")
            
            # Очищаем кэш для всех проектов
            logger.info("Очищаем кэш для всех проектов")
            clear_season_keyboard_cache()
            
            # Создаем обновленные клавиатуры
            logger.info("Создаем обновленные клавиатуры")
            centris_keyboard = get_season_keyboard("centris")
            golden_keyboard = get_season_keyboard("golden")
            
            # Подсчитываем количество сезонов
            centris_seasons = len(centris_keyboard.keyboard) - 1  # минус кнопка "Orqaga qaytish"
            golden_seasons = len(golden_keyboard.keyboard) - 1   # минус кнопка "Orqaga qaytish"
            
            response = f"🔄 **Клавиатуры сезонов обновлены!**\n\n"
            response += f"📱 **Centris Towers** ({centris_seasons} сезонов):\n"
            
            # Показываем кнопки Centris
            await message.answer(response, reply_markup=centris_keyboard)
            
            # Показываем кнопки Golden Lake
            response2 = f"📱 **Golden Lake** ({golden_seasons} сезонов):\n"
            await message.answer(response2, reply_markup=golden_keyboard)
            
            # Финальное сообщение
            final_response = f"✅ **Обновление завершено!**\n\n"
            final_response += f"📊 **Статистика:**\n"
            final_response += f"   • Centris Towers: {centris_seasons} сезонов\n"
            final_response += f"   • Golden Lake: {golden_seasons} сезонов\n\n"
            final_response += f"💡 Теперь пользователи увидят актуальный список сезонов.\n"
            final_response += f"🔧 Для проверки используйте: /test_cache"
            
            await message.answer(final_response)
            
            logger.info(f"=== КОНЕЦ force_refresh_seasons ===")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await message.answer(f"❌ Ошибка при обновлении клавиатуры сезонов: {e}")

    @dp.message_handler(Command('list_seasons'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def list_seasons_command(message: types.Message):
        try:
            # Получаем сезоны с количеством видео для Centris Towers
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            # Получаем сезоны с количеством видео для Golden Lake
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            response = "📋 Список добавленных сезонов:\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  • {season_name} ({video_count} видео)\n"
            
            if not centris_seasons and not golden_seasons:
                response += "Пока нет добавленных сезонов."
            
            await message.answer(response)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(Command('edit_season'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def edit_season_command(message: types.Message, state: FSMContext):
        try:
            # Получаем все сезоны с количеством видео
            centris_seasons = db.get_seasons_with_videos_by_project("centris")
            golden_seasons = db.get_seasons_with_videos_by_project("golden")
            
            if not centris_seasons and not golden_seasons:
                await message.answer("Нет сезонов для редактирования.")
                return
            
            response = "📝 Выберите сезон для редактирования (введите ID):\n\n"
            
            if centris_seasons:
                response += "🏢 Centris Towers:\n"
                for season_id, season_name, video_count in centris_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
                response += "\n"
            
            if golden_seasons:
                response += "🏘️ Golden Lake:\n"
                for season_id, season_name, video_count in golden_seasons:
                    response += f"  ID {season_id}: {season_name} ({video_count} видео)\n"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_season_id.state)
        except Exception as e:
            await message.answer(f"Ошибка при получении списка сезонов: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_season_id)
    async def process_season_id_for_edit(message: types.Message, state: FSMContext):
        try:
            season_id = int(message.text.strip())
            season_data = db.get_season_by_id(season_id)
            
            if not season_data:
                await message.answer("Сезон с таким ID не найден. Попробуйте снова:")
                return
            
            season_id, project, season_name = season_data
            videos = db.get_videos_with_ids_by_season(season_id)
            
            await state.update_data(season_id=season_id, project=project, season_name=season_name)
            
            response = f"📝 Редактирование сезона:\n"
            response += f"ID: {season_id}\n"
            response += f"Проект: {project}\n"
            response += f"Название: {season_name}\n"
            response += f"Количество видео: {len(videos)}\n\n"
            
            if videos:
                response += "Видео в сезоне:\n"
                for video_id, url, title, position in videos:
                    response += f"  ID {video_id}: {title} (позиция {position})\n"
            
            response += "\nВыберите действие:\n"
            response += "1. Изменить название сезона\n"
            response += "2. Редактировать видео\n"
            response += "3. Удалить отдельные видео\n"
            response += "4. Удалить весь сезон\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditSeasonStates.waiting_for_action.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID сезона (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditSeasonStates.waiting_for_action)
    async def process_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if action == "1":
            await message.answer("Введите новое название сезона:")
            await state.set_state(EditSeasonStates.waiting_for_new_name.state)
        elif action == "2":
            await message.answer("Введите ID видео для редактирования:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "3":
            await message.answer("Введите ID видео для удаления:")
            await state.set_state(EditVideoStates.waiting_for_video_id.state)
        elif action == "4":
            # Подтверждение удаления сезона
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да, удалить", callback_data=f"confirm_delete_season_{season_id}"),
                InlineKeyboardButton("Отмена", callback_data="cancel_delete")
            )
            await message.answer("⚠️ Вы уверены, что хотите удалить весь сезон и все его видео?", reply_markup=kb)
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditSeasonStates.waiting_for_new_name)
    async def process_new_season_name(message: types.Message, state: FSMContext):
        new_name = message.text.strip()
        data = await state.get_data()
        season_id = data.get("season_id")
        
        if db.update_season(season_id, new_name):
            await message.answer(f"✅ Название сезона успешно изменено на: {new_name}")
        else:
            await message.answer("❌ Ошибка при обновлении названия сезона.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_video_id)
    async def process_video_id_for_edit(message: types.Message, state: FSMContext):
        try:
            video_id = int(message.text.strip())
            video_data = db.get_video_by_id(video_id)
            
            if not video_data:
                await message.answer("Видео с таким ID не найдено. Попробуйте снова:")
                return
            
            video_id, season_id, url, title, position = video_data
            await state.update_data(video_id=video_id, season_id=season_id, url=url, title=title, position=position)
            
            response = f"📹 Редактирование видео:\n"
            response += f"ID: {video_id}\n"
            response += f"Название: {title}\n"
            response += f"Позиция: {position}\n"
            response += f"URL: {url}\n\n"
            response += "Выберите действие:\n"
            response += "1. Изменить URL\n"
            response += "2. Изменить название\n"
            response += "3. Изменить позицию\n"
            response += "4. Удалить видео\n"
            response += "5. Отмена"
            
            await message.answer(response)
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID видео (число):")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_video_edit_action(message: types.Message, state: FSMContext):
        action = message.text.strip()
        data = await state.get_data()
        
        if action == "1":
            await message.answer("Введите новый URL видео:")
            await state.set_state(EditVideoStates.waiting_for_new_url.state)
        elif action == "2":
            await message.answer("Введите новое название видео:")
            await state.set_state(EditVideoStates.waiting_for_new_title.state)
        elif action == "3":
            await message.answer("Введите новую позицию видео (число):")
            await state.set_state(EditVideoStates.waiting_for_new_position.state)
        elif action == "4":
            video_id = data.get("video_id")
            if db.delete_video(video_id):
                await message.answer("✅ Видео успешно удалено.")
            else:
                await message.answer("❌ Ошибка при удалении видео.")
            await state.finish()
        elif action == "5":
            await message.answer("Редактирование видео отменено.")
            await state.finish()
        else:
            await message.answer("Пожалуйста, выберите действие (1-5):")

    @dp.message_handler(state=EditVideoStates.waiting_for_new_url)
    async def process_new_video_url(message: types.Message, state: FSMContext):
        new_url = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        title = data.get("title")
        position = data.get("position")
        
        if db.update_video(video_id, new_url, title, position):
            await message.answer(f"✅ URL видео успешно изменен на: {new_url}")
        else:
            await message.answer("❌ Ошибка при обновлении URL видео.")
        
        await state.finish()

    @dp.message_handler(state=EditVideoStates.waiting_for_new_title)
    async def process_new_video_title(message: types.Message, state: FSMContext):
        new_title = message.text.strip()
        data = await state.get_data()
        video_id = data.get("video_id")
        url = data.get("url")
        position = data.get("position")
        
        if db.update_video(video_id, url, new_title, position):
            await message.answer(f"✅ Название видео успешно изменено на: {new_title}")
        else:
            await message.answer("❌ Ошибка при обновлении названия видео.")
        
        await state.finish()

except Exception as exx:
    from datetime import datetime
    now = datetime.now()
    formatted_date_time = now.strftime('%Y-%m-%d %H:%M:%S')
    print('admin image sender', formatted_date_time, f'error {exx}')

# Новая команда для обновления главного меню
@dp.message_handler(Command('update_main_menu'), user_id=ADMINS + [SUPER_ADMIN_ID])
async def update_main_menu_command(message: types.Message):
    """
    Команда для принудительного обновления главного меню
    """
    try:
        from handlers.users.video_selector import force_update_main_menu
        
        logger.info("🔄 Принудительное обновление главного меню...")
        
        # Принудительно обновляем главное меню
        updated_main_menu = force_update_main_menu()
        
        if updated_main_menu:
            logger.info("✅ Главное меню принудительно обновлено")
            
            # Отправляем обновленное меню пользователю
            await message.answer(
                "🔄 **Главное меню принудительно обновлено!** Теперь выберите проект:",
                reply_markup=updated_main_menu
            )
            
            await message.answer(
                "✅ Главное меню успешно обновлено!\n\n"
                "Теперь количество сезонов в кнопках соответствует актуальным данным из базы."
            )
        else:
            logger.error("❌ Не удалось обновить главное меню")
            await message.answer("❌ Ошибка при обновлении главного меню")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении главного меню: {e}")
        await message.answer(f"❌ Ошибка при обновлении главного меню: {e}")

# Команда для проверки разницы между главным меню и БД
@dp.message_handler(Command('check_menu_sync'), user_id=ADMINS + [SUPER_ADMIN_ID])
async def check_menu_sync_command(message: types.Message):
    """
    Команда для проверки синхронизации главного меню с базой данных
    """
    try:
        from handlers.users.video_selector import get_main_menu_keyboard
        
        logger.info("🔍 Проверка синхронизации главного меню с БД...")
        
        # Получаем данные из БД
        centris_seasons = db.get_seasons_by_project("centris")
        golden_seasons = db.get_seasons_by_project("golden")
        
        centris_count = len(centris_seasons)
        golden_count = len(golden_seasons)
        
        # Получаем текущее главное меню
        current_menu = get_main_menu_keyboard()
        
        # Анализируем кнопки
        centris_button = None
        golden_button = None
        
        for row in current_menu.keyboard:
            for button in row:
                if button.text.startswith("Centris towers"):
                    centris_button = button.text
                elif button.text.startswith("Golden lake"):
                    golden_button = button.text
        
        response = "🔍 **ПРОВЕРКА СИНХРОНИЗАЦИИ ГЛАВНОГО МЕНЮ**\n\n"
        response += f"📊 **Данные из БД:**\n"
        response += f"   • Centris: {centris_count} сезонов\n"
        response += f"   • Golden: {golden_count} сезонов\n\n"
        
        response += f"📱 **Текущие кнопки:**\n"
        response += f"   • Centris: {centris_button or 'НЕ НАЙДЕНА'}\n"
        response += f"   • Golden: {golden_button or 'НЕ НАЙДЕНА'}\n\n"
        
        # Проверяем соответствие
        if centris_button and golden_button:
            centris_menu_count = int(centris_button.split('(')[1].split()[0])
            golden_menu_count = int(golden_button.split('(')[1].split()[0])
            
            if centris_menu_count == centris_count and golden_menu_count == golden_count:
                response += "✅ **СИНХРОНИЗАЦИЯ ИДЕАЛЬНАЯ!**\n"
                response += "Главное меню полностью соответствует базе данных."
            else:
                response += "⚠️ **ОБНАРУЖЕНЫ РАЗЛИЧИЯ!**\n"
                if centris_menu_count != centris_count:
                    response += f"   • Centris: меню {centris_menu_count} vs БД {centris_count}\n"
                if golden_menu_count != golden_count:
                    response += f"   • Golden: меню {golden_menu_count} vs БД {golden_count}\n"
                response += "\nИспользуйте /update_main_menu для исправления."
        else:
            response += "❌ **ОШИБКА АНАЛИЗА КНОПОК**\n"
            response += "Не удалось проанализировать текущие кнопки."
        
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке синхронизации: {e}")
        await message.answer(f"❌ Ошибка при проверке синхронизации: {e}")

async def update_season_keyboards_for_all_chats(project):
    """Обновляет клавиатуры сезонов для всех активных чатов после добавления нового сезона"""
    logger.info(f'=== НАЧАЛО update_season_keyboards_for_all_chats для проекта {project} ===')
    try:
        from handlers.users.video_selector import clear_season_keyboard_cache
        clear_season_keyboard_cache(project)
        logger.info(f'✅ Кэш клавиатуры сезонов очищен для проекта {project}')
    except Exception as e:
        logger.error(f'❌ Ошибка при обновлении клавиатур сезонов: {e}')
    logger.info(f'=== КОНЕЦ update_season_keyboards_for_all_chats для проекта {project} ===')

async def notify_active_groups_about_new_season(project, season_name, video_count):
    """Отправляет уведомление о новом сезоне в активные группы"""
    try:
        project_names = {'centris': '�� Centris Towers', 'golden': '🏘️ Golden Lake'}
        project_display_name = project_names.get(project, project)
        logger.info(f'Уведомление о новом сезоне подготовлено для {project_display_name}')
    except Exception as e:
        logger.error(f'Ошибка при подготовке уведомления о новом сезоне: {e}')
