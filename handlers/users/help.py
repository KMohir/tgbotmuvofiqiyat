from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandHelp, Command
from aiogram.types import ReplyKeyboardRemove
import pandas as pd
from db import db
from loader import dp
from states.state import RegistrationStates
import os
from keyboards.default.reply import key, get_lang_for_button

@dp.message_handler(state=RegistrationStates.help)
@dp.message_handler(Command("help"))
async def bot_help(message: types.Message, state: FSMContext):
    text = "Buyruqlar ro'yxati:\n/taklif - Texnik yordamga habar yozish\n/about - Centris Towers haqida bilish"

    await message.answer(text, reply_markup=ReplyKeyboardRemove())
    await state.finish()

IMAGE_PATH1 = 'contact1.jpg'  # Изображение для Нарзиева Самира
IMAGE_PATH2 = 'contact2.jpg'  # Изображение для Гугай Алены
IMAGE_PATH3 = 'contact3.jpg'  # Изображение для Хакимовой Тахмины

@dp.message_handler(state=RegistrationStates.help)
@dp.message_handler(text="Centris Towers bilan bog'lanish")
@dp.message_handler(Command("contact"))
async def bot_contact(message: types.Message, state: FSMContext):
    # Текст для Нарзиева Самира (на узбекском)
    caption1 = """Centris Towers  
Нарзиев Самир  
Менеджер  

Murojaat uchun:  
mob: +998501554444 📱  
telegram: @centris1  
ofis: +9989555154444 📞  

📍 Toshkent sh., Nuroniylar ko'chasi, 2. (<a href="https://maps.app.goo.gl/aVBM7bMWRSXZasWy5">Xaritada ko'rish</a>)  

<a href="http://t.me/centris1">Telegram</a> • <a href="https://www.instagram.com/centris.towers/">Instagram</a> • <a href="https://www.facebook.com/centristowers">Facebook</a> • <a href="https://centristowers.uz/">Website</a> • <a href="https://youtube.com/@centrisdevelopment?si=d9FnNGjGb2MesuRY">Youtube</a>"""

    # Текст для Гугай Алены (на узбекском)
    caption2 = """Centris Towers  
Гугай Алена  
Sotuv bo'yicha katta menejer  

Ma'lumot uchun:  
mob: +998958085995 📱  
telegram: @Alyona_CentrisTowers  
ofis: +9989555154444 📞  

📍 Toshkent sh., Nuroniylar ko'chasi, 2. (<a href="https://maps.app.goo.gl/aVBM7bMWRSXZasWy5">Xaritada ko'rish</a>)  

<a href="http://t.me/centris1">Telegram</a> • <a href="https://www.instagram.com/centris.towers/">Instagram</a> • <a href="https://www.facebook.com/centristowers">Facebook</a> • <a href="https://centristowers.uz/">Website</a> • <a href="https://youtube.com/@centrisdevelopment?si=d9FnNGjGb2MesuRY">Youtube</a>"""

    # Текст для Хакимовой Тахмины (на узбекском)
    caption3 = """Centris Towers  
Khakimova Takhmina  
Sotuv menejeri  

Murojaat uchun:  
mob: +998958095995 📱  
telegram: @Takhmina_CentrisTowers  
ofis: +9989555154444 📞  

📍 Toshkent sh., Nuroniylar ko'chasi, 2. (<a href="https://maps.app.goo.gl/aVBM7bMWRSXZasWy5">Xaritada ko'rish</a>)  

<a href="http://t.me/centris1">Telegram</a> • <a href="https://www.instagram.com/centris.towers/">Instagram</a> • <a href="https://www.facebook.com/centristowers">Facebook</a> • <a href="https://centristowers.uz/">Website</a> • <a href="https://youtube.com/@centrisdevelopment?si=d9FnNGjGb2MesuRY">Youtube</a>"""

    # Отправка изображений с подписями
    try:
        # Отправка для Нарзиева Самира
        with open(IMAGE_PATH1, 'rb') as photo:
            await message.answer_photo(
                photo=photo,
                caption=caption1,
                parse_mode='HTML',
                reply_markup=ReplyKeyboardRemove()
            )

        # Отправка для Гугай Алены
        with open(IMAGE_PATH2, 'rb') as photo:
            await message.answer_photo(
                photo=photo,
                caption=caption2,
                parse_mode='HTML',
                reply_markup=ReplyKeyboardRemove()
            )

        # Отправка для Хакимовой Тахмины
        with open(IMAGE_PATH3, 'rb') as photo:
            await message.answer_photo(
                photo=photo,
                caption=caption3,
                parse_mode='HTML',
                reply_markup=get_lang_for_button(message)
            )
    except FileNotFoundError:
        await message.answer("Bir yoki bir nechta rasm topilmadi. Fayl yo'llarini tekshiring.")
    except Exception as e:
        await message.answer(f"Rasmlarni yuborishda xatolik yuz berdi: {str(e)}")

    await state.finish()