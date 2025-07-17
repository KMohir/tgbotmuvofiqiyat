from datetime import datetime, timedelta
from handlers.users.video_lists import VIDEO_LIST_1, VIDEO_LIST_2, VIDEO_LIST_3, VIDEO_LIST_4, VIDEO_LIST_5, VIDEO_LIST_GOLDEN_1
from data.config import ADMINS, SUPER_ADMIN_ID

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

    # --- Новый FSM ---
    class GroupVideoStates(StatesGroup):
        waiting_for_project = State()
        waiting_for_centr_season = State()
        waiting_for_centr_video = State()
        waiting_for_golden_video = State()
        waiting_for_golden_season = State()

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

    # --- Клавиатуры ---
    def get_project_keyboard():
        return InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton("Centris Towers", callback_data="project_centris"),
            InlineKeyboardButton("Golden Lake", callback_data="project_golden"),
            InlineKeyboardButton("Centris/Golden", callback_data="project_cg")
        )

    def get_season_keyboard(project):
        kb = InlineKeyboardMarkup(row_width=2)
        seasons = db.get_seasons_by_project(project)
        for season_id, season_name in seasons:
            kb.add(InlineKeyboardButton(season_name, callback_data=f"season_{season_id}"))
        return kb

    def get_video_keyboard_from_db(videos, viewed):
        kb = InlineKeyboardMarkup(row_width=3)
        has_unwatched = False
        for url, title, position in videos:
            if position not in viewed:
                kb.add(InlineKeyboardButton(f"{position+1}. {title}", callback_data=f"video_{position}"))
                has_unwatched = True
        return kb if has_unwatched else None

    @dp.message_handler(Command('set_start_video'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def set_start_video_command(message: types.Message, state: FSMContext):
        await message.answer(
            "Har kungi video yuborishni qaysi videodan boshlashni belgilang.\n"
            "Video raqamini kiriting (1-15):"
        )
        await state.set_state("waiting_for_video_number")

    @dp.message_handler(Command('set_group_video'), user_id=ADMINS + [SUPER_ADMIN_ID])
    async def set_group_video_command(message: types.Message, state: FSMContext):
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            await message.answer("Bu buyruq faqat guruhlarda ishlaydi.")
            return
        await message.answer("Группа учун проектни танланг:", reply_markup=get_project_keyboard())
        await state.set_state(GroupVideoStates.waiting_for_project.state)
        await state.update_data(chat_id=message.chat.id)

    @dp.callback_query_handler(lambda c: c.data.startswith("project_"), state=GroupVideoStates.waiting_for_project.state)
    async def process_project_selection(callback_query: types.CallbackQuery, state: FSMContext):
        project = callback_query.data.replace("project_", "")
        await state.update_data(project=project)  # Явно сохраняем выбранный проект
        if project == "centris":
            await callback_query.message.edit_text("Centris Towers учун сезонни танланг:", reply_markup=get_season_keyboard("centris"))
            await state.set_state(GroupVideoStates.waiting_for_centr_season.state)
        elif project == "golden":
            seasons = db.get_seasons_by_project("golden")
            if not seasons:
                await callback_query.message.edit_text("Нет сезонов Golden Lake.")
                return
            await callback_query.message.edit_text("Golden Lake учун сезонни танланг:", reply_markup=get_season_keyboard("golden"))
            await state.set_state(GroupVideoStates.waiting_for_golden_season.state)
        elif project == "cg":
            await callback_query.message.edit_text("Centris Towers учун сезонни танланг:", reply_markup=get_season_keyboard("centris"))
            await state.set_state(GroupVideoStates.waiting_for_centr_season.state)
            await state.update_data(both_selected=True)

    @dp.callback_query_handler(lambda c: c.data.startswith("season_"), state=GroupVideoStates.waiting_for_centr_season.state)
    async def process_centr_season(callback_query: types.CallbackQuery, state: FSMContext):
        season_id = int(callback_query.data.replace("season_", ""))
        await state.update_data(centris_season_id=season_id)
        videos = db.get_videos_by_season(season_id)
        chat_id = (await state.get_data()).get("chat_id")
        viewed = db.get_group_viewed_videos(chat_id)
        kb = get_video_keyboard_from_db(videos, viewed)
        if not kb:
            await callback_query.message.edit_text("Barcha video ushbu sezon uchun yuborilgan!")
            await state.finish()
            return
        await callback_query.message.edit_text("Centris Towers учун стартовое видео танланг:", reply_markup=kb)
        await state.set_state(GroupVideoStates.waiting_for_centr_video.state)

    @dp.callback_query_handler(lambda c: c.data.startswith("season_"), state=GroupVideoStates.waiting_for_golden_season.state)
    async def process_golden_season(callback_query: types.CallbackQuery, state: FSMContext):
        season_id = int(callback_query.data.replace("season_", ""))
        await state.update_data(golden_season_id=season_id)
        videos = db.get_videos_by_season(season_id)
        chat_id = (await state.get_data()).get("chat_id")
        viewed = db.get_group_viewed_videos(chat_id)
        kb = get_video_keyboard_from_db(videos, viewed)
        if not kb:
            await callback_query.message.edit_text("Barcha video ushbu sezon uchun yuborilgan!")
            await state.finish()
            return
        await callback_query.message.edit_text("Golden Lake учун стартовое видео танланг:", reply_markup=kb)
        await state.set_state(GroupVideoStates.waiting_for_golden_video.state)

    @dp.callback_query_handler(lambda c: c.data.startswith("video_"), state=GroupVideoStates.waiting_for_centr_video.state)
    async def process_centr_video(callback_query: types.CallbackQuery, state: FSMContext):
        video_idx = int(callback_query.data.replace("video_", ""))
        await state.update_data(centris_start_video=video_idx)
        data = await state.get_data()
        if data.get("project") == "cg":
            await callback_query.message.edit_text("Golden Lake учун сезонни танланг:", reply_markup=get_season_keyboard("golden"))
            await state.set_state(GroupVideoStates.waiting_for_golden_season.state)
        else:
            await save_group_settings(data)
            await callback_query.message.edit_text("Настройки сохранены! Рассылка активирована.")
            await state.finish()

    @dp.callback_query_handler(lambda c: c.data.startswith("video_"), state=GroupVideoStates.waiting_for_golden_video.state)
    async def process_golden_video(callback_query: types.CallbackQuery, state: FSMContext):
        video_idx = int(callback_query.data.replace("video_", ""))
        await state.update_data(golden_start_video=video_idx)
        data = await state.get_data()
        await save_group_settings(data)
        await callback_query.message.edit_text("Настройки сохранены! Рассылка активирована.")
        await state.finish()

    async def save_group_settings(data):
        chat_id = data.get("chat_id")
        project = data.get("project")
        centris_enabled = project in ["centris", "cg"]
        golden_enabled = project in ["golden", "cg"]
        centris_season_id = data.get("centris_season_id") if centris_enabled else None
        centris_start_video = data.get("centris_start_video", 0)
        golden_season_id = data.get("golden_season_id") if golden_enabled else None
        golden_start_video = data.get("golden_start_video", 0)
        db.set_group_video_settings(
            chat_id,
            int(centris_enabled),
            centris_season_id,
            centris_start_video,
            int(golden_enabled),
            golden_start_video
        )
        # --- Сохраняем стартовые сезоны и видео явно ---
        if centris_enabled and centris_season_id is not None:
            db.set_group_video_start(chat_id, 'centris', centris_season_id, centris_start_video)
            db.reset_group_viewed_videos(chat_id)
        if golden_enabled and golden_season_id is not None:
            db.set_group_video_start(chat_id, 'golden', golden_season_id, golden_start_video)
            db.reset_group_viewed_videos(chat_id)
        from handlers.users.video_scheduler import schedule_group_jobs
        schedule_group_jobs()

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
            InlineKeyboardButton("Centris Towers", callback_data="add_project_centr"),
            InlineKeyboardButton("Golden Lake", callback_data="add_project_golden")
        )
        await message.answer("Выберите проект для нового сезона:", reply_markup=kb)
        await state.set_state(AddSeasonStates.waiting_for_project.state)

    @dp.callback_query_handler(lambda c: c.data.startswith("add_project_"), state=AddSeasonStates.waiting_for_project.state)
    async def add_season_project(callback_query: types.CallbackQuery, state: FSMContext):
        project = callback_query.data.replace("add_project_", "")
        await state.update_data(project=project)
        await callback_query.message.edit_text("Введите название сезона:")
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
        # Сохраняем сезон и видео в базу
        project = data.get("project")
        season_name = data.get("season_name")
        db.add_season_with_videos(project, season_name, links, titles)
        await message.answer(f"Сезон '{season_name}' успешно добавлен в проект '{project}'.")
        await state.finish()

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
            response += "3. Удалить видео\n"
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
            await callback_query.message.edit_text("✅ Сезон и все его видео успешно удалены.")
        else:
            await callback_query.message.edit_text("❌ Ошибка при удалении сезона.")
        
        await callback_query.answer()

    @dp.callback_query_handler(lambda c: c.data == "cancel_delete")
    async def cancel_delete_season(callback_query: types.CallbackQuery):
        await callback_query.message.edit_text("❌ Удаление отменено.")
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

except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('admin image sender', formatted_date_time, f"error {exx}")