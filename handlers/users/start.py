from datetime import datetime, timedelta
import logging

try:

    from aiogram import types
    from aiogram.dispatcher import FSMContext
    from aiogram.dispatcher.filters.builtin import CommandStart
    from aiogram.types import ParseMode, Message, ReplyKeyboardRemove
    from db import db
    from keyboards.default.reply import key, get_lang_for_button, main_menu_keyboard
    from loader import dp, bot
    from states.state import RegistrationStates
    from translation import _
    import time
    from aiogram.dispatcher.storage import DELTA
    from data.config import SUPER_ADMIN_ID

    # Настройка логирования
    logger = logging.getLogger(__name__)

    # Словарь для хранения времени последнего сообщения от пользователя
    user_last_message = {}

    # Функция для проверки спама
    def is_spam(user_id):
        current_time = time.time()
        if user_id in user_last_message:
            last_message_time = user_last_message[user_id]
            if current_time - last_message_time < 1:  # Минимальный интервал между сообщениями - 1 секунда
                return True
        user_last_message[user_id] = current_time
        return False

    # Функция для формирования описания видео
    def get_video_caption() -> str:
        caption = (
            "✅1/15\n\n"
            "Мавзу: Centris Towers'даги лобби\n\n"
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
    async def bot_start(message: types.Message, state: FSMContext):
        try:
            if is_spam(message.from_user.id):
                logger.warning(f"Обнаружен спам от пользователя {message.from_user.id}")
                return

            # Логируем попытку сброса FSM
            if message.from_user.id == SUPER_ADMIN_ID or db.is_admin(message.from_user.id):
                logger.error(f"Попытка сброса FSM: chat_id={message.chat.id}, user_id={message.from_user.id}")
                await state.finish()
                logger.error(f"FSM сброшен: chat_id={message.chat.id}, user_id={message.from_user.id}")
                await message.answer("FSM (машинное состояние) сброшено командой /start админом.")

            # Если команда из группы — не спрашивать имя, не запускать регистрацию
            if message.chat.type in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
                if not db.user_exists(message.chat.id):
                    db.add_user(message.chat.id, message.chat.title or "Группа", None, is_group=True, group_id=message.chat.id)
                await message.answer("Бот активирован в группе!\nВсе участники могут пользоваться функциями без регистрации.", reply_markup=main_menu_keyboard)
                return

            # В личке — прежняя логика
            if not db.user_exists(message.from_user.id):
                await bot.send_message(
                    message.from_user.id,
                    'Assalomu aleykum, Centris Towers yordamchi botiga hush kelibsiz!'
                )
                await message.answer("Ismingizni kiriting")
                await RegistrationStates.name.set()
            else:
                try:
                    await bot.copy_message(
                        chat_id=message.chat.id,
                        from_chat_id=-1002550852551,
                        message_id=135,
                        caption='',
                        parse_mode="HTML",
                        reply_markup=get_lang_for_button(message),
                        protect_content=True
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке видео пользователю {message.from_user.id}: {e}")
                    await message.answer("Video yuborishda xato yuz berdi. Iltimos, keyinroq urinib ko'ring.")

        except Exception as e:
            logger.error(f"Ошибка в обработчике /start: {e}")
            await message.answer("Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")

    @dp.message_handler(state=RegistrationStates.name)
    async def register_name_handler(message: types.Message, state: FSMContext):
        try:
            if is_spam(message.from_user.id):
                return

            name = message.text
            async with state.proxy() as data:
                data['name'] = name

            await message.answer("Telefon raqamingizni kiriting", reply_markup=key())
            await RegistrationStates.phone.set()
        except Exception as e:
            logger.error(f"Ошибка при обработке имени пользователя {message.from_user.id}: {e}")
            await message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
            await state.finish()

    @dp.message_handler(state=RegistrationStates.phone, content_types=types.ContentType.TEXT)
    async def process_phone_text(message: Message, state: FSMContext):
        try:
            if is_spam(message.from_user.id):
                return

            contact = message.text
            if contact.startswith('+998') and len(contact) == 13:
                await save_user_data(message, state, contact)
            else:
                await message.answer(
                    "Telefon raqam noto'g'ri kiritildi, iltimos telefon raqamni +998XXXXXXXXX formatda kiriting yoki 'Kontakni yuborish' tugmasiga bosing.",
                    reply_markup=key()
                )
                await RegistrationStates.phone.set()
        except Exception as e:
            logger.error(f"Ошибка при обработке текстового номера телефона {message.from_user.id}: {e}")
            await message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
            await state.finish()

    @dp.message_handler(state=RegistrationStates.phone, content_types=types.ContentType.CONTACT)
    async def process_phone_contact(message: Message, state: FSMContext):
        try:
            if is_spam(message.from_user.id):
                return

            contact = message.contact.phone_number
            await save_user_data(message, state, contact)  # Сохраняем пользователя сразу
            await message.answer("Ro'yxatdan muvaffaqiyatli o'tdingiz!")
        except Exception as e:
            logger.error(f"Ошибка при обработке контакта пользователя {message.from_user.id}: {e}")
            await message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
            await state.finish()

    async def save_user_data(message: Message, state: FSMContext, contact: str):
        try:
            async with state.proxy() as data:
                name = data.get('name')
                if message.chat.type in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
                    db.add_user(message.from_user.id, name, contact, group_id=message.chat.id)
                else:
                    db.add_user(message.from_user.id, name, contact)
                db.update(message.from_user.id, name, contact)    # Затем обновляем данные
                caption = get_video_caption()
                try:

                        await bot.copy_message(
                            chat_id=message.chat.id,
                            from_chat_id=-1002550852551,
                            message_id=135,
                            caption='',
                            parse_mode="HTML",
                            reply_markup=get_lang_for_button(message),
                            protect_content=True
                        )
                except Exception as e:
                    logger.error(f"Ошибка при отправке видео после регистрации {message.from_user.id}: {e}")
                    await message.answer("Video yuborishda xato yuz berdi. Iltimos, keyinroq urinib ko'ring.")

                try:
                    print(1)
                except Exception as e:
                    logger.error(f"Ошибка при отправке видео пользователю {message.from_user.id}: {e}")
                    await message.answer("Video yuborishda xato yuz berdi. Iltimos, keyinroq urinib ko'ring.")
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных пользователя {message.from_user.id}: {e}")
            await message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
        finally:
            await state.finish()

except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('start ',  f"{time }formatted_date_time",f"error {exx}" )