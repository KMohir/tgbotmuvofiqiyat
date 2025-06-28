from datetime import datetime, timedelta
from handlers.users.video_lists import VIDEO_LIST_1, VIDEO_LIST_2, VIDEO_LIST_3, CAPTION_LIST_1, CAPTION_LIST_2, CAPTION_LIST_3

try:
    from aiogram import types
    from aiogram.dispatcher import FSMContext
    from aiogram.dispatcher.filters.builtin import Command
    from aiogram.types import MediaGroup
    import asyncio
    from db import db
    from loader import dp, bot

    # ID администратора
    ADMIN_ID = 5657091547

    @dp.message_handler(Command('set_start_video'), user_id=ADMIN_ID)
    async def set_start_video_command(message: types.Message, state: FSMContext):
        await message.answer(
            "Har kungi video yuborishni qaysi videodan boshlashni belgilang.\n"
            "Video raqamini kiriting (1-15):"
        )
        await state.set_state("waiting_for_video_number")

    @dp.message_handler(Command('set_group_video'))
    async def set_group_video_command(message: types.Message, state: FSMContext):
        # Проверяем, что команда отправлена в группе и от админа
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            await message.answer("Bu buyruq faqat guruhlarda ishlaydi.")
            return
            
        if message.from_user.id != ADMIN_ID:
            await message.answer("Sizda bu buyruqni bajarish uchun ruxsat yo'q.")
            return
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("1-sezon", "2-sezon", "3-sezon")
        keyboard.add("Bekor qilish")
        
        await message.answer(
            "Guruh uchun qaysi sezonni tanlaysiz?\n"
            "1-sezon: 2 ta video (08:00 va 20:00)\n"
            "2-sezon: 1 ta video (08:00)\n"
            "3-sezon: 1 ta video (08:00)"
        )
        await state.set_state("waiting_for_season")
        await state.update_data(chat_id=message.chat.id)

    @dp.message_handler(state="waiting_for_season")
    async def process_season_selection(message: types.Message, state: FSMContext):
        if message.from_user.id != ADMIN_ID:
            await message.answer("Sizda bu buyruqni bajarish uchun ruxsat yo'q.")
            await state.finish()
            return

        if message.text == "Bekor qilish":
            await message.answer("Bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())
            await state.finish()
            return

        if message.text not in ["1-sezon", "2-sezon", "3-sezon"]:
            await message.answer("Iltimos, to'g'ri sezonni tanlang.")
            return

        data = await state.get_data()
        chat_id = data.get("chat_id")
        
        await state.update_data(season=message.text)
        
        # Показываем список видео для выбранного сезона
        if message.text == "1-sezon":
            video_list = CAPTION_LIST_1
        elif message.text == "2-sezon":
            video_list = CAPTION_LIST_2
        else:  # 3-sezon
            video_list = CAPTION_LIST_3

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for i, caption in enumerate(video_list, 1):
            keyboard.add(f"{i}. {caption}")
        keyboard.add("Bekor qilish")

        await message.answer(
            f"{message.text} uchun qaysi videodan boshlashni tanlang:",
            reply_markup=keyboard
        )
        await state.set_state("waiting_for_group_video")

    @dp.message_handler(state="waiting_for_group_video")
    async def process_group_video_selection(message: types.Message, state: FSMContext):
        if message.from_user.id != ADMIN_ID:
            await message.answer("Sizda bu buyruqni bajarish uchun ruxsat yo'q.")
            await state.finish()
            return

        if message.text == "Bekor qilish":
            await message.answer("Bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())
            await state.finish()
            return

        try:
            # Извлекаем номер видео из текста (например, "1. Centris Towers'daги лобби" -> 1)
            video_number = int(message.text.split('.')[0])
            
            data = await state.get_data()
            season = data.get("season")
            chat_id = data.get("chat_id")
            
            # Сохраняем настройки для группы
            db.set_group_video_settings(chat_id, season, video_number - 1)
            
            await message.answer(
                f"Guruh uchun {season} {video_number}-chi videodan boshlanadi.\n"
                f"Har kungi yuborish faollashtirildi.",
                reply_markup=types.ReplyKeyboardRemove()
            )
            
            # Перезапускаем планировщик для группы
            from handlers.users.video_scheduler import schedule_group_jobs
            schedule_group_jobs()
            
        except (ValueError, IndexError):
            await message.answer("Iltimos, to'g'ri video raqamini tanlang.")
        
        await state.finish()

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

except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('admin image sender ',  f"{time }formatted_date_time",f"error {exx}" )