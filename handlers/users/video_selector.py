import logging
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters import Text, Command
from loader import bot, dp
from db import db
from keyboards.default.reply import key, get_lang_for_button
from datetime import datetime
from handlers.users.video_lists import VIDEO_LIST_1, VIDEO_LIST_2, VIDEO_LIST_3, VIDEO_LIST_4, CAPTION_LIST_1, CAPTION_LIST_2, CAPTION_LIST_3, CAPTION_LIST_4, VIDEO_LIST_GOLDEN_1, GOLDEN_LIST, CAPTION_LIST_6, VIDEO_LIST_6
from data.config import ADMINS

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
        if message.chat.type in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            db.add_user(user_id, "Не указано", "Не указано", "09:00", group_id=message.chat.id)
        else:
            db.add_user(user_id, "Не указано", "Не указано", "09:00")
            # Устанавливаем last_sent как текущую дату и время
            db.update_last_sent(user_id, datetime.now())

    await message.answer("Привет! Я бот Centris Towers. Чем могу помочь?",
                         reply_markup=main_menu_keyboard)
    await state.set_state(VideoStates.main_menu.state)

@dp.message_handler(text="Unsubscribe")
async def cmd_unsubscribe(message: types.Message):
    user_id = message.from_user.id
    db.unsubscribe_user(user_id)
    await message.answer("Siz obunadan chiqdingiz. Qayta obuna bo'lish uchun /start ni bosing.")

@dp.message_handler(Command("videos"))
@dp.message_handler(Text(equals="FAQ ?"))
async def cmd_videos(message: types.Message):
    await message.answer(
        "Iltimos, qaysi darsni ko'rmoqchi ekanligingizni tanlang:",
        reply_markup=get_lesson_keyboard()
    )

@dp.message_handler(lambda message: any(message.text.startswith(f"{i}.") for i in range(1, 16)))
async def send_selected_lesson(message: types.Message):
    try:
        lesson_number = int(message.text.split(".")[0])
        video_index = lesson_number - 1
        if video_index < 0 or video_index >= len(VIDEO_LIST):
            await message.answer("Bunday dars mavjud emas! Iltimos, mavjud darslardan birini tanlang.")
            return
        video_url = VIDEO_LIST[video_index]
        message_id = int(video_url.split("/")[-1])
        await bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=-1002550852551,
            message_id=message_id,
            protect_content=True,
            reply_markup=get_lesson_keyboard()
        )
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
            db.add_user(message.chat.id, message.chat.title or "Группа", None, preferred_time=new_time, is_group=True, group_id=message.chat.id)
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
            KeyboardButton(text="Golden lake")
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
        # Получаем сезоны Golden Lake из базы данных
        golden_seasons = db.get_seasons_by_project("golden")
        for season_id, season_name in golden_seasons:
            keyboard.add(KeyboardButton(season_name))
    else:
        # Получаем сезоны Centris Towers из базы данных
        centris_seasons = db.get_seasons_by_project("centr")
        for season_id, season_name in centris_seasons:
            keyboard.add(KeyboardButton(season_name))
    
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

@dp.message_handler(text="Golden lake")
async def olden_lake_menu(message: types.Message, state: FSMContext):
    await state.update_data(project="olden_lake")
    await message.answer("Sezonni tanlang:", reply_markup=get_season_keyboard(project="olden_lake"))
    await message.answer("Qaysi sezonni ko'rmoqchisiz?")
    await state.set_state(VideoStates.season_select.state)

@dp.message_handler(state=VideoStates.season_select)
async def season_selection(message: types.Message, state: FSMContext):
    data = await state.get_data()
    project = data.get("project")
    season_name = message.text.strip()
    
    logging.warning(f"season_selection: project={project}, message.text={season_name}")
    
    if not project:
        await message.answer("Ошибка: не выбран проект. Попробуйте заново из главного меню.")
        return
    
    if season_name == "Orqaga qaytish":
        await back_to_main_menu(message, state)
        return
    
    # Получаем сезон из базы данных
    season_data = db.get_season_by_name(season_name)
    if not season_data:
        await message.answer("Сезон не найден. Попробуйте выбрать другой сезон.")
        return
    
    season_id, season_project, season_name = season_data
    
    # Проверяем, что сезон принадлежит выбранному проекту
    if project == "centris" and season_project != "centr":
        await message.answer("Этот сезон не принадлежит проекту Centris Towers.")
        return
    elif project == "olden_lake" and season_project != "golden":
        await message.answer("Этот сезон не принадлежит проекту Golden Lake.")
        return
    
    # Получаем видео для этого сезона
    videos = db.get_videos_by_season_name(season_name)
    if not videos:
        await message.answer("В этом сезоне нет видео.")
        return
    
    # Создаем клавиатуру с названиями видео
    video_titles = [video[1] for video in videos]  # video[1] - это title
    keyboard = get_video_keyboard(video_titles)
    
    # Сохраняем информацию о сезоне в состоянии
    await state.update_data(season_id=season_id, season_name=season_name, videos=videos)
    
    await message.answer("Darsni tanlang:", reply_markup=keyboard)
    await state.set_state(VideoStates.video_select.state)

@dp.message_handler(text="Orqaga qaytish", state=VideoStates.video_select)
async def back_to_season_menu(message: types.Message, state: FSMContext):
    data = await state.get_data()
    project = data.get("project")
    if project == "olden_lake":
        await message.answer("Sezonni tanlang:", reply_markup=get_season_keyboard(project="olden_lake"))
    else:
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

@dp.message_handler(state=VideoStates.video_select)
async def send_video(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        project = data.get("project")
        videos = data.get("videos", [])
        season_name = data.get("season_name")
        
        if message.text == "Orqaga qaytish":
            await back_to_season_menu(message, state)
            return
        
        # Ищем видео по названию
        video_url = None
        video_position = None
        for url, title, position in videos:
            if title == message.text:
                video_url = url
                video_position = position
                break
        
        if video_url:
            message_id = int(video_url.split("/")[-1])
            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=-1002550852551,
                message_id=message_id,
                protect_content=True
            )

            # Если это группа — отмечаем видео как просмотренное
            if message.chat.type in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
                # Создаем уникальный идентификатор для группы и сезона
                if project == "centris":
                    group_key = f"centris_{message.chat.id}_{season_name}"
                elif project == "olden_lake":
                    group_key = f"golden_{message.chat.id}"
                else:
                    group_key = f"{project}_{message.chat.id}"
                
                # Отмечаем видео как просмотренное
                db.mark_group_video_as_viewed(group_key, video_position)
        else:
            await message.answer("Video topilmadi.")
    except Exception as exx:
        from datetime import datetime
        now = datetime.now()
        formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
        print('video selector', f"{formatted_date_time}", f"error {exx}")