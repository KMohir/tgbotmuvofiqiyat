try:
    from aiogram import types
    from aiogram.dispatcher.filters import Command, Text
    from loader import dp, bot
    from db import db
    from keyboards.default.reply import key, get_lang_for_button
    from datetime import datetime

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
        "Мавзу: Centris Towers’даги лобби\n\n"
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
        user_id = message.from_user.id
        print(f"Пользователь {user_id} выбрал урок: {message.text}")

        if not db.user_exists(user_id):
            print(f"Пользователь {user_id} не зарегистрирован")
            await message.answer("Iltimos, /start buyrug'i bilan ro'yxatdan o'ting.")
            return

        try:
            lesson_number = int(message.text.split(".")[0])
            video_index = lesson_number - 1

            if video_index < 0 or video_index >= len(VIDEO_LIST):
                await message.answer("Bunday dars mavjud emas! Iltimos, mavjud darslardan birini tanlang.")
                print(f"Ошибка: урок {lesson_number} вне диапазона")
                return

            # Извлекаем message_id из ссылки
            video_url = VIDEO_LIST[video_index]
            message_id = int(video_url.split("/")[-1])

            # Копируем видео из канала без указания источника
            print(f"Копирование видео из канала {video_url} пользователю {user_id} (dars #{lesson_number})")
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=-1002550852551,  # ID канала
                message_id=message_id,
                protect_content=True,
                reply_markup=get_lesson_keyboard()  # Показываем клавиатуру с уроками
            )
            print(f"Dars #{lesson_number} скопирован пользователю {user_id}")

            # Отмечаем видео как просмотренное
            db.mark_video_as_viewed(user_id, video_index)
            print(f"Видео {video_index} отмечено как просмотренное для пользователя {user_id}")

            # Обновляем video_index в базе данных



        except (ValueError, IndexError) as e:
            await message.answer("Xato! Iltimos, darsni to'g'ri tanlang.")
            print(f"Ошибка при выборе урока для пользователя {user_id}: {e}")
        except Exception as e:
            await message.answer("Video yuborishda xato yuz berdi. Iltimos, keyinroq urinib ko'ring.")
            print(f"Ошибка при копировании видео для пользователя {user_id}: {e}")


    @dp.message_handler()
    async def handle_all_messages(message: types.Message):
        user_id = message.from_user.id
        print(f"Получено сообщение от {user_id}: {message.text}")
        await message.answer("Izvinite, men bu buyruqni tushunmayapman. Iltimos, /start dan foydalaning.")

except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('video selector', f"{formatted_date_time}", f"error {exx}")