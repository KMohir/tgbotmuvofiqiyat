from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.types import ParseMode, Message, ReplyKeyboardRemove
from db import db
from keyboards.default.reply import key, get_lang_for_button
from loader import dp, bot
from states.state import RegistrationStates
from translation import _
import time

# Функция для формирования описания видео
def get_video_caption() -> str:
    caption = (
        "✅1/15\n\n"
        "Мавзу: Centris Towers’даги лобби\n\n"
        "Иброҳим Мамасаидов \"Centris Towers\" лойиҳаси асосчиси\n\n"
        "Centris Towers - инновация ва замонавий услуб гуллаб-яшнайдиган янги авлод бизнес маркази\n\n"
        "📞 Алоқа учун: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
        "<a href=\"https://t.me/centris1\">Менежер билан боғланиш</a>\n\n"
        "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Манзил: Тошкент шаҳри, Нуронийлар кўчаси 2</a>)\n"
        "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
        "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
        "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>"
    )
    return caption

@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    if not db.user_exists(message.from_user.id):
        # Приветственное сообщение только на узбекском
        await bot.send_message(
            message.from_user.id,
            'Assalomu aleykum, Centris Towers yordamchi botiga hush kelibsiz!'
        )
        # Запрашиваем имя без выбора языка
        await message.answer("Ismingizni kiriting")
        await RegistrationStates.name.set()
    else:
        try:
            # Копируем видео из канала без указания источника
            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=-1002550852551,  # ID канала
                message_id=77,  # ID сообщения из ссылки
                caption='',  # Без описания
                parse_mode="HTML",
                reply_markup=get_lang_for_button(message),
                protect_content=True
            )
            print(f"Видео из канала пересыловано пользователю {message.from_user.id}")

        except Exception as exx:
            print(f"Ошибка при пересылке видео: {exx}")
            await message.answer("Video yuborishda xato yuz berdi. Iltimos, keyinroq urinib ko'ring.")

@dp.message_handler(state=RegistrationStates.name)
async def register_name_handler(message: types.Message, state: FSMContext):
    name = message.text
    async with state.proxy() as data:
        data['name'] = name

    # Запрашиваем телефон только на узбекском
    await message.answer("Telefon raqamingizni kiriting", reply_markup=key())
    await RegistrationStates.phone.set()

@dp.message_handler(state=RegistrationStates.phone, content_types=types.ContentType.TEXT)
async def process_phone_text(message: Message, state: FSMContext):
    contact = message.text

    if contact.startswith('+998') and len(contact) == 13:
        await save_user_data(message, state, contact)
    else:
        await message.answer(
            "Telefon raqam noto'g'ri kiritildi, iltimos telefon raqamni +998XXXXXXXXX formatda kiriting yoki 'Kontakni yuborish' tugmasiga bosing.",
            reply_markup=key()
        )
        await RegistrationStates.phone.set()

@dp.message_handler(state=RegistrationStates.phone, content_types=types.ContentType.CONTACT)
async def process_phone_contact(message: Message, state: FSMContext):
    await message.answer("Ro'yxatdan muvaffaqiyatli o'tdingiz!", reply_markup=ReplyKeyboardRemove())
    contact = message.contact.phone_number
    await save_user_data(message, state, contact)

async def save_user_data(message: Message, state: FSMContext, contact: str):
    async with state.proxy() as data:
        name = data.get('name')

        # Сохраняем данные пользователя без языка
        db.update(message.from_user.id, name, contact)

        # Копируем первое видео из канала без указания источника
        try:
            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=-1002550852551,  # ID канала
                message_id=77,  # ID сообщения из ссылки
                caption='',  # Без описания
                parse_mode="HTML",
                reply_markup=get_lang_for_button(message),
                protect_content=True
            )
            print(f"Первое видео из канала пересыловано пользователю {message.from_user.id}")
        except Exception as exx:
            print(f"Ошибка при пересылке первого видео: {exx}")
            await message.answer("Video yuborishda xato yuz berdi. Iltimos, keyinroq urinib ko'ring.")

        # Задержка перед отправкой второго видео
        time.sleep(20)

        # Копируем второе видео из канала с описанием
        try:
            caption = get_video_caption()
            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=-1002550852551,  # ID канала
                message_id=59,  # ID сообщения из ссылки
                caption=caption,  # С описанием
                parse_mode="HTML",
                reply_markup=get_lang_for_button(message),
                protect_content=True
            )
            print(f"Второе видео из канала пересыловано пользователю {message.from_user.id}")
        except Exception as exx:
            print(f"Ошибка при пересылке второго видео: {exx}")
            await message.answer("Video yuborishda xato yuz berdi. Iltimos, keyinroq urinib ko'ring.")

    await state.finish()