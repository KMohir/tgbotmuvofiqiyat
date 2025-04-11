from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.types import ParseMode, Message, ReplyKeyboardRemove
from db import db
from keyboards.default.reply import key, get_lang_for_button
from keyboards.inline.support import langMenu
from loader import dp, bot
from states.state import RegistrationStates
from translation import _

# Глобальная переменная lang (можно перенести в состояние, если нужно)
global lang

# Функция для формирования описания видео при регистрации
def get_video_caption(lang: str) -> str:
    if lang == "uz":
        caption = (
            "Тема: Лобби в Centris Towers\n\n"
            "Ибрагим Мамасаидов, основатель проекта \"Centris Towers\"\n\n"
            "Centris Towers - инновационный бизнес-центр нового поколения, где процветают современный стиль и инновации\n\n"
            "📞 Для связи: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
            "<a href=\"https://t.me/centris1\">Связаться с менеджером</a>\n\n"
            "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Адрес: г. Ташкент, ул. Нуронийлар, 2</a>)\n"
            "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
            "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
            "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>"
        )
    else:  # lang == "ru"
        caption = (
            "Тема: Лобби в Centris Towers\n\n"
            "Ибрагим Мамасаидов, основатель проекта \"Centris Towers\"\n\n"
            "Centris Towers - инновационный бизнес-центр нового поколения, где процветают современный стиль и инновации\n\n"
            "📞 Для связи: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
            "<a href=\"https://t.me/centris1\">Связаться с менеджером</a>\n\n"
            "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Адрес: г. Ташкент, ул. Нуронийлар, 2</a>)\n"
            "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
            "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
            "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>"
        )
    return caption

@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    if not db.user_exists(message.from_user.id):
        await bot.send_message(
            message.from_user.id,
            'Assalomu aleykum, Centris Towers yordamchi botiga hush kelibsiz!\nЗдравствуйте, добро пожаловать в бот поддержки Centris Towers!'
        )
        await bot.send_message(
            message.from_user.id,
            'Tilni tanlang:\nВыберите язык:',
            reply_markup=langMenu
        )
        await RegistrationStates.lang.set()
    else:
        try:
            lang = db.get_lang(message.from_user.id)
            caption = get_video_caption(lang)
            video_path = 'Centris.mp4'
            with open(video_path, 'rb') as video:
                await bot.send_video(
                    chat_id=message.chat.id,
                    video=video,
                    caption=caption,
                    parse_mode="HTML",
                    supports_streaming=True,
                    reply_markup=get_lang_for_button(message),
                    protect_content=True
                )
        except Exception as exx:
            print(exx)
            await bot.send_message(
                message.from_user.id,
                "Buyruqlar ro'yxati:\n/ask - Texnik yordamga habar yozish\n/change_language - Tilni o'zgartish\n/about - Centris Towers haqida bilish\n/get_registration_time - Узнать время регистрации",
                reply_markup=get_lang_for_button(message)
            )

@dp.message_handler(state=RegistrationStates.name)
async def register_name_handler(message: types.Message, state: FSMContext):
    name = message.text
    async with state.proxy() as data:
        data['name'] = name
        lang = data.get('lang')

    if lang == "uz":
        await message.answer("Telefon raqamingizni kiriting", reply_markup=key(lang))
    elif lang == "ru":
        await message.answer("Введите свой номер телефона", reply_markup=key(lang))
    await RegistrationStates.phone.set()

@dp.message_handler(state=RegistrationStates.phone, content_types=types.ContentType.TEXT)
async def process_phone_text(message: Message, state: FSMContext):
    contact = message.text
    async with state.proxy() as data:
        lang = data.get('lang')

    if contact.startswith('+998') and len(contact) == 13:
        await save_user_data(message, state, contact)
    else:
        if lang == "uz":
            await message.answer(
                "Telefon raqam noto'g'ri kiritildi, iltimos telefon raqamni +998XXXXXXXXX formatda kiriting yoki 'Kontakni yuborish' tugmasiga bosing.",
                reply_markup=key(lang))
        elif lang == "ru":
            await message.answer(
                "Номер телефона введен неверно, пожалуйста, введите номер в формате +998XXXXXXXXX или нажмите кнопку 'Отправить контакт'.",
                reply_markup=key(lang))
        await RegistrationStates.phone.set()

@dp.message_handler(state=RegistrationStates.phone, content_types=types.ContentType.CONTACT)
async def process_phone_contact(message: Message, state: FSMContext):
    contact = message.contact.phone_number
    await save_user_data(message, state, contact)

async def save_user_data(message: Message, state: FSMContext, contact: str):
    async with state.proxy() as data:
        lang = data.get('lang')
        name = data.get('name')

        db.update(lang, message.from_user.id, name, contact)

        await message.answer(_("Ro'yxatdan muvaffaqiyatli o'tdingiz!", lang), reply_markup=ReplyKeyboardRemove())

        video_path = 'video_1.mp4'
        caption = get_video_caption(lang)
        with open(video_path, 'rb') as video:
            await bot.send_video(
                chat_id=message.chat.id,
                video=video,
                caption=caption,
                parse_mode="HTML",
                supports_streaming=True,
                reply_markup=get_lang_for_button(message),
                protect_content=True
            )

    await state.finish()