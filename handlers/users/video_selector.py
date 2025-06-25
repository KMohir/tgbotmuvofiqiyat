try:
    from aiogram import types
    from aiogram.dispatcher.filters import Command, Text
    from loader import dp, bot
    from db import db
    from keyboards.default.reply import key, get_lang_for_button
    from datetime import datetime
    from handlers.users.video_scheduler import schedule_jobs_for_users

    # Список ссылок на сообщения в канале
    VIDEO_LIST = [
        'https://t.me/c/2550852551/120',
        'https://t.me/c/2550852551/121',
        'https://t.me/c/2550852551/122',
        'https://t.me/c/2550852551/123',
        'https://t.me/c/2550852551/124',
        'https://t.me/c/2550852551/125',
        'https://t.me/c/2550852551/126',
        'https://t.me/c/2550852551/127',
        'https://t.me/c/2550852551/128',
        'https://t.me/c/2550852551/129',
        'https://t.me/c/2550852551/130',
        'https://t.me/c/2550852551/131',
        'https://t.me/c/2550852551/132',
        'https://t.me/c/2550852551/133',
        'https://t.me/c/2550852551/134'
    ]

    # Список описаний для извлечения названий уроков (только для кнопок)
    CAPTION_LIST = [
        "✅1/15\n\n"
        "Мавзу: Centris Towers'daги лобби\n\n"
        "Иброҳим Мамасаидов \"Centris Towers\" лойиҳаси асосчиси\n\n"
        "Centris Towers - инновация ва замонавий услуб гуллаб-яшнайдиган янги авлод бизнес маркази\n\n"
        "📞 Алоқа учун: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
        "<a href=\"https://t.me/centris1\">Менежер билан боғланиш</a>\n\n"
        "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Манзил: Тошкент шаҳри, Нуронийлар кўчаси 2</a>)\n"
        "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
        "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
        "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",

        "✅2/15\n\n"
        "Мавзу: Хизмат кўрсатиш харажатларини камайтириш бўйича режалар\n\n"
        "Иброҳим Мамасаидов \"Centris Towers\" лойиҳаси асосчиси\n\n"
        "<a href=\"https://youtu.be/S3rtsNlAVjU\">4К форматда кўриш</a>\n\n"
        "Centris Towers - инновация ва замонавий услуб гуллаб-яшнайдиган янги авлод бизнес маркази\n\n"
        "📞 Алоқа учун: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
        "<a href=\"https://t.me/centris1\">Менежер билан боғланиш</a>\n\n"
        "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Манзил: Тошкент шаҳри, Нуронийлар кўчаси 2</a>)\n"
        "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
        "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
        "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",

        "✅3/15\n\n"
        "Мавзу: Таъсир қилувчи шахслар ўзимизда I Марказдаги ер нархи ўсиши тезлашган\n\n"
        "Иброҳим Мамасаидов \"Centris Towers\" лойиҳаси асосчиси\n\n"
        "Centris Towers - инновация ва замонавий услуб гуллаб-яшнайдиган янги авлод бизнес маркази  \n\n"
        "📞 Алоқа учун: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
        "<a href=\"https://t.me/centris1\">Менежер билан боғланиш</a>\n\n"
        "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Манзил: Тошкент шаҳри, Нуронийлар кўчаси 2</a>)\n"
        "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
        "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
        "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",

        "✅4/15\n\n"
        "Мавзу: Centris Towers - қўшимча қулайликлари\n\n"
        "Иброҳим Мамасаидов \"Centris Towers\" лойиҳаси асосчиси\n\n"
        "Centris Towers - инновация ва замонавий услуб гуллаб-яшнайдиган янги авлод бизнес маркази  \n\n"
        "📞 Алоқа учун: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
        "<a href=\"https://t.me/centris1\">Менежер билан боғланиш</a>\n\n"
        "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Манзил: Тошкент шаҳри, Нуронийлар кўчаси 2</a>)\n"
        "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
        "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
        "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",

        "✅5/15\n\n"
        "Мавзу: Бино қачон кўринади\n\n"
        "Иброҳим Мамасаидов \"Centris Towers\" лойиҳаси асосчиси\n\n"
        "Centris Towers - инновация ва замонавий услуб гуллаб-яшнайдиган янги авлод бизнес маркази  \n\n"
        "📞 Алоқа учун: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
        "<a href=\"https://t.me/centris1\">Менежер билан боғланиш</a>\n\n"
        "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Манзил: Тошкент шаҳри, Нуронийлар кўчаси 2</a>)\n"
        "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
        "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
        "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",

        "✅6/15\n\n"
        "Мавзу: Парковка сотилмайди\n\n"
        "Иброҳим Мамасаидов \"Centris Towers\" лойиҳаси асосчиси\n\n"
        "Centris Towers - инновация ва замонавий услуб гуллаб-яшнайдиган янги авлод бизнес маркази  \n\n"
        "📞 Алоқа учун: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
        "<a href=\"https://t.me/centris1\">Менежер билан боғланиш</a>\n\n"
        "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Манзил: Тошкент шаҳри, Нуронийлар кўчаси 2</a>)\n"
        "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
        "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
        "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",

        "✅7/15\n\n"
        "Мавзу: Centris Towers-Муваффақият Маркази\n\n"
        "Иброҳим Мамасаидов \"Centris Towers\" лойиҳаси асосчиси\n\n"
        "Centris Towers - инновация ва замонавий услуб гуллаб-яшнайдиган янги авлод бизнес маркази\n\n"
        "📞 Алоқа учун: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
        "<a href=\"https://t.me/centris1\">Менежер билан боғланиш</a>\n\n"
        "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Манзил: Тошкент шаҳри, Нуронийлар кўчаси 2</a>)\n"
        "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
        "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
        "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",

        "✅8/15\n\n"
        "Мавзу: Охирги пулига олинган\n\n"
        "Иброҳим Мамасаидов \"Centris Towers\" лойиҳаси асосчиси\n\n"
        "Centris Towers - инновация ва замонавий услуб гуллаб-яшнайдиган янги авлод бизнес маркази\n\n"
        "📞 Алоқа учун: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
        "<a href=\"https://t.me/centris1\">Менежер билан боғланиш</a>\n\n"
        "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Манзил: Тошкент шаҳри, Нуронийлар кўчаси 2</a>)\n"
        "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
        "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
        "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",

        "✅9/15\n\n"
        "Мавзу: Инвестиция хавфсизлиги\n\n"
        "Иброҳим Мамасаидов \"Centris Towers\" лойиҳаси асосчиси\n\n"
        "Centris Towers - инновация ва замонавий услуб гуллаб-яшнайдиган янги авлод бизнес маркази\n\n"
        "📞 Алоқа учун: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
        "<a href=\"https://t.me/centris1\">Менежер билан боғланиш</a>\n\n"
        "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Манзил: Тошкент шаҳри, Нуронийлар кўчаси 2</a>)\n"
        "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
        "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
        "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",

        "✅10/15\n\n"
        "Мавзу: Қурилиш битишига таъсир қилувчи омиллар\n\n"
        "Иброҳим Мамасаидов \"Centris Towers\" лойиҳаси асосчиси\n\n"
        "Centris Towers - инновация ва замонавий услуб гуллаб-яшнайдиган янги авлод бизнес маркази\n\n"
        "📞 Алоқа учун: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
        "<a href=\"https://t.me/centris1\">Менежер билан боғланиш</a>\n\n"
        "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Манзил: Тошкент шаҳри, Нуронийлар кўчаси 2</a>)\n"
        "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
        "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
        "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",

        "✅11/15\n\n"
        "Мавзу: Манга қўшниларим муҳим\n\n"
        "Иброҳим Мамасаидов \"Centris Towers\" лойиҳаси асосчиси\n\n"
        "Centris Towers - инновация ва замонавий услуб гуллаб-яшнайдиган янги авлод бизнес маркази\n\n"
        "📞 Алоқа учун: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
        "<a href=\"https://t.me/centris1\">Менежер билан боғланиш</a>\n\n"
        "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Манзил: Тошкент шаҳри, Нуронийлар кўчаси 2</a>)\n"
        "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
        "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
        "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",

        "✅12/15\n\n"
        "Мавзу: Бизга қайси сегмент қизиқ\n\n"
        "Иброҳим Мамасаидов \"Centris Towers\" лойиҳаси асосчиси\n\n"
        "Centris Towers - инновация ва замонавий услуб гуллаб-яшнайдиган янги авлод бизнес маркази\n\n"
        "📞 Алоқа учун: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
        "<a href=\"https://t.me/centris1\">Менежер билан боғланиш</a>\n\n"
        "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Манзил: Тошкент шаҳри, Нуронийлар кўчаси 2</a>)\n"
        "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
        "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
        "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",

        "✅13/15\n\n"
        "Мавзу: Centris Towers ғояси\n\n"
        "Иброҳим Мамасаидов \"Centris Towers\" лойиҳаси асосчиси\n\n"
        "Centris Towers - инновация ва замонавий услуб гуллаб-яшнайдиган янги авлод бизнес маркази\n\n"
        "📞 Алоқа учун: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
        "<a href=\"https://t.me/centris1\">Менежер билан боғланиш</a>\n\n"
        "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Манзил: Тошкент шаҳри, Нуронийлар кўчаси 2</a>)\n"
        "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
        "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
        "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",

        "✅14/15\n\n"
        "Мавзу: Centris Towers қулайликлари ва инвестиция бўйича хавфсизлиги\n\n"
        "Иброҳим Мамасаидов \"Centris Towers\" лойиҳаси асосчиси\n\n"
        "Centris Towers - инновация ва замонавий услуб гуллаб-яшнайдиган янги авлод бизнес маркази\n\n"
        "📞 Алоқа учун: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
        "<a href=\"https://t.me/centris1\">Менежер билан боғланиш</a>\n\n"
        "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Манзил: Тошкент шаҳри, Нуронийлар кўчаси 2</a>)\n"
        "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
        "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
        "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",

        "✅15/15\n\n"
        "Мавзу: Centris Towers-Муваффақият Маркази\n\n"
        "Иброҳим Мамасаидов \"Centris Towers\" лойиҳаси асосчиси\n\n"
        "Centris Towers - инновация ва замонавий услуб гуллаб-яшнайдиган янги авлод бизнес маркази\n\n"
        "📞 Алоқа учун: <a href=\"tel:+998501554444\">+998501554444</a>\n\n"
        "<a href=\"https://t.me/centris1\">Менежер билан боғланиш</a>\n\n"
        "(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Манзил: Тошкент шаҳри, Нуронийлар кўчаси 2</a>)\n"
        "🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • "
        "📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • "
        "⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",
    ]


    # Извлечение тем уроков из CAPTION_LIST для кнопок
    def extract_lesson_topics():
        topics = []
        for caption in CAPTION_LIST:
            lines = caption.split("\n")
            for line in lines:
                if line.startswith("Мавзу:"):
                    topic = line.replace("Мавзу:", "").strip()
                    topics.append(topic)
                    break
        return topics


    # Создаём клавиатуру с уроками
    def get_lesson_keyboard():
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        topics = extract_lesson_topics()
        for i, topic in enumerate(topics, start=1):
            button_text = f"{i}. {topic}"
            markup.add(types.KeyboardButton(button_text))

        markup.add(types.KeyboardButton("Orqaga qaytish"))

        return markup


    @dp.message_handler(commands=['start'])
    async def cmd_start(message: types.Message):
        user_id = message.from_user.id
        # Добавляем пользователя в базу данных, если его нет
        if not db.user_exists(user_id):
            db.add_user(user_id, "Не указано", "Не указано", "09:00")
            # Устанавливаем last_sent как текущую дату и время
            db.update_last_sent(user_id, datetime.now())

        await message.answer("Привет! Я бот Centris Towers. Чем могу помочь?",
                             reply_markup=get_lang_for_button(message))


    @dp.message_handler(text="Unsubscribe")
    async def cmd_unsubscribe(message: types.Message):
        user_id = message.from_user.id
        if not db.user_exists(user_id):
            await message.answer("Iltimos, /start buyrug'i bilan ro'yxatdan o'ting.")
            return

        db.unsubscribe_user(user_id)
        await message.answer("Siz obunadan chiqdingiz. Qayta obuna bo'lish uchun /start ni bosing.")


    @dp.message_handler(Command("videos"))
    @dp.message_handler(Text(equals="FAQ ?"))
    async def cmd_videos(message: types.Message):
        # Только для лички требуем регистрацию
        if message.chat.type == types.ChatType.PRIVATE:
            user_id = message.from_user.id
            if not db.user_exists(user_id):
                await message.answer("Iltimos, /start buyrug'i bilan ro'yxatdan o'ting.")
                return
            is_subscribed = db.get_subscription_status(user_id)
            if not is_subscribed:
                await message.answer("Siz obunadan chiqgansiz. Qayta obuna bo'lish uchun /start ni bosing.")
                return
        await message.answer(
            "Iltimos, qaysi darsni ko'rmoqchi ekanligingizni tanlang:",
            reply_markup=get_lesson_keyboard()
        )


    @dp.message_handler(Text(equals="Orqaga qaytish"))
    async def cancel_selection(message: types.Message):
        user_id = message.from_user.id
        print(f"Пользователь {user_id} нажал 'Orqaga qaytish'")

        if not db.user_exists(user_id):
            print(f"Пользователь {user_id} не зарегистрирован")
            await message.answer("Iltimos, /start buyrug'i bilan ro'yxatdan o'ting.")
            return

        await message.answer(
            "Bosh sahifaga qaytdi",
            reply_markup=get_lang_for_button(message)
        )
        print(f"Выбор отменён для пользователя {user_id}, показаны команды как в /start")


    @dp.message_handler(lambda message: any(message.text.startswith(f"{i}.") for i in range(1, 16)))
    async def send_selected_lesson(message: types.Message):
        # Только для лички требуем регистрацию
        if message.chat.type == types.ChatType.PRIVATE:
            user_id = message.from_user.id
            if not db.user_exists(user_id):
                await message.answer("Iltimos, /start buyrug'i bilan ro'yxatdan o'ting.")
                return
        try:
            lesson_number = int(message.text.split(".")[0])
            video_index = lesson_number - 1
            if video_index < 0 or video_index >= len(VIDEO_LIST):
                await message.answer("Bunday dars mavjud emas! Iltimos, mavjud darslardan birini tanlang.")
                return
            video_url = VIDEO_LIST[video_index]
            message_id = int(video_url.split("/")[-1])
            # Отправляем видео в тот же чат, откуда пришёл запрос
            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=-1002550852551,
                message_id=message_id,
                protect_content=True,
                reply_markup=get_lesson_keyboard()
            )
            # Отмечаем просмотр только для лички
            if message.chat.type == types.ChatType.PRIVATE:
                db.mark_video_as_viewed(message.from_user.id, video_index)
        except (ValueError, IndexError) as e:
            await message.answer("Xato! Iltimos, darsni to'g'ri tanlang.")
        except Exception as e:
            await message.answer("Video yuborishda xato yuz berdi. Iltimos, keyinroq urinib ko'ring.")


    @dp.message_handler(chat_type=types.ChatType.PRIVATE)
    async def handle_all_messages(message: types.Message):
        user_id = message.from_user.id
        print(f"Получено сообщение от {user_id}: {message.text}")
        await message.answer("Izvinite, men bu buyruqni tushunmayapman. Iltimos, /start dan foydalaning.")


    @dp.message_handler(commands=['set_time'])
    async def set_time_command(message: types.Message):
        args = message.get_args()
        if not args or not args.strip():
            await message.reply("Пожалуйста, укажите время в формате HH:MM, например: /set_time 09:00")
            return

        new_time = args.strip()
        try:
            hour, minute = map(int, new_time.split(":"))
            assert 0 <= hour < 24 and 0 <= minute < 60
        except Exception:
            await message.reply("Неверный формат времени. Пример: /set_time 09:00")
            return

        # Для групп
        if message.chat.type in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            if not db.user_exists(message.chat.id):
                db.add_user(message.chat.id, message.chat.title or "Группа", None, preferred_time=new_time, is_group=True)
            db.set_preferred_time(message.chat.id, new_time)
            await message.reply(f"Время рассылки для этой группы установлено на {new_time}")
            schedule_jobs_for_users()
        else:
            # Для лички
            if not db.user_exists(message.from_user.id):
                db.add_user(message.from_user.id, "Не указано", "Не указано", preferred_time=new_time)
            db.set_preferred_time(message.from_user.id, new_time)
            await message.reply(f"Время рассылки для вас установлено на {new_time}")
            schedule_jobs_for_users()

except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('video selector', f"{formatted_date_time}", f"error {exx}")