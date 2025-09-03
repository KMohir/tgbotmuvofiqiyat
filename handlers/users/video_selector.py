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

# Настройка логирования
logger = logging.getLogger(__name__)

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

# Используем CAPTION_LIST_1 вместо неопределенной CAPTION_LIST
CAPTION_LIST = CAPTION_LIST_1
VIDEO_LIST = VIDEO_LIST_1

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

@dp.message_handler(commands=["start", "start@CentrisTowersbot"], chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
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

    await message.answer("Bosh menyu:", reply_markup=get_main_menu_keyboard())
    await state.finish()

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

# Главная клавиатура - теперь динамическая
def get_main_menu_keyboard():
    """
    Создает динамическое главное меню с актуальными данными
    """
    try:
        # Получаем количество сезонов для каждого проекта
        centris_seasons = db.get_seasons_by_project("centris")
        golden_seasons = db.get_seasons_by_project("golden")
        
        centris_count = len(centris_seasons)
        golden_count = len(golden_seasons)
        
        # Создаем клавиатуру с количеством сезонов
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=f"Centris towers ({centris_count} сезонов)"),
                ],
                [
                    KeyboardButton(text=f"Golden lake ({golden_count} сезонов)")
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
        
        logger.info(f"Создано главное меню: Centris ({centris_count}), Golden ({golden_count})")
        return keyboard
        
    except Exception as e:
        logger.error(f"Ошибка при создании главного меню: {e}")
        # Возвращаем базовую клавиатуру в случае ошибки
        return ReplyKeyboardMarkup(
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

def force_update_main_menu():
    """
    Принудительно обновляет главное меню, очищая все кэши
    """
    try:
        logger.info("🔄 Принудительное обновление главного меню...")
        
        # Очищаем кэш сезонов
        clear_season_keyboard_cache()
        
        # Получаем свежее главное меню
        fresh_menu = get_main_menu_keyboard()
        
        logger.info("✅ Главное меню принудительно обновлено")
        return fresh_menu
        
    except Exception as e:
        logger.error(f"❌ Ошибка при принудительном обновлении главного меню: {e}")
        return None

# Старая статическая клавиатура (для обратной совместимости)
main_menu_keyboard = ReplyKeyboardMarkup(
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

# Клавиатура сезонов — всегда динамически из базы

# Кэш для клавиатур сезонов
_season_keyboard_cache = {}
_cache_timestamp = {}

def get_season_keyboard(project=None):
    """
    Создает клавиатуру с сезонами для указанного проекта.
    Упрощенная версия без сложного кэширования.
    """
    logger.info(f"=== НАЧАЛО get_season_keyboard ===")
    logger.info(f"Параметр project: {project}")
    
    # Всегда получаем свежие данные из БД
    logger.info(f"Получаем свежие данные из БД для проекта {project}")
    
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    
    if project == "golden":
        seasons = db.get_seasons_by_project("golden")
        logger.info(f"Найдено сезонов Golden Lake: {len(seasons)}")
    else:
        seasons = db.get_seasons_by_project("centris")
        logger.info(f"Найдено сезонов Centris Towers: {len(seasons)}")
    
    for season_id, season_name in seasons:
        keyboard.add(KeyboardButton(season_name))
        logger.info(f"Добавлена кнопка: {season_name}")
    
    keyboard.add(KeyboardButton("Orqaga qaytish"))
    logger.info("Добавлена кнопка 'Orqaga qaytish'")
    
    logger.info(f"✅ Клавиатура создана с {len(keyboard.keyboard)} кнопками")
    logger.info(f"=== КОНЕЦ get_season_keyboard ===")
    
    return keyboard

def clear_season_keyboard_cache(project=None):
    """
    Очищает кэш клавиатуры сезонов для указанного проекта.
    Упрощенная версия.
    """
    logger.info(f"Очистка кэша для проекта: {project}")
    
    try:
        if project:
            cache_key = f"seasons_{project}"
            if cache_key in _season_keyboard_cache:
                del _season_keyboard_cache[cache_key]
                logger.info(f"✅ Кэш очищен для проекта {project}")
            if cache_key in _cache_timestamp:
                del _cache_timestamp[cache_key]
        else:
            # Очищаем весь кэш
            _season_keyboard_cache.clear()
            _cache_timestamp.clear()
            logger.info("✅ Весь кэш очищен")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке кэша: {e}")
    
    logger.info("Кэш очищен")

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

# Centris towers — для всех (упрощенная версия как у Golden Lake)
@dp.message_handler(lambda message: message.text and message.text.startswith("Centris towers"), chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP, types.ChatType.PRIVATE], state="*")
@dp.message_handler(commands=["centris_towers", "centris_towers@CentrisTowersbot"], chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP, types.ChatType.PRIVATE], state="*")
async def centris_towers_menu(message: types.Message, state: FSMContext):
    logger.info(f"=== НАЧАЛО centris_towers_menu ===")
    logger.info(f"Пользователь: {message.from_user.id} ({message.from_user.username})")
    logger.info(f"Чат: {message.chat.id} ({message.chat.type})")
    
    await state.update_data(project="centris")
    
    # Простая очистка кэша как у Golden Lake
    logger.info("Очищаем кэш для Centris Towers")
    clear_season_keyboard_cache("centris")
    
    # Получаем клавиатуру
    logger.info("Получаем клавиатуру для Centris Towers")
    season_keyboard = get_season_keyboard("centris")
    
    logger.info(f"Отправляем клавиатуру с {len(season_keyboard.keyboard)} кнопками")
    await message.answer("Sezonni tanlang:", reply_markup=season_keyboard)
    await message.answer("Qaysi sezonni ko'rmoqchisiz?")
    await state.set_state(VideoStates.season_select.state)
    
    logger.info(f"=== КОНЕЦ centris_towers_menu ===")

# Golden lake — для всех (упрощенная версия как у Centris Towers)
@dp.message_handler(lambda message: message.text and message.text.startswith("Golden lake"), chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP, types.ChatType.PRIVATE], state="*")
@dp.message_handler(commands=["golden_lake", "golden_lake@CentrisTowersbot"], chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP, types.ChatType.PRIVATE], state="*")
async def golden_lake_menu(message: types.Message, state: FSMContext):
    logger.info(f"=== НАЧАЛО golden_lake_menu ===")
    logger.info(f"Пользователь: {message.from_user.id} ({message.from_user.username})")
    logger.info(f"Чат: {message.chat.id} ({message.chat.type})")
    
    await state.update_data(project="golden")
    
    # Простая очистка кэша как у Centris Towers
    logger.info("Очищаем кэш для Golden Lake")
    clear_season_keyboard_cache("golden")
    
    # Получаем клавиатуру
    logger.info("Получаем клавиатуру для Golden Lake")
    season_keyboard = get_season_keyboard("golden")
    
    logger.info(f"Отправляем клавиатуру с {len(season_keyboard.keyboard)} кнопками")
    await message.answer("Sezonni tanlang:", reply_markup=season_keyboard)
    await message.answer("Qaysi sezonni ko'rmoqchisiz?")
    await state.set_state(VideoStates.season_select.state)
    
    logger.info(f"=== КОНЕЦ golden_lake_menu ===")

# Centris Towers bilan bog'lanish — для всех
@dp.message_handler(text="Centris Towers bilan bog'lanish", chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP, types.ChatType.PRIVATE], state="*")
@dp.message_handler(commands=["contact", "contact@CentrisTowersbot"], chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP, types.ChatType.PRIVATE], state="*")
async def centris_contact(message: types.Message, state: FSMContext):
    # Пути к изображениям
    IMAGE_PATH1 = 'contact1.jpg'  # Изображение для Нарзиева Самира
    IMAGE_PATH2 = 'contact2.jpg'  # Изображение для Гугай Алены
    IMAGE_PATH3 = 'contact3.jpg'  # Изображение для Хакимовой Тахмины

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
                parse_mode='HTML'
            )

        # Отправка для Гугай Алены
        with open(IMAGE_PATH2, 'rb') as photo:
            await message.answer_photo(
                photo=photo,
                caption=caption2,
                parse_mode='HTML'
            )

        # Отправка для Хакимовой Тахмины
        with open(IMAGE_PATH3, 'rb') as photo:
            await message.answer_photo(
                photo=photo,
                caption=caption3,
                parse_mode='HTML',
                reply_markup=main_menu_keyboard
            )
    except FileNotFoundError:
        await message.answer("Bir yoki bir nechta rasm topilmadi. Fayl yo'llarini tekshiring.", reply_markup=main_menu_keyboard)
    except Exception as e:
        await message.answer(f"Rasmlarni yuborishda xatolik yuz berdi: {str(e)}", reply_markup=main_menu_keyboard)

# Bino bilan tanishish — для всех
@dp.message_handler(text="Bino bilan tanishish", chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP, types.ChatType.PRIVATE], state="*")
@dp.message_handler(commands=["about", "about@CentrisTowersbot"], chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP, types.ChatType.PRIVATE], state="*")
async def about_building(message: types.Message, state: FSMContext):
    await message.answer("Centris Towers binolari haqida ko'proq ma'lumot olish uchun quyidagi tugmani bosing:")
    # Здесь можно добавить отправку ссылки, фото или инлайн-кнопки с подробностями

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
    if project == "centris" and season_project != "centris":
        await message.answer("Этот сезон не принадлежит проекту Centris Towers.")
        return
    elif project == "golden" and season_project != "golden":
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
    if project == "golden":
        await message.answer("Sezonni tanlang:", reply_markup=get_season_keyboard(project="golden"))
    else:
        await message.answer("Sezonni tanlang:", reply_markup=get_season_keyboard())
    await message.answer("Qaysi sezonni ko'rmoqchisiz?")
    await state.set_state(VideoStates.season_select.state)

@dp.message_handler(text="Orqaga qaytish", state=VideoStates.season_select)
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await message.answer("Bosh menyu:", reply_markup=get_main_menu_keyboard())
    await state.finish()

@dp.message_handler(Command("centris_towers"))
async def centris_towers_command(message: types.Message, state: FSMContext):
    await centris_towers_menu(message, state)

@dp.message_handler(Command("golden_lake"))
async def golden_lake_command(message: types.Message, state: FSMContext):
    await golden_lake_menu(message, state)

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
                db.mark_group_video_as_viewed(message.chat.id, video_position)
        else:
            await message.answer("Video topilmadi.")
    except Exception as exx:
        from datetime import datetime
        now = datetime.now()
        formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
        print('video selector', f"{formatted_date_time}", f"error {exx}")