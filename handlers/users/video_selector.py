try:
    from aiogram import types
    from aiogram.dispatcher.filters import Command, Text
    from loader import dp, bot
    from db import db
    from keyboards.default.reply import key, get_lang_for_button
    from datetime import datetime
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    from handlers.users.video_lists import VIDEO_LIST_1, VIDEO_LIST_2, VIDEO_LIST_3, VIDEO_LIST_4, CAPTION_LIST_1, CAPTION_LIST_2, CAPTION_LIST_3, CAPTION_LIST_4, VIDEO_LIST_GOLDEN_1, GOLDEN_LAKE_TOPICS, CAPTION_LIST_6, VIDEO_LIST_6
    from aiogram.dispatcher import FSMContext
    from aiogram.dispatcher.filters.state import State, StatesGroup
    from handlers.users.video_lists import CAPTION_LIST_5, VIDEO_LIST_5

    # Список описаний для извлечения названий уроков (только для кнопок)
    CAPTION_LIST_2 = [
        "Келажакни инобатга олган қулай локатсия",
        "Худуд бўйича жойлашув ва нархлар",
        "Парковка масаласи ва тарифлари",
        "Хавфсизлик бўйича талабларга жавобимиз",
        "Меҳмонлар учун қулайликлар",
        "Макетдаги бино қани деб қолмаймизми?",
        "Қарзга олгандан кўра, олмаслик яхшироқ.",
        "Centris Towers қандай ва кимлар учун.",
        "Ўхшамай қолса пулингиз қайтарилади",
        "Бинонинг ташқи худуди.",
        "Фитнес ва автосалоннинг боғлиқлиги.",
        "Аёллар учун ажратилган зона",
        "Нарх сиёсатининг муҳимлиги.",
        'Вид муҳим деб билганлар  учун таклиф.',
        "Сотиш учун олаётганларга тавсия.",
        "Эвакуация кучли ўйланилган.",
        "Бизнес сентр қуриш осонмас…",
        "100% тўлов қилишнинг чегирмаси.",
        "Чет эл фуқаролари ҳам олса бўладими?",
        "Тўлиқ кўрсатув…"
    ]

    CAPTION_LIST_3 = [
        "Centris Towers билан ҳамкорлик шартлари",
        "Ижара нархлари",
        "Centris Towers нинг ташқи тузилиши",
        "Энг оммабоп муаммонинг ечими",
        "Қаҳвахона ёки кафе учун идеал жой",
        "Биздаги 4 хил уникал ресторан",
        "Centris Towers нинг бошқалардан фарқи",
        "Қаҳва бурчак (Coffee Corner) учун таклиф",
        "Бино қурилиши қачон тугайди?",
        "Саволларга жавоб олиш учун кимга мурожаат қилиш керак?",
        "Бизга кимлар қизиқ эмас?",
        "Ёш болалар учун ўйин майдони бўладими?",
        "Автосалон очадиганларга учун имконият",
        "Бино фасади учун режалар",
        "Аёллар учун қулайликлар",
        "Co-working зоналари учун ажратилган имкониятлар",
        "Ижара шартномаси долларда бўладими ёки сўмда?",
        "Нималар мумкин эмас?",
        "Пул оқимида хавфлар борми?",
        "Шартнома учун кимлар билан келишиш керак?",
        "Қандай суғурта (страховка) билан таъминлайди?",
        "Имконият бўлмай қолса, тўланган пуллар нима бўлади?",
        "Таклиф нима учун камаяди?",
        "Нима учун тиллага эмас, кўчмас мулкка пул тиккан маъқул?",
        "Centris Towers девелопер сифатида яқин келажакдаги қурилиш режалари ҳақида фикрингиз",
        "ТОП-3 брендлар қаторида жой олишимиз мумкинми?",
        "Centris Towers расман қачон очилиши мумкин?",
        "Лифтлар билан боғлиқ қулайликлар",
        "Чет элга сармоя киритиш керакми ёки Ўзбекистонга?",
        "Дубай ва Озарбайжонга пул тикиш тўғрими?"
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
    async def cmd_start(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        # Добавляем пользователя в базу данных, если его нет
        if not db.user_exists(user_id):
            db.add_user(user_id, "Не указано", "Не указано", "09:00")
            # Устанавливаем last_sent как текущую дату и время
            db.update_last_sent(user_id, datetime.now())

        await message.answer("Привет! Я бот Centris Towers. Чем могу помочь?",
                             reply_markup=main_menu_keyboard)
        await state.set_state(VideoStates.main_menu.state)


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


    # @dp.message_handler(chat_type=types.ChatType.PRIVATE)
    # async def handle_all_messages(message: types.Message):
    #     user_id = message.from_user.id
    #     print(f"Получено сообщение от {user_id}: {message.text}")
    #     await message.answer("Kechirasiz, men bu buyruqni tushunmayapman. Iltimos, /start dan foydalaning.")


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

        if message.chat.type in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            # Меняем время для группы
            if not db.user_exists(message.chat.id):
                db.add_user(message.chat.id, message.chat.title or "Группа", None, preferred_time=new_time, is_group=True)
            db.set_preferred_time(message.chat.id, new_time)
            await message.reply(f"Время рассылки для этой группы установлено на {new_time}")
        else:
            # Меняем время для пользователя
            if not db.user_exists(message.from_user.id):
                db.add_user(message.from_user.id, "Не указано", "Не указано", preferred_time=new_time)
            db.set_preferred_time(message.from_user.id, new_time)
            await message.reply(f"Время рассылки для вас установлено на {new_time}")

    # Главная клавиатура
    main_menu_keyboard =ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Centris towers"),

            ],
            [
                KeyboardButton(text="Olden lake 1.0")
            ],
            [
                KeyboardButton(text="Centris Towers bilan bog'lanish")
            ],
            [
                KeyboardButton(text="Bino bilan tanishish")
            ],
        ],
        resize_keyboard=True
    )



    # Клавиатура сезонов
    def get_season_keyboard(project=None):
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        if project == "olden_lake":
            keyboard.add(KeyboardButton("Golden lake 1"))
        else:
            keyboard.add(KeyboardButton("Яқинлар 1.0 I I Иброҳим Мамасаидов"))
            keyboard.add(KeyboardButton("Яқинлар 2.0 I I Иброҳим Мамасаидов"))
            keyboard.add(KeyboardButton("Яқинлар 3.0 I I Иброҳим Мамасаидов"))
            keyboard.add(KeyboardButton("Яқинлар 4.0 I I Иброҳим Мамасаидов"))
            keyboard.add(KeyboardButton("Яқинлар 5.0 I I Иброҳим Мамасаидов"))
            keyboard.add(KeyboardButton("Яқинлар I Ташриф Centris Towers"))
        keyboard.add(KeyboardButton("Orqaga qaytish"))
        return keyboard

    # Клавиатура с названиями видео для сезона
    def get_video_keyboard(caption_list):
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for name in caption_list:
            keyboard.add(KeyboardButton(name))
        keyboard.add(KeyboardButton("Orqaga qaytish"))
        return keyboard

    # --- Обработчики ---

    class VideoStates(StatesGroup):
        main_menu = State()
        season_select = State()
        video_select = State()
        project_select = State()  # Новое состояние для выбора проекта

    @dp.message_handler(text="Centris towers")
    async def centris_towers_menu(message: types.Message, state: FSMContext):
        await state.update_data(project="centris")  # Сохраняем выбранный проект
        await message.answer("Sezonni tanlang:", reply_markup=get_season_keyboard())
        await message.answer("Qaysi sezonni ko'rmoqchisiz?")
        await state.set_state(VideoStates.season_select.state)

    @dp.message_handler(text="Olden lake 1.0")
    async def olden_lake_menu(message: types.Message, state: FSMContext):
        await state.update_data(project="olden_lake")
        await message.answer("Sezonni tanlang:", reply_markup=get_season_keyboard(project="olden_lake"))
        await message.answer("Qaysi sezonni ko'rmoqchisiz?")
        await state.set_state(VideoStates.season_select.state)

    @dp.message_handler(lambda m: m.text in [
        "Яқинлар 1.0 I I Иброҳим Мамасаидов",
        "Яқинлар 2.0 I I Иброҳим Мамасаидов",
        "Яқинлар 3.0 I I Иброҳим Мамасаидов",
        "Яқинлар 4.0 I I Иброҳим Мамасаидов",
        "Яқинлар 5.0 I I Иброҳим Мамасаидов",
        "Яқинлар I Ташриф Centris Towers",
        "Golden lake 1"
    ], state=VideoStates.season_select)
    async def season_selection(message: types.Message, state: FSMContext):
        data = await state.get_data()
        project = data.get("project")
        
        if project == "centris":
            if message.text == "Яқинлар 1.0 I I Иброҳим Мамасаидов":
                await message.answer("Darsni tanlang:", reply_markup=get_video_keyboard(CAPTION_LIST_1))
                await state.set_state(VideoStates.video_select.state)
            elif message.text == "Яқинлар 2.0 I I Иброҳим Мамасаидов":
                await message.answer("Darsni tanlang:", reply_markup=get_video_keyboard(CAPTION_LIST_2))
                await state.set_state(VideoStates.video_select.state)
            elif message.text == "Яқинлар 3.0 I I Иброҳим Мамасаидов":
                await message.answer("Darsni tanlang:", reply_markup=get_video_keyboard(CAPTION_LIST_3))
                await state.set_state(VideoStates.video_select.state)
            elif message.text == "Яқинлар 4.0 I I Иброҳим Мамасаидов":
                await message.answer("Darsni tanlang:", reply_markup=get_video_keyboard(CAPTION_LIST_4))
                await state.set_state(VideoStates.video_select.state)
            elif message.text == "Яқинлар 5.0 I I Иброҳим Мамасаидов":
                await message.answer("Darsni tanlang:", reply_markup=get_video_keyboard(CAPTION_LIST_5))
                await state.set_state(VideoStates.video_select.state)
            elif message.text == "Яқинлар I Ташриф Centris Towers":
                await message.answer("Darsni tanlang:", reply_markup=get_video_keyboard(CAPTION_LIST_6))
                await state.set_state(VideoStates.video_select.state)
        elif project == "olden_lake":
            if message.text == "Golden lake 1":
                await message.answer("Darsni tanlang:", reply_markup=get_video_keyboard(GOLDEN_LAKE_TOPICS))
                await state.set_state(VideoStates.video_select.state)
            elif message.text == "Яқинлар 2.0 I I Иброҳим Мамасаидов":
                await message.answer("Olden lake 2-sezon hali tayyor emas")
                await state.set_state(VideoStates.season_select.state)
            elif message.text == "Яқинлар 3.0 I I Иброҳим Мамасаидов":
                await message.answer("Olden lake 3-sezon hali tayyor emas")
                await state.set_state(VideoStates.season_select.state)
            elif message.text == "Яқинлар 4.0 I I Иброҳим Мамасаидов":
                await message.answer("Olden lake 4-sezon hali tayyor emas")
                await state.set_state(VideoStates.season_select.state)
            elif message.text == "Яқинлар 5.0 I I Иброҳим Мамасаидов":
                await message.answer("Olden lake 5-sezon hali tayyor emas")
                await state.set_state(VideoStates.season_select.state)

    @dp.message_handler(text="Orqaga qaytish", state=VideoStates.video_select)
    async def back_to_season_menu(message: types.Message, state: FSMContext):
        await message.answer("Sezonni tanlang:", reply_markup=get_season_keyboard())
        await message.answer("Qaysi sezonni ko'rmoqchisiz?")
        await state.set_state(VideoStates.season_select.state)

    @dp.message_handler(text="Orqaga qaytish", state=VideoStates.season_select)
    async def back_to_main_menu(message: types.Message, state: FSMContext):
        await message.answer("Bosh menyu:", reply_markup=main_menu_keyboard)
        await state.finish()

    @dp.message_handler(Command("centris_towers"))
    async def centris_towers_command(message: types.Message):
        await centris_towers_menu(message)

    @dp.message_handler(Command("olden_lake"))
    async def olden_lake_command(message: types.Message):
        await olden_lake_menu(message)

    @dp.message_handler(lambda m: m.text in CAPTION_LIST_1 + CAPTION_LIST_2 + CAPTION_LIST_3 + CAPTION_LIST_4 + CAPTION_LIST_5 + CAPTION_LIST_6 + GOLDEN_LAKE_TOPICS, state=VideoStates.video_select)
    async def send_video(message: types.Message, state: FSMContext):
        data = await state.get_data()
        project = data.get("project")
        
        video_url = None
        if project == "centris":
            if message.text in CAPTION_LIST_1:
                idx = CAPTION_LIST_1.index(message.text)
                video_url = VIDEO_LIST_1[idx]
            elif message.text in CAPTION_LIST_2:
                idx = CAPTION_LIST_2.index(message.text)
                video_url = VIDEO_LIST_2[idx]
            elif message.text in CAPTION_LIST_3:
                idx = CAPTION_LIST_3.index(message.text)
                video_url = VIDEO_LIST_3[idx]
            elif message.text in CAPTION_LIST_4:
                idx = CAPTION_LIST_4.index(message.text)
                video_url = VIDEO_LIST_4[idx]
            elif message.text in CAPTION_LIST_5:
                idx = CAPTION_LIST_5.index(message.text)
                video_url = VIDEO_LIST_5[idx]
            elif message.text in CAPTION_LIST_6:
                idx = CAPTION_LIST_6.index(message.text)
                video_url = VIDEO_LIST_6[idx]
        elif project == "olden_lake":
            if message.text in GOLDEN_LAKE_TOPICS:
                idx = GOLDEN_LAKE_TOPICS.index(message.text)
                video_url = VIDEO_LIST_GOLDEN_1[idx]
        
        if video_url:
            message_id = int(video_url.split("/")[-1])
            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=-1002550852551,
                message_id=message_id,
                protect_content=True
            )
            # Если это группа — сдвигаем индекс рассылки для группы вперёд и отмечаем просмотренное
            if message.chat.type in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
                # Определяем глобальный индекс видео
                if project == "centris":
                    all_videos = VIDEO_LIST_1 + VIDEO_LIST_2 + VIDEO_LIST_3 + VIDEO_LIST_4 + VIDEO_LIST_5 + VIDEO_LIST_6
                    if message.text in CAPTION_LIST_1:
                        idx = CAPTION_LIST_1.index(message.text)
                        global_idx = idx
                    elif message.text in CAPTION_LIST_2:
                        idx = CAPTION_LIST_2.index(message.text)
                        global_idx = len(CAPTION_LIST_1) + idx
                    elif message.text in CAPTION_LIST_3:
                        idx = CAPTION_LIST_3.index(message.text)
                        global_idx = len(CAPTION_LIST_1) + len(CAPTION_LIST_2) + idx
                    elif message.text in CAPTION_LIST_4:
                        idx = CAPTION_LIST_4.index(message.text)
                        global_idx = len(CAPTION_LIST_1) + len(CAPTION_LIST_2) + len(CAPTION_LIST_3) + idx
                    elif message.text in CAPTION_LIST_5:
                        idx = CAPTION_LIST_5.index(message.text)
                        global_idx = len(CAPTION_LIST_1) + len(CAPTION_LIST_2) + len(CAPTION_LIST_3) + len(CAPTION_LIST_4) + idx
                    elif message.text in CAPTION_LIST_6:
                        idx = CAPTION_LIST_6.index(message.text)
                        global_idx = len(CAPTION_LIST_1) + len(CAPTION_LIST_2) + len(CAPTION_LIST_3) + len(CAPTION_LIST_4) + len(CAPTION_LIST_5) + idx
                    else:
                        global_idx = None
                elif project == "olden_lake":
                    all_videos = VIDEO_LIST_GOLDEN_1
                    if message.text in GOLDEN_LAKE_TOPICS:
                        global_idx = GOLDEN_LAKE_TOPICS.index(message.text)
                    else:
                        global_idx = None
                else:
                    global_idx = None
                if global_idx is not None:
                    db.mark_group_video_as_viewed(message.chat.id, global_idx)
        else:
            await message.answer("Video topilmadi.")

except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('video selector', f"{formatted_date_time}", f"error {exx}")