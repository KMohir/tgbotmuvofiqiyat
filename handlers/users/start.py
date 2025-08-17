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
    async def bot_start(message: types.Message):
        try:
            if is_spam(message.from_user.id):
                logger.warning(f"Обнаружен спам от пользователя {message.from_user.id}")
                return

            user_id = message.from_user.id
            
            # Проверяем, не находится ли пользователь уже в процессе регистрации
            current_state = dp.current_state(user=user_id, chat=message.chat.id)
            if current_state:
                current_state_data = await current_state.get_state()
                if current_state_data and current_state_data.startswith('RegistrationStates:'):
                    await message.answer("⏳ **Siz allaqachon ro'yxatdan o'tish jarayonida!**\n\nIltimos, avvalgi xabarni to'ldiring.")
                    return

            if not db.user_exists(user_id):
                logger.info(f"Foydalanuvchi {user_id} ro'yxatdan o'tishni boshladi")
                await bot.send_message(
                    message.from_user.id,
                    'Assalomu aleykum, Centris Towers yordamchi botiga hush kelibsiz!'
                )
                await message.answer("Ismingizni kiriting")
                await RegistrationStates.name.set()
            else:
                logger.info(f"Foydalanuvchi {user_id} allaqachon ro'yxatdan o'tgan")
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

            user_id = message.from_user.id
            
            # Дополнительная проверка - не зарегистрирован ли уже пользователь
            if db.user_exists(user_id):
                logger.warning(f"Foydalanuvchi {user_id} allaqachon ro'yxatdan o'tgan, lekin name state da")
                await message.answer("❌ **Siz allaqachon ro'yxatdan o'tgansiz!**")
                await state.finish()
                return

            name = message.text.strip()
            if len(name) < 2:
                await message.answer("❌ **Ism juda qisqa**\n\nIltimos, kamida 2 ta belgi kiriting:")
                return
                
            if len(name) > 100:
                await message.answer("❌ **Ism juda uzun**\n\nIltimos, 100 belgidan kam bo'lgan ism kiriting:")
                return

            async with state.proxy() as data:
                data['name'] = name

            logger.info(f"Foydalanuvchi {user_id} ismini kiritdi: {name}")
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

            user_id = message.from_user.id
            
            # Дополнительная проверка - не зарегистрирован ли уже пользователь
            if db.user_exists(user_id):
                logger.warning(f"Foydalanuvchi {user_id} allaqachon ro'yxatdan o'tgan, lekin phone state da")
                await message.answer("❌ **Siz allaqachon ro'yxatdan o'tgansiz!**")
                await state.finish()
                return

            contact = message.text.strip()
            if contact.startswith('+998') and len(contact) == 13:
                logger.info(f"Foydalanuvchi {user_id} telefon raqamini kiritdi: {contact}")
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

            user_id = message.from_user.id
            
            # Дополнительная проверка - не зарегистрирован ли уже пользователь
            if db.user_exists(user_id):
                logger.warning(f"Foydalanuvchi {user_id} allaqachon ro'yxatdan o'tgan, lekin phone contact state da")
                await message.answer("❌ **Siz allaqachon ro'yxatdan o'tgansiz!**")
                await state.finish()
                return

            contact = message.contact.phone_number
            logger.info(f"Foydalanuvchi {user_id} kontakt orqali telefon raqamini yubordi: {contact}")
            await save_user_data(message, state, contact)  # Сохраняем пользователя сразу
            await message.answer("Ro'yxatdan muvaffaqiyatli o'tdingiz!", reply_markup=ReplyKeyboardRemove())
        except Exception as e:
            logger.error(f"Ошибка при обработке контакта пользователя {message.from_user.id}: {e}")
            await message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
            await state.finish()

    async def save_user_data(message: Message, state: FSMContext, contact: str):
        try:
            user_id = message.from_user.id
            
            # Финальная проверка - не зарегистрирован ли уже пользователь
            if db.user_exists(user_id):
                logger.warning(f"Foydalanuvchi {user_id} allaqachon ro'yxatdan o'tgan, save_user_data da")
                await message.answer("❌ **Siz allaqachon ro'yxatdan o'tgansiz!**")
                await state.finish()
                return

            async with state.proxy() as data:
                name = data.get('name')
                
            logger.info(f"Foydalanuvchi {user_id} ro'yxatdan o'tishni yakunladi: {name}, {contact}")
            
            # Сначала добавляем пользователя
            success = db.add_user(user_id, name, contact)
            if not success:
                logger.warning(f"Foydalanuvchi {user_id} ni qo'shishda xatolik yoki allaqachon mavjud")
                await message.answer("❌ **Xatolik yuz berdi yoki siz allaqachon ro'yxatdan o'tgansiz!**")
                await state.finish()
                return
            
            # Затем обновляем данные (если нужно)
            db.update(user_id, name, contact)
            
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
                logger.info(f"Foydalanuvchi {user_id} ga video yuborildi")
            except Exception as e:
                logger.error(f"Ошибка при отправке видео после регистрации {user_id}: {e}")
                await message.answer("Video yuborishda xato yuz berdi. Iltimos, keyinroq urinib ko'ring.")

        except Exception as e:
            logger.error(f"Ошибка при сохранении данных пользователя {user_id}: {e}")
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