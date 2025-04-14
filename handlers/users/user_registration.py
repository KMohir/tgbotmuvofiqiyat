from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.types import ParseMode, Message, ReplyKeyboardRemove
from db import db
from keyboards.default.reply import key, get_lang_for_button
from loader import dp, bot
from states.state import RegistrationStates

# Функция для формирования описания видео
def get_video_caption() -> str:
    caption = (
        "✅1/15\n\n"
        "Мавзу: Centris Towers’даги лобби\n\n"
        "Иброҳим Мамасаидов \"Centris Towers\" лойиҳаси асосчиси\n\n"
        "<a href=\"https://youtu.be/Dg4H7JhGRFI\">4К форматда кўриш</a>\n\n"
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
            caption = get_video_caption()
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
    contact = message.contact.phone_number
    await save_user_data(message, state, contact)

async def save_user_data(message: Message, state: FSMContext, contact: str):
    async with state.proxy() as data:
        name = data.get('name')

        # Сохраняем данные пользователя без языка
        db.update(message.from_user.id, name, contact)

        await message.answer("Ro'yxatdan muvaffaqiyatli o'tdingiz!", reply_markup=ReplyKeyboardRemove())

        video_path = 'video_1.mp4'
        caption = get_video_caption()
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