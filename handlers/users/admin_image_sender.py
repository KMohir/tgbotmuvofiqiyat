from datetime import datetime, timedelta
from handlers.users.video_lists import VIDEO_LIST_1, VIDEO_LIST_2, VIDEO_LIST_3, VIDEO_LIST_4, VIDEO_LIST_5, VIDEO_LIST_GOLDEN_1

try:
    from aiogram import types
    from aiogram.dispatcher import FSMContext
    from aiogram.dispatcher.filters.builtin import Command
    from aiogram.types import MediaGroup
    import asyncio
    from db import db
    from loader import dp, bot
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.dispatcher.filters.state import State, StatesGroup

    # ID администратора
    ADMIN_ID = 5657091547

    # --- Новый FSM ---
    class GroupVideoStates(StatesGroup):
        waiting_for_project = State()
        waiting_for_centr_season = State()
        waiting_for_centr_video = State()
        waiting_for_golden_video = State()

    # --- Клавиатуры ---
    def get_project_keyboard():
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("Centris Towers", callback_data="project_centr"),
            InlineKeyboardButton("Golden Lake", callback_data="project_golden"),
            InlineKeyboardButton("Оба", callback_data="project_both")
        )
        return kb

    def get_season_keyboard():
        kb = InlineKeyboardMarkup(row_width=2)
        for season in ["1-sezon", "2-sezon", "3-sezon", "4-sezon", "5-sezon"]:
            kb.add(InlineKeyboardButton(season, callback_data=f"season_{season}"))
        return kb

    def get_video_keyboard(video_list, viewed):
        kb = InlineKeyboardMarkup(row_width=3)
        has_unwatched = False
        for idx, video in enumerate(video_list, 1):
            if (idx-1) not in viewed:
                kb.add(InlineKeyboardButton(str(idx), callback_data=f"video_{idx}"))
                has_unwatched = True
        return kb if has_unwatched else None

    @dp.message_handler(Command('set_start_video'), user_id=ADMIN_ID)
    async def set_start_video_command(message: types.Message, state: FSMContext):
        await message.answer(
            "Har kungi video yuborishni qaysi videodan boshlashni belgilang.\n"
            "Video raqamini kiriting (1-15):"
        )
        await state.set_state("waiting_for_video_number")

    @dp.message_handler(Command('set_group_video'), user_id=ADMIN_ID)
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
        await state.update_data(project=project)
        if project in ["centr", "both"]:
            await callback_query.message.edit_text("Centris Towers учун сезонни танланг:", reply_markup=get_season_keyboard())
            await state.set_state(GroupVideoStates.waiting_for_centr_season.state)
        elif project == "golden":
            await callback_query.message.edit_text("Golden Lake учун стартовое видео танланг:", reply_markup=get_video_keyboard(VIDEO_LIST_GOLDEN_1, []))
            await state.set_state(GroupVideoStates.waiting_for_golden_video.state)

    @dp.callback_query_handler(lambda c: c.data.startswith("season_"), state=GroupVideoStates.waiting_for_centr_season.state)
    async def process_centr_season(callback_query: types.CallbackQuery, state: FSMContext):
        season = callback_query.data.replace("season_", "")
        await state.update_data(centris_season=season)
        season_map = {
            "1-sezon": VIDEO_LIST_1,
            "2-sezon": VIDEO_LIST_2,
            "3-sezon": VIDEO_LIST_3,
            "4-sezon": VIDEO_LIST_4,
            "5-sezon": VIDEO_LIST_5,
        }
        video_list = season_map.get(season, [])
        chat_id = (await state.get_data()).get("chat_id")
        viewed = db.get_group_viewed_videos(f"centris_{chat_id}_{season}")
        kb = get_video_keyboard(video_list, viewed)
        if not kb:
            await callback_query.message.edit_text("Barcha video ushbu sezon uchun yuborilgan!")
            await state.finish()
            return
        await callback_query.message.edit_text(f"Centris Towers: {season} uchun start video tanlang:", reply_markup=kb)
        await state.set_state(GroupVideoStates.waiting_for_centr_video.state)

    @dp.callback_query_handler(lambda c: c.data.startswith("video_"), state=GroupVideoStates.waiting_for_centr_video.state)
    async def process_centr_video(callback_query: types.CallbackQuery, state: FSMContext):
        video_idx = int(callback_query.data.replace("video_", "")) - 1
        await state.update_data(centris_start_video=video_idx)
        data = await state.get_data()
        if data.get("project") == "both":
            await callback_query.message.edit_text("Golden Lake учун стартовое видео танланг:", reply_markup=get_video_keyboard(VIDEO_LIST_GOLDEN_1, []))
            await state.set_state(GroupVideoStates.waiting_for_golden_video.state)
        else:
            await save_group_settings(data)
            await callback_query.message.edit_text("Настройки сохранены! Рассылка активирована.")
            await state.finish()

    @dp.callback_query_handler(lambda c: c.data.startswith("video_"), state=GroupVideoStates.waiting_for_golden_video.state)
    async def process_golden_video(callback_query: types.CallbackQuery, state: FSMContext):
        video_idx = int(callback_query.data.replace("video_", "")) - 1
        await state.update_data(golden_start_video=video_idx)
        data = await state.get_data()
        chat_id = data.get("chat_id")
        viewed = db.get_group_viewed_videos(f"golden_{chat_id}")
        video_list = VIDEO_LIST_GOLDEN_1
        kb = get_video_keyboard(video_list, viewed)
        if not kb:
            await callback_query.message.edit_text("Barcha Golden Lake videolari yuborilgan!")
            await state.finish()
            return
        await save_group_settings(data)
        await callback_query.message.edit_text("Настройки сохранены! Рассылка активирована.")
        await state.finish()

    async def save_group_settings(data):
        chat_id = data.get("chat_id")
        project = data.get("project")
        centris_enabled = project in ["centr", "both"]
        golden_enabled = project in ["golden", "both"]
        centris_season = data.get("centris_season") if centris_enabled else None
        centris_start_video = data.get("centris_start_video") if centris_enabled else 0
        golden_start_video = data.get("golden_start_video") if golden_enabled else 0
        db.set_group_video_settings(
            chat_id,
            centris_enabled,
            centris_season,
            centris_start_video,
            golden_enabled,
            golden_start_video
        )
        from handlers.users.video_scheduler import schedule_group_jobs
        schedule_group_jobs()

    @dp.message_handler(state="waiting_for_video_number")
    async def process_video_number(message: types.Message, state: FSMContext):
        if message.from_user.id != ADMIN_ID:
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

    @dp.message_handler(Command('send_media'), user_id=ADMIN_ID)
    async def send_media_command(message: types.Message, state: FSMContext):
        await message.answer(
            "Iltimos, barcha foydalanuvchilarga jo'natmoqchi bo'lgan rasmlar yoki videolarni yuboring. "
            "Tugatganingizdan so'ng /done buyrug'ini kiritin.")
        await state.set_state("waiting_for_media")
        await state.update_data(media=[])

    @dp.message_handler(content_types=[types.ContentType.PHOTO, types.ContentType.VIDEO], state="waiting_for_media")
    async def process_media(message: types.Message, state: FSMContext):
        if message.from_user.id != ADMIN_ID:
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
        if message.from_user.id != ADMIN_ID:
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
        if message.from_user.id != ADMIN_ID:
            await message.answer("Sizda bu buyruqni bajarish uchun ruxsat yo'q.")
            await state.finish()
            return

        await process_media_sending(message, state, caption="")

    @dp.message_handler(state="waiting_for_caption")
    async def process_caption(message: types.Message, state: FSMContext):
        if message.from_user.id != ADMIN_ID:
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

    @dp.message_handler(Command('get_all_users'), user_id=ADMIN_ID)
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

    @dp.message_handler(Command('banned_groups'), user_id=ADMIN_ID)
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

    @dp.message_handler(Command('unban_group'), user_id=ADMIN_ID)
    async def unban_group_command(message: types.Message):
        try:
            group_id = int(message.text.split()[1])
            db.unban_group(group_id)
            await message.answer(f"Группа {group_id} разблокирована.")
        except (IndexError, ValueError):
            await message.answer("Использование: /unban_group <ID_группы>")

    @dp.message_handler(Command('reset_group_videos'), user_id=ADMIN_ID)
    async def reset_group_videos_command(message: types.Message, state: FSMContext):
        chat_id = message.chat.id
        # Сбросить просмотренные для Centris Towers всех сезонов и Golden Lake
        for season in ["1-sezon", "2-sezon", "3-sezon", "4-sezon", "5-sezon"]:
            db.set_group_video_index_and_viewed(f"centris_{chat_id}_{season}", None, season, 0, [])
        db.set_group_video_index_and_viewed(f"golden_{chat_id}", None, None, 0, [])
        await message.answer("Прогресс группы сброшен. Теперь можно выбрать стартовое видео заново.")

except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('admin image sender ',  f"{time }formatted_date_time",f"error {exx}" )