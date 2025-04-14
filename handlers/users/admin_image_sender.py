from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Command
from aiogram.types import MediaGroup
import asyncio
from db import db
from loader import dp, bot

# ID администратора
ADMIN_ID = 5657091547

@dp.message_handler(Command('send_image'), user_id=ADMIN_ID)
async def send_image_command(message: types.Message, state: FSMContext):
    await message.answer(
        "Iltimos, barcha foydalanuvchilarga jo'natmoqchi bo'lgan rasmlarni yuboring. Tugatganingizdan so'ng /done buyrug'ini kiritin.")
    await state.set_state("waiting_for_images")
    await state.update_data(images=[])

@dp.message_handler(content_types=types.ContentType.PHOTO, state="waiting_for_images")
async def process_image(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Sizda bu buyruqni bajarish uchun ruxsat yo'q.")
        await state.finish()
        return

    data = await state.get_data()
    images = data.get('images', [])
    photo = message.photo[-1]
    images.append(photo.file_id)
    await state.update_data(images=images)
    await message.answer(
        f"Rasm qo'shildi. Jami: {len(images)}. Yana yuboring yoki /done buyrug'i bilan yakunlang.")

@dp.message_handler(Command('done'), state="waiting_for_images")
async def finish_image_collection(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Sizda bu buyruqni bajarish uchun ruxsat yo'q.")
        await state.finish()
        return

    data = await state.get_data()
    images = data.get('images', [])

    if not images:
        await message.answer("Siz birorta ham rasm yubormadingiz.")
        await state.finish()
        return

    # Переходим к состоянию ожидания описания
    await message.answer("Rasmlar qabul qilindi. Endi rasmlar bilan birga jo'natiladigan opisaniyeni kiriting.")
    await state.set_state("waiting_for_caption")
    # Сохраняем изображения в состоянии
    await state.update_data(images=images)

@dp.message_handler(state="waiting_for_caption")
async def process_caption(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Sizda bu buyruqni bajarish uchun ruxsat yo'q.")
        await state.finish()
        return

    caption = message.text
    data = await state.get_data()
    images = data.get('images', [])

    total_images = len(images)
    await message.answer(f"Jami {total_images} ta rasm qabul qilindi. Opisaniye: {caption}. Jo'natish boshlanadi...")

    users = db.get_all_users()
    print(f"Topilgan foydalanuvchilar: {len(users)}")

    chunk_size = 10
    image_chunks = [images[i:i + chunk_size] for i in range(0, len(images), chunk_size)]

    sent_count = 0
    for user_id in users:
        try:
            for chunk in image_chunks:
                media_group = MediaGroup()
                for i, file_id in enumerate(chunk):
                    if i == 0:
                        media_group.attach_photo(file_id, caption=caption)
                    else:
                        media_group.attach_photo(file_id)
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
        f"{total_images} ta rasmdan media guruhlar {sent_count} foydalanuvchilarga muvaffaqiyatli yuborildi!")
    await state.finish()

@dp.message_handler(state="waiting_for_images")
async def invalid_input(message: types.Message, state: FSMContext):
    await message.answer("Iltimos, rasm yuboring yoki /done buyrug'i bilan kirishni yakunlang.")
    await state.set_state("waiting_for_images")