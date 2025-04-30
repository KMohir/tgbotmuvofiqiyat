from datetime import datetime, timedelta

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
        await message.answer(f"Jami {total_media} ta media qabul qilindi. Opisaniye: {caption or 'yo‘q'}. Jo'natish boshlanadi...")

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
except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('admin image sender ',  f"{time }formatted_date_time",f"error {exx}" )