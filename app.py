import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import CommandStart
from datetime import datetime, timedelta
import os
from environs import Env
import gspread
from google.oauth2.service_account import Credentials
import platform
import sqlite3
import psycopg2
from psycopg2 import sql, IntegrityError
import re
import json

# Загрузка переменных окружения
env = Env()
env.read_env()
API_TOKEN = env.str('BOT_TOKEN')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())

# Состояния
class Form(StatesGroup):
    date_selection = State()  # Выбор даты (вчера/сегодня)
    type = State()  # Кирим/Чиқим
    object_name = State()  # Объект номи
    expense_type = State()  # Харажат тури
    currency_type = State()  # Сом или Доллар
    payment_type = State()  # Тулов тури
    amount = State()  # Сумма
    exchange_rate = State()  # Курс доллара (если выбрана валюта)
    comment = State()  # Изох

# Кнопки выбора даты
date_selection_kb = InlineKeyboardMarkup(row_width=2)
date_selection_kb.add(
    InlineKeyboardButton('📅 Bugun', callback_data='date_today'),
    InlineKeyboardButton('📅 Kecha', callback_data='date_yesterday')
)

# Кнопки выбора Кирим/Чиқим
type_selection_kb = InlineKeyboardMarkup(row_width=2)
type_selection_kb.add(
    InlineKeyboardButton('🟢 Кирим', callback_data='type_kirim'),
    InlineKeyboardButton('🔴 Чиқим', callback_data='type_chiqim')
)

# Объекты номи
object_names = [
    "Сам Сити",
    "Ситй+Сиёб Б Й К блок",
    "Ал Бухорий",
    "Ал-Бухорий Хотел",
    "Рубловка",
    "Қува ҚВП",
    "Макон Малл",
    "Карши Малл",
    "Карши Хотел",
    "Воха Гавхари",
    "Зарметан усто Ғафур",
    "Кожа завод",
    "Мотрид катеж",
    "Хишрав",
    "Махдуми Азам",
    "Сирдарё 1/10 Зухри",
    "Эшонгузар",
    "Рубловка(Хожи бобо дом)",
    "Ургут",
    "Қўқон малл"
]

# Типы расходов
expense_types = [
    "Мижозлардан",
    "Дорожные расходы",
    "Питания",
    "Курилиш материаллар",
    "Хоз товары и инвентарь",
    "Ремонт техники и запчасти",
    "Коммунал и интернет",
    "Прочие расходы",
    "Хизмат (Прочие расходы)",
    "Йоқилғи",
    "Ойлик",
    "Обём",
    "Олиб чикиб кетилган мусор",
    "Аренда техника",
    "Перечесления Расход",
    "Перечесления Приход",
    "Эхсон",
    "Карз олинди",
    "Карз кайтарилди",
    "Перевод",
    "Доллар олинди",
    "Доллар Сотилди",
    "Премия",
    "Расход техника",
    "хозтавар",
    "Кунлик ишчи",
    "Конставар",
    "Хомийлик"
]

# Типы валют
currency_types = [
    ("Сом", "currency_som"),
    ("Доллар", "currency_dollar")
]

# Типы оплаты
payment_types = [
    ("Нахт", "payment_nah"),
    ("Пластик", "payment_plastik"),
    ("Банк", "payment_bank")
]

# Категории (старые - оставляем для совместимости)
categories = [
    ("🟥 Doimiy Xarajat", "cat_doimiy"),
    ("🟩 Oʻzgaruvchan Xarajat", "cat_ozgaruvchan"),
    ("🟪 Qarz", "cat_qarz"),
    ("⚪ Avtoprom", "cat_avtoprom"),
    ("🟩 Divident", "cat_divident"),
    ("🟪 Soliq", "cat_soliq"),
    ("🟦 Ish Xaqi", "cat_ishhaqi")
]

# Словарь соответствий: категория -> эмодзи
category_emojis = {
    "Qurilish materiallari": "🟩",
    "Doimiy Xarajat": "🟥",
    "Qarz": "🟪",
    "Divident": "🟩",
    "Soliq": "🟪",
    "Ish Xaqi": "🟦",
    # Добавьте другие категории и эмодзи по мере необходимости
}

def get_category_with_emoji(category_name):
    emoji = category_emojis.get(category_name, "")
    return f"{emoji} {category_name}".strip()

def get_object_names_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    for name in get_object_names():
        cb = f"object_{name}"
        kb.add(InlineKeyboardButton(name, callback_data=cb))
    return kb

def get_expense_types_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    for name in get_expense_types():
        cb = f"expense_{name}"
        kb.add(InlineKeyboardButton(name, callback_data=cb))
    return kb

def get_currency_types_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    for name, cb in currency_types:
        kb.add(InlineKeyboardButton(name, callback_data=cb))
    return kb

def get_payment_types_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    for name, cb in payment_types:
        kb.add(InlineKeyboardButton(name, callback_data=cb))
    return kb

def get_categories_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    for name in get_categories():
        cb = f"cat_{name}"
        # Показываем эмодзи в меню
        btn_text = get_category_with_emoji(name)
        kb.add(InlineKeyboardButton(btn_text, callback_data=cb))
    return kb

# Тип оплаты
pay_types = [
    ("Plastik", "pay_plastik"),
    ("Naxt", "pay_naxt"),
    ("Perevod", "pay_perevod"),
    ("Bank", "pay_bank")
]

def get_pay_types_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    for name in get_pay_types():
        cb = f"pay_{name}"
        kb.add(InlineKeyboardButton(name, callback_data=cb))
    return kb

# Кнопка пропуска для Izoh
skip_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Пропустить", callback_data="skip_comment"))

# Кнопки подтверждения
confirm_kb = InlineKeyboardMarkup(row_width=2)
confirm_kb.add(
    InlineKeyboardButton('✅ Ha', callback_data='confirm_yes'),
    InlineKeyboardButton('❌ Yoq', callback_data='confirm_no')
)

# --- Google Sheets settings ---
SHEET_ID = '1D-9i4Y2R_txHL90LI0Kohx7H1HjvZ8vNJlLi7r4n6Oo'
SHEET_NAME = 'КиримЧиким'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_FILE = 'credentials.json'

# Добавляем функцию для получения списка листов
def get_sheet_names():
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SHEET_ID)
        return [ws.title for ws in sh.worksheets()]
    except Exception as e:
        print(f"Ошибка при получении списка листов: {e}")
        return []

def get_e1_g1_values():
    """Возвращает числовые значения из ячеек E1 и G1 (результат формул, не сами формулы)."""
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SHEET_ID)
        worksheet = sh.worksheet(SHEET_NAME)

        # Читаем как неконвертированные значения (без формул)
        e1 = worksheet.get('E1', value_render_option='UNFORMATTED_VALUE')
        g1 = worksheet.get('G1', value_render_option='UNFORMATTED_VALUE')

        def extract_single(val):
            try:
                return val[0][0] if val and len(val) > 0 and len(val[0]) > 0 else ''
            except Exception:
                return ''

        e1_value = extract_single(e1)
        g1_value = extract_single(g1)
        return e1_value, g1_value
    except Exception as e:
        logging.error(f"E1/G1 ni o'qishda xatolik: {e}")
        return '', ''

def clean_emoji(text):
    # Удаляет только эмодзи/спецсимволы в начале строки, остальной текст не трогает
    return re.sub(r'^[^\w\s]+', '', text).strip()

async def safe_answer_callback(call, **kwargs):
    """Безопасно отвечает на callback query с обработкой ошибок"""
    # Проверяем, не был ли уже обработан этот callback
    if is_callback_processed(call.id):
        logging.info(f"Callback {call.id} уже был обработан, пропускаем")
        return
    
    # Отмечаем callback как обработанный
    mark_callback_processed(call.id)
    
    try:
        await call.answer(**kwargs)
    except Exception as e:
        error_str = str(e)
        if any(phrase in error_str for phrase in [
            "Query is too old", 
            "InvalidQueryID", 
            "query id is invalid",
            "response timeout expired"
        ]):
            logging.warning(f"Callback query истек или недействителен: {e}")
        else:
            logging.warning(f"Не удалось ответить на callback query: {e}")
        # Игнорируем ошибку, так как callback уже устарел или недействителен

async def safe_edit_text(message, text, **kwargs):
    """Безопасно редактирует сообщение с обработкой MessageNotModified"""
    try:
        await message.edit_text(text, **kwargs)
    except Exception as e:
        error_str = str(e)
        if "Message is not modified" in error_str:
            logging.info(f"Сообщение не изменилось, пропускаем редактирование: {text[:50]}...")
            return
        elif any(phrase in error_str for phrase in [
            "message to edit not found",
            "message can't be edited",
            "Query is too old"
        ]):
            # Если сообщение нельзя отредактировать, отправляем новое
            logging.warning(f"Не удалось отредактировать сообщение, отправляем новое: {e}")
            try:
                await message.answer(text, **kwargs)
            except Exception as fallback_error:
                logging.error(f"Ошибка при отправке нового сообщения: {fallback_error}")
        else:
            logging.error(f"Неожиданная ошибка при редактировании сообщения: {e}")
            raise

def add_to_google_sheet(data):
    from datetime import datetime
    global recent_entries
    
    logging.info(f"🔄 Начинаю запись в Google Sheet. Данные: {data}")
    
    # Проверяем на дублирование
    user_id = data.get('user_id', '')
    current_time = datetime.now().timestamp()
    
    # Создаем уникальный ключ для записи
    entry_key = f"{user_id}_{data.get('object_name', '')}_{data.get('type', '')}_{data.get('expense_type', '')}_{data.get('amount', '')}_{data.get('comment', '')}"
    logging.info(f"🔑 Ключ записи: {entry_key}")
    
    # Проверяем, не была ли такая запись уже сделана в последние 30 секунд
    if entry_key in recent_entries:
        last_time = recent_entries[entry_key]
        if current_time - last_time < 30:  # 30 секунд
            logging.info(f"⚠️ Дублирование предотвращено для пользователя {user_id}")
            return False  # Возвращаем False если это дублирование
    
    # Сохраняем время текущей записи
    recent_entries[entry_key] = current_time
    logging.info(f"✅ Запись добавлена в recent_entries")
    
    # Очищаем старые записи (старше 5 минут)
    current_time = datetime.now().timestamp()
    recent_entries = {k: v for k, v in recent_entries.items() if current_time - v < 300}
    
    try:
        logging.info(f"🔐 Подключаюсь к Google Sheets...")
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        logging.info(f"✅ Credentials загружены")
        
        gc = gspread.authorize(creds)
        logging.info(f"✅ Авторизация в Google Sheets выполнена")
        
        sh = gc.open_by_key(SHEET_ID)
        logging.info(f"✅ Таблица открыта: {SHEET_ID}")
        
        worksheet = sh.worksheet(SHEET_NAME)
        logging.info(f"✅ Лист открыт: {SHEET_NAME}")
        
    except Exception as e:
        logging.error(f"❌ Ошибка подключения к Google Sheets: {e}")
        return False
    
    # Используем дату из данных, если она есть, иначе текущую дату
    date_to_use = data.get('dt_for_sheet')
    logging.info(f"📅 Дата для записи: {date_to_use}")
    
    if date_to_use:
        # Если dt_for_sheet уже в нужном формате, используем как есть
        if isinstance(date_to_use, str) and '/' in date_to_use:
            date_str = date_to_use
            logging.info(f"✅ Дата уже в нужном формате: {date_str}")
        else:
            # Парсим дату и форматируем
            try:
                if isinstance(date_to_use, str):
                    # Если это строка в формате 'YYYY-MM-DD HH:MM:SS'
                    parsed_date = datetime.strptime(date_to_use, '%Y-%m-%d %H:%M:%S')
                else:
                    parsed_date = date_to_use
                
                if platform.system() == 'Windows':
                    date_str = parsed_date.strftime('%m/%d/%Y')
                else:
                    date_str = parsed_date.strftime('%-m/%-d/%Y')
                logging.info(f"✅ Дата отформатирована: {date_str}")
            except (ValueError, AttributeError) as e:
                # Если не удалось распарсить, используем текущую дату
                logging.warning(f"⚠️ Не удалось распарсить дату {date_to_use}: {e}")
                now = datetime.now()
                if platform.system() == 'Windows':
                    date_str = now.strftime('%m/%d/%Y')
                else:
                    date_str = now.strftime('%-m/%-d/%Y')
                logging.info(f"✅ Используется текущая дата: {date_str}")
    else:
        # Если dt_for_sheet нет, используем текущую дату
        logging.warning(f"⚠️ dt_for_sheet не найден, используем текущую дату")
        now = datetime.now()
        if platform.system() == 'Windows':
            date_str = now.strftime('%m/%d/%Y')
        else:
            date_str = now.strftime('%-m/%-d/%Y')
        logging.info(f"✅ Используется текущая дата: {date_str}")
    
    # Время всегда текущее
    time_str = datetime.now().strftime('%H:%M')
    logging.info(f"⏰ Время записи: {time_str}")
    
    user_name = get_user_name(data.get('user_id', data.get('user_id', '')))
    logging.info(f"👤 Имя пользователя: {user_name}")
    
    # Определяем данные для столбцов в зависимости от валюты
    currency_type = data.get('currency_type', '')
    amount = data.get('amount', '')
    exchange_rate = data.get('exchange_rate', '')
    
    if currency_type == 'Доллар':
        # Если доллар: Курс = курс, $ = сумма в долларах, Сом = пусто
        som_amount = ''
        dollar_amount = int(float(amount)) if amount else ''
        exchange_rate = int(float(exchange_rate)) if exchange_rate else ''
    else:
        # Если сом: Курс = пусто, $ = пусто, Сом = сумма в сомах
        som_amount = int(float(amount)) if amount else ''
        dollar_amount = ''
        exchange_rate = ''
    
    # Находим первую пустую строку
    all_values = worksheet.get_all_values()
    
    # Ищем первую пустую строку после заголовков
    next_row = 2  # Начинаем со строки 2 (после заголовков)
    for i, row in enumerate(all_values[1:], 2):  # Пропускаем заголовки
        if not any(cell.strip() for cell in row[:9]):  # Проверяем первые 9 столбцов
            next_row = i
            break
    else:
        # Если не нашли пустую строку, добавляем новую
        next_row = len(all_values) + 1
        # Расширяем лист если нужно
        if next_row > 45:
            worksheet.resize(next_row + 10, 25)  # Добавляем 10 строк
    
    # Записываем данные в правильные столбцы (A-J)
    logging.info(f"📝 Записываю данные в строку {next_row}")
    
    try:
        worksheet.update(f'A{next_row}', data.get('object_name', ''))      # Объект номи
        worksheet.update(f'B{next_row}', data.get('type', ''))             # Кирим/Чиким
        worksheet.update(f'C{next_row}', data.get('expense_type', ''))     # Харажат Тури
        worksheet.update(f'D{next_row}', data.get('comment', ''))          # Изох
        worksheet.update(f'E{next_row}', dollar_amount)                     # $
        worksheet.update(f'F{next_row}', exchange_rate)                     # Курс
        worksheet.update(f'G{next_row}', som_amount)                        # Сом
        worksheet.update(f'H{next_row}', date_str)                         # Сана
        worksheet.update(f'I{next_row}', user_name)                        # Масул шахс
        worksheet.update(f'K{next_row}', data.get('payment_type', ''))     # Тулов тури
        
        logging.info(f"✅ Данные успешно записаны в Google Sheet, строка {next_row}")
        return True  # Возвращаем True если запись успешна
        
    except Exception as e:
        logging.error(f"❌ Ошибка при записи данных в Google Sheet: {e}")
        return False

def format_number(number):
    """Форматирует число с разделителями тысяч для удобного чтения"""
    try:
        # Преобразуем в строку и убираем десятичные знаки если они есть
        num_str = str(int(float(number)))
        
        # Добавляем разделители каждые 3 цифры справа налево
        formatted = ""
        for i, digit in enumerate(reversed(num_str)):
            if i > 0 and i % 3 == 0:
                formatted = " " + formatted
            formatted = digit + formatted
        
        return formatted
    except (ValueError, TypeError):
        # Если не удалось преобразовать, возвращаем как есть
        return str(number)

def format_summary(data):
    tur_emoji = '🟢' if data.get('type') == 'Кирим' else '🔴'
    dt = data.get('dt', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # Формируем информацию о сумме и валюте с красивым форматированием
    currency_type = data.get('currency_type', '')
    amount = data.get('amount', '-')
    
    if currency_type == 'Доллар':
        exchange_rate = data.get('exchange_rate', '-')
        # Форматируем сумму и курс
        formatted_amount = format_number(amount)
        formatted_rate = format_number(exchange_rate)
        amount_info = f"{formatted_amount} $ (курс: {formatted_rate})"
    else:
        # Форматируем сумму в сомах
        formatted_amount = format_number(amount)
        amount_info = f"{formatted_amount} Сом"
    
    return (
        f"<b>Natija:</b>\n"
        f"<b>Tur:</b> {tur_emoji} {data.get('type', '-')}\n"
        f"<b>Объект номи:</b> {data.get('object_name', '-')}\n"
        f"<b>Харажат тури:</b> {data.get('expense_type', '-')}\n"
        f"<b>Валюта:</b> {currency_type}\n"
        f"<b>Тулов тури:</b> {data.get('payment_type', '-')}\n"
        f"<b>Сумма:</b> {amount_info}\n"
        f"<b>Изох:</b> {data.get('comment', '-')}\n"
        f"<b>Vaqt:</b> {dt}"
    )

# --- Админы ---
ADMINS = [5657091547, 5048593195]  # Здесь можно добавить id других админов через запятую

# Хранилище для отслеживания последних записей (защита от дублирования)
recent_entries = {}

# Глобальный словарь для отслеживания обработанных callback'ов
processed_callbacks = set()

def is_callback_processed(callback_id):
    """Проверяет, был ли уже обработан callback с данным ID"""
    return callback_id in processed_callbacks

def mark_callback_processed(callback_id):
    """Отмечает callback как обработанный"""
    processed_callbacks.add(callback_id)
    # Ограничиваем размер словаря для предотвращения утечек памяти
    if len(processed_callbacks) > 10000:
        # Удаляем старые записи, оставляя только последние 5000
        old_callbacks = list(processed_callbacks)[:-5000]
        for old_id in old_callbacks:
            processed_callbacks.discard(old_id)

# Хранилище для отслеживания последних отправленных сообщений о балансе (защита от дублирования)
recent_balance_messages = {}

def is_balance_message_duplicate(user_id, operation_type, amount, currency, timestamp):
    """Проверяет, не является ли сообщение о балансе дубликатом"""
    key = f"{user_id}_{operation_type}_{amount}_{currency}"
    
    # Проверяем, есть ли уже такое сообщение
    if key in recent_balance_messages:
        last_time = recent_balance_messages[key]
        # Если прошло меньше 5 секунд, считаем дубликатом
        if (timestamp - last_time).total_seconds() < 5:
            return True
    
    # Обновляем время последнего сообщения
    recent_balance_messages[key] = timestamp
    
    # Ограничиваем размер словаря
    if len(recent_balance_messages) > 1000:
        # Удаляем старые записи
        old_keys = list(recent_balance_messages.keys())[:-500]
        for old_key in old_keys:
            del recent_balance_messages[old_key]
    
    return False

# --- Инициализация БД ---
def get_db_conn():
    return psycopg2.connect(
        dbname=env.str('POSTGRES_DB', 'kapital'),
        user=env.str('POSTGRES_USER', 'postgres'),
        password=env.str('POSTGRES_PASSWORD', 'postgres'),
        host=env.str('POSTGRES_HOST', 'localhost'),
        port=env.str('POSTGRES_PORT', '5432')
    )

def init_db():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        user_id BIGINT UNIQUE,
        name TEXT,
        phone TEXT,
        status TEXT,
        reg_date TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        id SERIAL PRIMARY KEY,
        user_id BIGINT UNIQUE,
        name TEXT,
        added_by BIGINT,
        added_date TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS pay_types (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS object_names (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS expense_types (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS pending_approvals (
        id SERIAL PRIMARY KEY,
        approval_key TEXT UNIQUE,
        user_id BIGINT,
        data JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Очищаем старые данные
    c.execute('DELETE FROM object_names')
    c.execute('DELETE FROM expense_types')
    
    # Заполняем дефолтные значения, если таблицы пусты
    c.execute('SELECT COUNT(*) FROM pay_types')
    if c.fetchone()[0] == 0:
        for name in ["Plastik", "Naxt", "Perevod", "Bank"]:
            c.execute('INSERT INTO pay_types (name) VALUES (%s)', (name,))
    c.execute('SELECT COUNT(*) FROM categories')
    if c.fetchone()[0] == 0:
        for name in ["🟥 Doimiy Xarajat", "🟩 Oʻzgaruvchan Xarajat", "🟪 Qarz", "⚪ Avtoprom", "🟩 Divident", "🟪 Soliq", "🟦 Ish Xaqi"]:
            c.execute('INSERT INTO categories (name) VALUES (%s)', (name,))
    
    # Добавляем дефолтных админов
    c.execute('SELECT COUNT(*) FROM admins')
    if c.fetchone()[0] == 0:
        from datetime import datetime
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for admin_id in ADMINS:
            c.execute('INSERT INTO admins (user_id, name, added_by, added_date) VALUES (%s, %s, %s, %s) ON CONFLICT (user_id) DO NOTHING',
                      (admin_id, f'Admin {admin_id}', admin_id, current_time))
    
    # Заполняем объекты номи
    for name in object_names:
        c.execute('INSERT INTO object_names (name) VALUES (%s)', (name,))
    
    # Заполняем типы расходов
    for name in expense_types:
        c.execute('INSERT INTO expense_types (name) VALUES (%s)', (name,))
    
    conn.commit()
    conn.close()

init_db()

# --- Проверка статуса пользователя ---
def get_user_status(user_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('SELECT status FROM users WHERE user_id=%s', (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# --- Проверка является ли пользователь админом ---
def is_admin(user_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('SELECT user_id FROM admins WHERE user_id=%s', (user_id,))
    row = c.fetchone()
    conn.close()
    return row is not None

# --- Добавление нового админа ---
def add_admin(user_id, name, added_by):
    from datetime import datetime
    conn = get_db_conn()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO admins (user_id, name, added_by, added_date) VALUES (%s, %s, %s, %s) ON CONFLICT (user_id) DO NOTHING',
                  (user_id, name, added_by, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        return True
    except IntegrityError:
        conn.rollback()
        return False
    finally:
        conn.close()

# --- Удаление админа ---
def remove_admin(user_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('DELETE FROM admins WHERE user_id=%s', (user_id,))
    result = c.rowcount > 0
    conn.commit()
    conn.close()
    return result

# --- Получение списка всех админов ---
def get_all_admins():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('SELECT user_id, name, added_date FROM admins ORDER BY added_date')
    admins = c.fetchall()
    conn.close()
    return admins

# --- Регистрация пользователя ---
def register_user(user_id, name, phone):
    from datetime import datetime
    conn = get_db_conn()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (user_id, name, phone, status, reg_date) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (user_id) DO NOTHING',
                  (user_id, name, phone, 'pending', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
    except IntegrityError:
        conn.rollback()
    conn.close()

# --- Обновление статуса пользователя ---
def update_user_status(user_id, status):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('UPDATE users SET status=%s WHERE user_id=%s', (status, user_id))
    conn.commit()
    conn.close()

# --- Получение имени пользователя для Google Sheets ---
def get_user_name(user_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('SELECT name FROM users WHERE user_id=%s', (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else ''

# --- Получение актуальных списков ---
def get_pay_types():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('SELECT name FROM pay_types')
    result = [row[0] for row in c.fetchall()]
    conn.close()
    return result

def get_categories():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('SELECT name FROM categories ORDER BY name')
    result = [row[0] for row in c.fetchall()]
    conn.close()
    return result

def get_object_names():
    # Используем порядок из списка object_names
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('SELECT name FROM object_names')
    db_names = [row[0] for row in c.fetchall()]
    conn.close()
    
    # Сортируем по порядку в списке object_names
    result = []
    for name in object_names:
        if name in db_names:
            result.append(name)
    
    # Добавляем те, которых нет в списке (если есть)
    for name in db_names:
        if name not in result:
            result.append(name)
    
    return result

def get_expense_types():
    # Используем порядок из списка expense_types
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('SELECT name FROM expense_types')
    db_names = [row[0] for row in c.fetchall()]
    conn.close()
    
    # Сортируем по порядку в списке expense_types
    result = []
    for name in expense_types:
        if name in db_names:
            result.append(name)
    
    # Добавляем те, которых нет в списке (если есть)
    for name in db_names:
        if name not in result:
            result.append(name)
    
    return result

# --- Старт с регистрацией ---
@dp.message_handler(commands=['start'])
async def start(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    status = get_user_status(user_id)
    if status == 'approved':
        await state.finish()
        # Показываем меню выбора даты
        await show_main_menu(msg, state)
        logging.info(f"Главное меню показано пользователю {user_id}")
    elif status == 'pending':
        await msg.answer('⏳ Sizning arizangiz ko\'rib chiqilmoqda. Iltimos, kuting.')
    elif status == 'denied':
        await msg.answer('❌ Sizga botdan foydalanishga ruxsat berilmagan.')
    else:
        await msg.answer('Ismingizni kiriting:')
        await state.set_state('register_name')

# --- FSM для регистрации ---
class Register(StatesGroup):
    name = State()
    phone = State()

@dp.message_handler(state='register_name', content_types=types.ContentTypes.TEXT)
async def process_register_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text.strip())
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
    await msg.answer('Telefon raqamingizni yuboring:', reply_markup=kb)
    await state.set_state('register_phone')

@dp.message_handler(state='register_phone', content_types=types.ContentTypes.CONTACT)
async def process_register_phone(msg: types.Message, state: FSMContext):
    phone = msg.contact.phone_number
    data = await state.get_data()
    user_id = msg.from_user.id
    name = data.get('name', '')
    register_user(user_id, name, phone)
    await msg.answer('⏳ Arizangiz adminga yuborildi. Iltimos, kuting.', reply_markup=types.ReplyKeyboardRemove())
    # Уведомление админа
    admins = get_all_admins()
    for admin_id, admin_name, added_date in admins:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton('✅ Ha', callback_data=f'approve_{user_id}'),
            InlineKeyboardButton('❌ Yoq', callback_data=f'deny_{user_id}')
        )
        await bot.send_message(admin_id, f'🆕 Yangi foydalanuvchi ro\'yxatdan o\'tdi:\nID: <code>{user_id}</code>\nIsmi: <b>{name}</b>\nTelefon: <code>{phone}</code>', reply_markup=kb)
    await state.finish()

# --- Обработка одобрения/запрета админом ---
@dp.callback_query_handler(lambda c: (c.data.startswith('approve_') or c.data.startswith('deny_')) and not c.data.startswith('approve_large_') and not c.data.startswith('reject_large_'), state='*')
async def process_admin_approve(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await safe_answer_callback(call, text='Faqat admin uchun!', show_alert=True)
        return
    action, user_id = call.data.split('_')
    user_id = int(user_id)
    if action == 'approve':
        update_user_status(user_id, 'approved')
        await bot.send_message(user_id, '✅ Sizga botdan foydalanishga ruxsat berildi! /start')
        await safe_edit_text(call.message, '✅ Foydalanuvchi tasdiqlandi.')
    else:
        update_user_status(user_id, 'denied')
        await bot.send_message(user_id, '❌ Sizga botdan foydalanishga ruxsat berilmagan.')
        await safe_edit_text(call.message, '❌ Foydalanuvchi rad etildi.')
    await safe_answer_callback(call)

# --- Ограничение доступа для всех остальных хендлеров ---
@dp.message_handler(lambda msg: get_user_status(msg.from_user.id) != 'approved', state='*')
async def block_unapproved(msg: types.Message, state: FSMContext):
    await msg.answer('⏳ Sizning arizangiz ko\'rib chiqilmoqda yoki sizga ruxsat berilmagan.')
    await state.finish()

async def show_main_menu(bot_or_msg_or_call, state_or_user_id):
    """Показывает главное меню выбора даты"""
    text = "<b>Qaysi kun uchun operatsiya?</b>"
    
    # Определяем, что передано: bot + user_id или msg/call + state
    # Проверяем, является ли первый аргумент Bot объектом (у Bot есть метод send_message, но нет from_user)
    if hasattr(bot_or_msg_or_call, 'send_message') and not hasattr(bot_or_msg_or_call, 'from_user') and isinstance(state_or_user_id, int):
        # Передан bot и user_id - отправляем новое сообщение
        await bot_or_msg_or_call.send_message(state_or_user_id, text, reply_markup=date_selection_kb)
        user_id = state_or_user_id
        logging.info(f"Меню выбора даты отправлено пользователю {user_id} через bot.send_message")
    else:
        # Передан msg/call и state - используем стандартный способ
        msg_or_call = bot_or_msg_or_call
        state = state_or_user_id
        
        # Проверяем тип объекта и отправляем сообщение соответственно
        if hasattr(msg_or_call, 'message'):
            # Это CallbackQuery, используем call.message
            await msg_or_call.message.answer(text, reply_markup=date_selection_kb)
        else:
            # Это Message, используем msg
            await msg_or_call.answer(text, reply_markup=date_selection_kb)
        
        await Form.date_selection.set()
        
        user_id = msg_or_call.from_user.id if hasattr(msg_or_call, 'from_user') else msg_or_call.chat.id
        logging.info(f"Меню выбора даты показано пользователю {user_id}")

# Удаляем дублирующуюся функцию start - оставляем только первую

@dp.message_handler(commands=['reboot'], state='*')
async def reboot_cmd(msg: types.Message, state: FSMContext):
    """Команда для перезапуска бота и сброса FSM состояния"""
    logging.info(f"Команда /reboot вызвана пользователем {msg.from_user.id}")
    
    # Сбрасываем FSM состояние
    await state.finish()
    
    # Отправляем сообщение о перезапуске
    await msg.answer("🔄 Bot qayta ishga tushirildi! FSM holati tozalandi.")
    
    # Показываем главное меню
    await show_main_menu(msg, state)
    
    logging.info(f"Пользователь {msg.from_user.id} возвращен к начальному состоянию FSM")

# Выбор даты
@dp.callback_query_handler(lambda c: c.data.startswith('date_'), state=Form.date_selection)
async def process_date_selection(call: types.CallbackQuery, state: FSMContext):
    # Сразу отвечаем на callback чтобы кнопка не "зависла"
    await safe_answer_callback(call)
    
    logging.info(f"process_date_selection вызван для пользователя {call.from_user.id} с данными: {call.data}")
    
    # Определяем выбранную дату
    if call.data == 'date_today':
        selected_date = datetime.now()
        date_text = "Bugun"
    else:  # date_yesterday
        selected_date = datetime.now() - timedelta(days=1)
        date_text = "Kecha"
    
    # Сохраняем выбранную дату в состоянии
    await state.update_data(selected_date=selected_date, date_text=date_text)
    
    logging.info(f"Пользователь {call.from_user.id} выбрал дату: {date_text} ({selected_date.strftime('%Y-%m-%d')})")
    
    # Показываем меню выбора типа операции
    await safe_edit_text(call.message, "<b>Qaysi turdagi operatsiya?</b>", reply_markup=type_selection_kb)
    await Form.type.set()

# Кирим/Чиқим выбор
@dp.callback_query_handler(lambda c: c.data.startswith('type_'), state=Form.type)
async def process_type(call: types.CallbackQuery, state: FSMContext):
    # Сразу отвечаем на callback чтобы кнопка не "зависла"
    await safe_answer_callback(call)
    
    t = 'Кирим' if call.data == 'type_kirim' else 'Чиқим'
    await state.update_data(type=t)
    await safe_edit_text(call.message, "<b>Объект номини tanlang:</b>", reply_markup=get_object_names_kb())
    await Form.object_name.set()

# Объект номи выбор
@dp.callback_query_handler(lambda c: c.data.startswith('object_'), state=Form.object_name)
async def process_object_name(call: types.CallbackQuery, state: FSMContext):
    # Сразу отвечаем на callback чтобы кнопка не "зависла"
    await safe_answer_callback(call)
    
    object_name = call.data[7:]  # Убираем 'object_' префикс
    await state.update_data(object_name=object_name)
    await safe_edit_text(call.message, "<b>Харажат турини tanlang:</b>", reply_markup=get_expense_types_kb())
    await Form.expense_type.set()

# Харажат тури выбор
@dp.callback_query_handler(lambda c: c.data.startswith('expense_'), state=Form.expense_type)
async def process_expense_type(call: types.CallbackQuery, state: FSMContext):
    # Сразу отвечаем на callback чтобы кнопка не "зависла"
    await safe_answer_callback(call)
    
    expense_type = call.data[8:]  # Убираем 'expense_' префикс
    await state.update_data(expense_type=expense_type)
    await safe_edit_text(call.message, "<b>Qanday to'lov turi? Сом yoki $?</b>", reply_markup=get_currency_types_kb())
    await Form.currency_type.set()

# Выбор валюты
@dp.callback_query_handler(lambda c: c.data.startswith('currency_'), state=Form.currency_type)
async def process_currency_type(call: types.CallbackQuery, state: FSMContext):
    # Сразу отвечаем на callback чтобы кнопка не "зависла"
    await safe_answer_callback(call)
    
    currency = 'Сом' if call.data == 'currency_som' else 'Доллар'
    await state.update_data(currency_type=currency)
    await safe_edit_text(call.message, "<b>Summani kiriting:</b>")
    await Form.amount.set()

# Выбор типа оплаты
@dp.callback_query_handler(lambda c: c.data.startswith('payment_'), state=Form.payment_type)
async def process_payment_type(call: types.CallbackQuery, state: FSMContext):
    # Сразу отвечаем на callback чтобы кнопка не "зависла"
    await safe_answer_callback(call)
    
    payment_map = {
        'payment_nah': 'Нахт',
        'payment_plastik': 'Пластик',
        'payment_bank': 'Банк'
    }
    payment = payment_map.get(call.data, 'Нахт')
    await state.update_data(payment_type=payment)
    
    # Проверяем, выбран ли "Мижозлардан"
    data = await state.get_data()
    expense_type = data.get('expense_type', '')
    
    if expense_type == 'Мижозлардан':
        await safe_edit_text(call.message, "<b>Договор раками kiriting (yoki пропустите):</b>", reply_markup=skip_kb)
    else:
        await safe_edit_text(call.message, "<b>Изох kiriting (yoki пропустите):</b>", reply_markup=skip_kb)
    
    await Form.comment.set()

# Сумма
@dp.message_handler(lambda m: m.text.replace('.', '', 1).isdigit(), state=Form.amount)
async def process_amount(msg: types.Message, state: FSMContext):
    await state.update_data(amount=msg.text)
    data = await state.get_data()
    
    # Если выбрана валюта Доллар, спрашиваем курс
    if data.get('currency_type') == 'Доллар':
        await msg.answer("<b>Курс долларани kiriting:</b>")
        await Form.exchange_rate.set()
    else:
        # Если Сом, переходим к типу оплаты
        await msg.answer("<b>Тулов турини tanlang:</b>", reply_markup=get_payment_types_kb())
        await Form.payment_type.set()

# Курс доллара
@dp.message_handler(lambda m: m.text.replace('.', '', 1).isdigit(), state=Form.exchange_rate)
async def process_exchange_rate(msg: types.Message, state: FSMContext):
    await state.update_data(exchange_rate=msg.text)
    await msg.answer("<b>Тулов турини tanlang:</b>", reply_markup=get_payment_types_kb())
    await Form.payment_type.set()

# Кнопка пропуска комментария
@dp.callback_query_handler(lambda c: c.data == 'skip_comment', state=Form.comment)
async def skip_comment_btn(call: types.CallbackQuery, state: FSMContext):
    # Сразу отвечаем на callback чтобы кнопка не "зависла"
    await safe_answer_callback(call)
    
    logging.info(f"skip_comment_btn вызван для пользователя {call.from_user.id}")
    
    await state.update_data(comment='-')
    data = await state.get_data()
    # Set and save the final timestamp
    data['dt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    await state.update_data(dt=data['dt'])
    
    text = format_summary(data)
    
    await call.message.answer(text, reply_markup=confirm_kb)
    await state.set_state('confirm')

# Комментарий (или пропуск)
@dp.message_handler(state=Form.comment, content_types=types.ContentTypes.TEXT)
async def process_comment(msg: types.Message, state: FSMContext):
    logging.info(f"process_comment вызван для пользователя {msg.from_user.id}")
    
    await state.update_data(comment=msg.text)
    data = await state.get_data()
    # Set and save the final timestamp
    data['dt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    await state.update_data(dt=data['dt'])
    
    text = format_summary(data)

    await msg.answer(text, reply_markup=confirm_kb)
    await state.set_state('confirm')

# Обработка кнопок Да/Нет
@dp.callback_query_handler(lambda c: c.data in ['confirm_yes', 'confirm_no'], state='confirm')
async def process_confirm(call: types.CallbackQuery, state: FSMContext):
    # Сразу отвечаем на callback чтобы кнопка не "зависла"
    await safe_answer_callback(call)
    
    logging.info(f"process_confirm вызван для пользователя {call.from_user.id} с данными: {call.data}")
    
    # Проверяем, не был ли уже обработан этот callback
    current_state = await state.get_state()
    if current_state != 'confirm':
        logging.warning(f"Попытка обработать подтверждение в неправильном состоянии: {current_state}")
        await safe_answer_callback(call, text='Operatsiya allaqachon bajarilgan!', show_alert=True)
        return
    
    if call.data == 'confirm_yes':
        data = await state.get_data()
        from datetime import datetime
        
        # Используем выбранную дату, а не текущую
        selected_date = data.get('selected_date')
        if selected_date:
            # Если selected_date - это строка, парсим её
            if isinstance(selected_date, str):
                try:
                    selected_date = datetime.strptime(selected_date, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # Если не удалось распарсить, используем текущую дату
                    selected_date = datetime.now()
            # Если selected_date - это datetime объект, используем как есть
            elif isinstance(selected_date, datetime):
                pass
            else:
                selected_date = datetime.now()
        else:
            # Если selected_date не найден, используем текущую дату
            selected_date = datetime.now()
        
        dt = selected_date  # Используем выбранную дату
        import platform
        if platform.system() == 'Windows':
            date_str = dt.strftime('%m/%d/%Y')
        else:
            date_str = dt.strftime('%-m/%-d/%Y')
        time_str = dt.strftime('%H:%M')
        data['dt_for_sheet'] = date_str
        data['vaqt'] = time_str
        # Гарантируем, что user_id всегда есть
        data['user_id'] = call.from_user.id
        
        # Проверяем сумму для одобрения админом (только для Chiqim)
        operation_type = data.get('type', '')
        currency_type = data.get('currency_type', '')
        amount = data.get('amount', '0')
        exchange_rate = data.get('exchange_rate', '0')
        
        try:
            amount_value = float(amount)
            exchange_rate_value = float(exchange_rate) if exchange_rate != '0' else 1
            
            # Рассчитываем общую сумму в сомах
            if currency_type == 'Доллар':
                total_som_amount = amount_value * exchange_rate_value
            else:
                total_som_amount = amount_value
            
            # Проверяем, нужна ли одобрение (только для Chiqim и если сумма >= 10,000,000 сом)
            needs_approval = (operation_type == 'Чиқим' and total_som_amount >= 10000000)
            
            if needs_approval:
                # Генерируем уникальный timestamp для всей операции
                approval_timestamp = int(dt.timestamp())
                
                # Отправляем на одобрение админу
                user_name = get_user_name(call.from_user.id) or call.from_user.full_name
                summary_text = format_summary(data)
                admin_approval_text = f"⚠️ <b>Tasdiqlash talab qilinadi!</b>\n\nFoydalanuvchi <b>{user_name}</b> tomonidan kiritilgan katta summa:\n\n{summary_text}"
                
                # Создаем кнопки для админа с одинаковым timestamp
                admin_kb = InlineKeyboardMarkup(row_width=2)
                admin_kb.add(
                    InlineKeyboardButton('✅ Tasdiqlash', callback_data=f'approve_large_{call.from_user.id}_{approval_timestamp}'),
                    InlineKeyboardButton('❌ Rad etish', callback_data=f'reject_large_{call.from_user.id}_{approval_timestamp}')
                )
                
                # Сохраняем данные для последующего использования в базе данных
                approval_key = f"{call.from_user.id}_{approval_timestamp}"
                data['pending_approval'] = True
                data['approval_timestamp'] = approval_timestamp
                
                # Сохраняем в базе данных
                logging.info(f"Пытаемся сохранить данные в БД. Ключ: {approval_key}, данные: {data}")
                if save_pending_approval(approval_key, call.from_user.id, data):
                    logging.info(f"✅ Данные успешно сохранены в базе данных для одобрения. Ключ: {approval_key}")
                    logging.info(f"Сохраненные данные: {data}")
                else:
                    logging.error(f"❌ Ошибка сохранения данных в базе данных для ключа: {approval_key}")
                    # Продолжаем отправку админам, даже если сохранение не удалось
                
                # Отправляем всем админам
                sent_to_admin = False
                admins = get_all_admins()
                logging.info(f"Найдено админов в базе: {len(admins)}")
                for admin_id, admin_name, added_date in admins:
                    logging.info(f"Пытаемся отправить уведомление админу {admin_id} ({admin_name})")
                    try:
                        await bot.send_message(admin_id, admin_approval_text, reply_markup=admin_kb)
                        sent_to_admin = True
                        logging.info(f"✅ Уведомление успешно отправлено админу {admin_id}")
                    except Exception as e:
                        error_msg = str(e)
                        if "Chat not found" in error_msg:
                            logging.error(f"❌ Админ {admin_id} ({admin_name}) не найден в чате. Возможно, не запустил бота или заблокировал его.")
                        elif "Forbidden" in error_msg:
                            logging.error(f"❌ Админ {admin_id} ({admin_name}) заблокировал бота.")
                        else:
                            logging.error(f"❌ Ошибка отправки админу {admin_id}: {error_msg}")
                
                if sent_to_admin:
                    await call.message.answer('⏳ Arizangiz administratorga yuborildi. Tasdiqlashni kuting.')
                    
                    # Показываем главное меню и возвращаем в начальное состояние
                    await state.finish()
                    await show_main_menu(call.message, state)
                else:
                    await call.message.answer('⚠️ Xatolik: tasdiqlashga yuborish amalga oshmadi. Iltimos, administrator bilan bog\'laning.')
                    
                    # Показываем главное меню и возвращаем в начальное состояние
                    await state.finish()
                    await show_main_menu(call.message, state)
            else:
                # Обычная отправка в Google Sheet
                success = add_to_google_sheet(data)
                if success:
                    await call.message.answer('✅ Ma\'lumotlar Google Sheets-ga muvaffaqiyatli yuborildi!')
                                    # Jo'natilgandan so'ng, valyutaga qarab E1 yoki G1 natijaviy qiymatini yuboramiz
                try:
                    e1_value, g1_value = get_e1_g1_values()
                    
                    # Проверяем дублирование сообщения о балансе
                    from datetime import datetime
                    current_time = datetime.now()
                    is_duplicate = is_balance_message_duplicate(
                        call.from_user.id, 
                        data.get('type', ''), 
                        data.get('amount', ''), 
                        data.get('currency_type', ''), 
                        current_time
                    )
                    
                    if not is_duplicate:
                        # Отправляем баланс в зависимости от валюты операции
                        if data.get('currency_type') == 'Доллар':
                            logging.info(f"Отправляем баланс в долларах пользователю {call.from_user.id}: {e1_value}")
                            await call.message.answer(f"💰 Balans: dollarda {e1_value}")
                        else:  # Сом
                            logging.info(f"Отправляем баланс в сомах пользователю {call.from_user.id}: {g1_value}")
                            await call.message.answer(f"💰 Balans: somda {g1_value}")
                    else:
                        logging.info(f"Сообщение о балансе для пользователя {call.from_user.id} пропущено как дубликат")
                        
                except Exception as e:
                    logging.error(f"E1/G1 qiymatlarini yuborishda xatolik: {e}")

                # Уведомление для админов
                user_name = get_user_name(call.from_user.id) or call.from_user.full_name
                summary_text = format_summary(data)
                admin_notification_text = f"Foydalanuvchi <b>{user_name}</b> tomonidan kiritilgan yangi ma'lumot:\n\n{summary_text}"
                
                # Добавляем информацию о балансе для админов (всегда показываем обе валюты)
                try:
                    e1_value, g1_value = get_e1_g1_values()
                    balance_info = f"\n\n💰 <b>Balans:</b>\n"
                    balance_info += f"💵 Dollarda: {format_number(e1_value)}\n"
                    balance_info += f"💸 Somda: {format_number(g1_value)}"
                    admin_notification_text += balance_info
                    logging.info(f"Информация о балансе добавлена в уведомление для админов: E1={e1_value}, G1={g1_value}")
                except Exception as e:
                    logging.error(f"Balans ma'lumotlarini qo'shishda xatolik: {e}")
                
                admins = get_all_admins()
                logging.info(f"Отправляем уведомления {len(admins)} админам")
                for admin_id, admin_name, added_date in admins:
                    try:
                        await bot.send_message(admin_id, admin_notification_text)
                        logging.info(f"✅ Уведомление отправлено админу {admin_id} ({admin_name})")
                    except Exception as e:
                        error_msg = str(e)
                        if "Chat not found" in error_msg:
                            logging.error(f"❌ Админ {admin_id} ({admin_name}) не найден в чате")
                        elif "Forbidden" in error_msg:
                            logging.error(f"❌ Админ {admin_id} ({admin_name}) заблокировал бота")
                        else:
                            logging.error(f"❌ Ошибка отправки админу {admin_id}: {error_msg}")
                
                # Показываем главное меню и возвращаем в начальное состояние
                await state.finish()
                await show_main_menu(call.message, state)

        except Exception as e:
            await call.message.answer(f'⚠️ Google Sheets-ga yuborishda xatolik: {e}')
            await state.finish()
    else:
        await call.message.answer('❌ Operatsiya bekor qilindi.')
        await state.finish()
    
    # Теперь главное меню показывается в нужных местах

# Обработка одобрения больших сумм
@dp.callback_query_handler(lambda c: c.data.startswith('approve_large_'), state='*')
async def approve_large_amount(call: types.CallbackQuery, state: FSMContext):
    logging.info(f"Одобрение больших сумм вызвано: {call.data}")
    
    # Сразу отвечаем на callback чтобы кнопка не "зависла"
    await safe_answer_callback(call)
    
    # Проверяем дедупликацию - если callback уже был обработан, выходим
    if is_callback_processed(f"approve_{call.data}"):
        logging.info(f"Callback {call.data} уже был обработан для одобрения")
        return
    mark_callback_processed(f"approve_{call.data}")
    
    if not is_admin(call.from_user.id):
        try:
            await call.answer('Faqat admin uchun!', show_alert=True)
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения о правах: {e}")
        return
    
    # Парсим данные из callback
    try:
        parts = call.data.split('_')
        if len(parts) < 4:
            logging.error(f"Неверный формат callback данных: {call.data}")
            await call.answer('Xatolik: noto\'g\'ri ma\'lumotlar', show_alert=True)
            return
            
        user_id = int(parts[2])
        timestamp = int(parts[3])
        approval_key = f"{user_id}_{timestamp}"
        
        logging.info(f"Approval key: {approval_key}, user_id: {user_id}, timestamp: {timestamp}")
    except (ValueError, IndexError) as e:
        logging.error(f"Ошибка парсинга callback данных: {e}, data: {call.data}")
        await call.answer('Xatolik: noto\'g\'ri ma\'lumotlar', show_alert=True)
        return
    
    # Проверяем, не был ли уже обработан этот ключ одобрения
    if not check_approval_status(approval_key):
        logging.warning(f"Ключ одобрения {approval_key} уже был обработан или не существует")
        try:
            await call.answer('Bu ariza allaqachon ko\'rib chiqilgan yoki mavjud emas!', show_alert=True)
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения о статусе: {e}")
        return
    
    try:
        # Получаем сохраненные данные из базы данных
        saved_data = get_pending_approval(approval_key)
        if saved_data:
            logging.info(f"Найдены данные для одобрения: {saved_data}")
            
            # Отправляем в Google Sheet
            success = add_to_google_sheet(saved_data)
            if success:
                logging.info("Данные отправлены в Google Sheet")
                # Jo'natilgandan so'ng, valyutaga qarab E1 yoki G1 natijaviy qiymatini yuboramiz
                try:
                    e1_value, g1_value = get_e1_g1_values()
                    
                    # Проверяем дублирование сообщения о балансе
                    current_time = datetime.now()
                    is_duplicate = is_balance_message_duplicate(
                        user_id, 
                        saved_data.get('type', ''), 
                        saved_data.get('amount', ''), 
                        saved_data.get('currency_type', ''), 
                        current_time
                    )
                    
                    if not is_duplicate:
                        # Отправляем баланс в обеих валютах с форматированием
                        balance_message = f"💰 <b>Balans:</b>\n"
                        balance_message += f"💵 Dollarda: {format_number(e1_value)}\n"
                        balance_message += f"💸 Somda: {format_number(g1_value)}"
                        
                        logging.info(f"Отправляем баланс пользователю {user_id}: E1={e1_value}, G1={g1_value}")
                        await bot.send_message(user_id, balance_message)
                    else:
                        logging.info(f"Сообщение о балансе для пользователя {user_id} пропущено как дубликат")
                        
                except Exception as e_val:
                    logging.error(f"E1/G1 qiymatlarini yuborishda xatolik: {e_val}")
            else:
                logging.info("Дублирование предотвращено при одобрении")
            
            # Отправляем сообщение пользователю
            await bot.send_message(user_id, '✅ Arizangiz tasdiqlandi! Ma\'lumotlar Google Sheet-ga yozildi.')
            
            # Удаляем из базы данных
            delete_pending_approval(approval_key)
            
            # Останавливаем FSM для пользователя, который отправил заявку
            try:
                # Просто логируем, что FSM остановка не требуется для одобрения
                logging.info(f"FSM остановка не требуется для одобрения пользователя {user_id}")
            except Exception as e:
                logging.error(f"Ошибка при обработке FSM для пользователя {user_id}: {e}")
            
            # Отправляем меню выбора даты для следующей операции
            try:
                await show_main_menu(bot, user_id)
                logging.info(f"Главное меню отправлено пользователю {user_id}")
            except Exception as e:
                logging.error(f"Ошибка при отправке главного меню пользователю {user_id}: {e}")
            
            # Отправляем уведомления всем админам об одобрении
            user_name = get_user_name(user_id) or "Неизвестный пользователь"
            admin_notification_text = f"✅ <b>Ariza tasdiqlandi!</b>\n\nFoydalanuvchi <b>{user_name}</b> tomonidan kiritilgan ma'lumot tasdiqlandi va Google Sheet-ga yozildi.\n\n{format_summary(saved_data)}"
            
            # Добавляем информацию о балансе для админа
            balance_info = f"\n\n💰 <b>Balans:</b>\n"
            balance_info += f"💵 Dollarda: {format_number(e1_value)}\n"
            balance_info += f"💸 Somda: {format_number(g1_value)}"
            admin_notification_text += balance_info
            
            admins = get_all_admins()
            for admin_id, admin_name, added_date in admins:
                try:
                    await bot.send_message(admin_id, admin_notification_text)
                    logging.info(f"✅ Уведомление об одобрении отправлено админу {admin_id} ({admin_name})")
                except Exception as e:
                    error_msg = str(e)
                    if "Chat not found" in error_msg:
                        logging.error(f"❌ Админ {admin_id} ({admin_name}) не найден в чате")
                    elif "Forbidden" in error_msg:
                        logging.error(f"❌ Админ {admin_id} ({admin_name}) заблокировал бота")
                    else:
                        logging.error(f"❌ Ошибка отправки уведомления об одобрении админу {admin_id}: {error_msg}")
        else:
            logging.warning(f"Данные для ключа одобрения {approval_key} не найдены")
            try:
                await call.answer('Ma\'lumotlar topilmadi!', show_alert=True)
            except Exception as e:
                logging.error(f"Ошибка при отправке сообщения о данных: {e}")
    except Exception as e:
        logging.error(f"Ошибка при одобрении: {e}")
        try:
            await call.answer('Xatolik yuz berdi!', show_alert=True)
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения об ошибке: {e}")

# Обработка отклонения больших сумм
@dp.callback_query_handler(lambda c: c.data.startswith('reject_large_'), state='*')
async def reject_large_amount(call: types.CallbackQuery, state: FSMContext):
    logging.info(f"Отклонение больших сумм вызвано: {call.data}")
    
    # Сразу отвечаем на callback чтобы кнопка не "зависла"
    await safe_answer_callback(call)
    
    # Проверяем дедупликацию - если callback уже был обработан, выходим
    if is_callback_processed(f"reject_{call.data}"):
        logging.info(f"Callback {call.data} уже был обработан для отклонения")
        return
    mark_callback_processed(f"reject_{call.data}")
    
    if not is_admin(call.from_user.id):
        try:
            await call.answer('Faqat admin uchun!', show_alert=True)
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения о правах: {e}")
        return
    
    # Парсим данные из callback
    try:
        parts = call.data.split('_')
        if len(parts) < 4:
            logging.error(f"Неверный формат callback данных: {call.data}")
            await call.answer('Xatolik: noto\'g\'ri ma\'lumotlar', show_alert=True)
            return
            
        user_id = int(parts[2])
        timestamp = int(parts[3])
        approval_key = f"{user_id}_{timestamp}"
        
        logging.info(f"Rejection key: {approval_key}, user_id: {user_id}, timestamp: {timestamp}")
    except (ValueError, IndexError) as e:
        logging.error(f"Ошибка парсинга callback данных: {e}, data: {call.data}")
        await call.answer('Xatolik: noto\'g\'ri ma\'lumotlar', show_alert=True)
        return
    
    # Проверяем, не был ли уже обработан этот ключ одобрения
    if not check_approval_status(approval_key):
        logging.warning(f"Ключ одобрения {approval_key} уже был обработан или не существует")
        try:
            await call.answer('Bu ariza allaqachon ko\'rib chiqilgan yoki mavjud emas!', show_alert=True)
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения о статусе: {e}")
        return
    
    try:
        # Отправляем сообщение пользователю
        await bot.send_message(user_id, '❌ Arizangiz administrator tomonidan rad etildi.')
        
        # Удаляем из базы данных
        if delete_pending_approval(approval_key):
            logging.info(f"Заявка удалена из базы данных: {approval_key}")
        else:
            logging.warning(f"Заявка не найдена в базе данных для удаления: {approval_key}")
            # Проверяем, может быть другой админ уже обработал заявку
            if not check_approval_status(approval_key):
                await safe_edit_text(call.message, '❌ Ariza ma\'lumotlari topilmadi. Boshqa admin tomonidan tasdiqlangan yoki rad etilgan bo\'lishi mumkin.', reply_markup=None)
                return
        
        # Останавливаем FSM для пользователя, который отправил заявку
        try:
            # Просто логируем, что FSM остановка не требуется для отклонения
            logging.info(f"FSM остановка не требуется для отклонения пользователя {user_id}")
        except Exception as e:
            logging.error(f"Ошибка при обработке FSM для пользователя {user_id}: {e}")
        
        # Отправляем меню выбора даты для следующей операции
        try:
            await show_main_menu(bot, user_id)
            logging.info(f"Главное меню отправлено пользователю {user_id}")
        except Exception as e:
            logging.error(f"Ошибка при отправке главного меню пользователю {user_id}: {e}")
        
        # Убираем только кнопки, оставляем оригинальный текст
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except Exception as edit_error:
            if "Message is not modified" in str(edit_error):
                logging.info("Сообщение уже не имеет кнопок")
            else:
                logging.error(f"Ошибка при удалении кнопок: {edit_error}")
        
    except Exception as e:
        logging.error(f"Ошибка при отклонении: {e}")
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except Exception as edit_error:
            if "Message is not modified" in str(edit_error):
                logging.info("Сообщение уже не имеет кнопок")
            else:
                logging.error(f"Ошибка при удалении кнопок: {edit_error}")

# --- Команды для админа ---
@dp.message_handler(commands=['test_approval'], state='*')
async def test_approval_cmd(msg: types.Message, state: FSMContext):
    """Тестирует кнопки одобрения для отладки"""
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    
    await state.finish()  # Сброс состояния
    
    # Создаем тестовые данные
    test_data = {
        'type': 'Чиқим',
        'object_name': 'Test Object',
        'expense_type': 'Test Expense',
        'currency_type': 'Сом',
        'payment_type': 'Test Payment',
        'amount': '15000000',
        'comment': 'Test comment',
        'user_id': msg.from_user.id
    }
    
    # Создаем тестовое сообщение с кнопками
    summary_text = format_summary(test_data)
    admin_approval_text = f"⚠️ <b>Tasdiqlash talab qilinadi!</b>\n\nTest ma'lumot:\n\n{summary_text}"
    
    # Создаем кнопки для админа
    admin_kb = InlineKeyboardMarkup(row_width=2)
    admin_kb.add(
        InlineKeyboardButton('✅ Tasdiqlash', callback_data=f'approve_large_{msg.from_user.id}_{int(datetime.now().timestamp())}'),
        InlineKeyboardButton('❌ Rad etish', callback_data=f'reject_large_{msg.from_user.id}_{int(datetime.now().timestamp())}')
    )
    
    await msg.answer(admin_approval_text, reply_markup=admin_kb)

@dp.message_handler(commands=['check_db'], state='*')
async def check_db_cmd(msg: types.Message, state: FSMContext):
    """Проверяет состояние базы данных для отладки"""
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    
    await state.finish()  # Сброс состояния
    
    try:
        # Проверяем таблицу pending_approvals
        conn = get_db_conn()
        c = conn.cursor()
        
        # Получаем все записи
        c.execute('SELECT COUNT(*) FROM pending_approvals')
        total_count = c.fetchone()[0]
        
        c.execute('SELECT approval_key, user_id, created_at FROM pending_approvals ORDER BY created_at DESC LIMIT 10')
        recent_records = c.fetchall()
        
        conn.close()
        
        response = f"🔍 <b>Состояние БД:</b>\n\n"
        response += f"📊 Всего записей в pending_approvals: {total_count}\n\n"
        
        if recent_records:
            response += "📋 <b>Последние 10 записей:</b>\n"
            for i, (key, user_id, created_at) in enumerate(recent_records, 1):
                response += f"{i}. <code>{key}</code>\n"
                response += f"   User: {user_id}, Время: {created_at}\n\n"
        else:
            response += "❌ Нет записей в БД\n"
        
        await msg.answer(response)
        
    except Exception as e:
        await msg.answer(f"❌ Ошибка при проверке БД: {e}")

@dp.message_handler(commands=['clear_old_approvals'], state='*')
async def clear_old_approvals_cmd(msg: types.Message, state: FSMContext):
    """Очищает старые записи из таблицы одобрений"""
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    
    await state.finish()  # Сброс состояния
    
    try:
        conn = get_db_conn()
        c = conn.cursor()
        
        # Удаляем записи старше 24 часов
        c.execute("DELETE FROM pending_approvals WHERE created_at < NOW() - INTERVAL '24 hours'")
        deleted_count = c.rowcount
        
        conn.commit()
        conn.close()
        
        await msg.answer(f"✅ Удалено {deleted_count} старых записей из БД")
        
    except Exception as e:
        await msg.answer(f"❌ Ошибка при очистке БД: {e}")

@dp.message_handler(commands=['check_fsm'], state='*')
async def check_fsm_cmd(msg: types.Message, state: FSMContext):
    """Проверяет FSM состояние пользователя"""
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    
    await state.finish()  # Сброс состояния
    
    try:
        # Получаем всех пользователей с их FSM состояниями
        conn = get_db_conn()
        c = conn.cursor()
        
        # Проверяем, есть ли таблица FSM состояний (зависит от типа storage)
        c.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%fsm%'
        """)
        fsm_tables = c.fetchall()
        
        response = f"🔍 <b>FSM состояния:</b>\n\n"
        response += f"📊 Найдено FSM таблиц: {len(fsm_tables)}\n"
        
        if fsm_tables:
            for table in fsm_tables:
                response += f"   - {table[0]}\n"
                
                # Показываем содержимое первой FSM таблицы
                try:
                    c.execute(f"SELECT * FROM {table[0]} LIMIT 5")
                    rows = c.fetchall()
                    if rows:
                        response += f"   Примеры записей:\n"
                        for i, row in enumerate(rows[:3], 1):
                            response += f"   {i}. {row}\n"
                except Exception as e:
                    response += f"   Ошибка чтения: {e}\n"
        else:
            response += "❌ FSM таблицы не найдены\n"
        
        conn.close()
        await msg.answer(response)
        
    except Exception as e:
        await msg.answer(f"❌ Ошибка при проверке FSM: {e}")

@dp.message_handler(commands=['reset_approval_system'], state='*')
async def reset_approval_system_cmd(msg: types.Message, state: FSMContext):
    """Полностью сбрасывает систему одобрения"""
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    
    await state.finish()  # Сброс состояния
    
    try:
        conn = get_db_conn()
        c = conn.cursor()
        
        # Удаляем все записи из таблицы одобрений
        c.execute("DELETE FROM pending_approvals")
        deleted_count = c.rowcount
        
        conn.commit()
        conn.close()
        
        await msg.answer(f"🔄 Система одобрения полностью сброшена!\n✅ Удалено {deleted_count} записей из БД\n\nТеперь можно тестировать заново.")
        
    except Exception as e:
        await msg.answer(f"❌ Ошибка при сбросе системы: {e}")

@dp.message_handler(commands=['debug_start'], state='*')
async def debug_start_cmd(msg: types.Message, state: FSMContext):
    """Отлаживает команду /start"""
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    
    await state.finish()  # Сброс состояния
    
    try:
        user_id = msg.from_user.id
        status = get_user_status(user_id)
        
        response = f"🔍 <b>Отладка /start:</b>\n\n"
        response += f"👤 User ID: {user_id}\n"
        response += f"📊 Status: {status}\n"
        response += f"🔑 FSM State: {state.state}\n"
        
        # Проверяем, есть ли пользователь в БД
        conn = get_db_conn()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
        user_data = c.fetchone()
        conn.close()
        
        if user_data:
            response += f"✅ Пользователь найден в БД\n"
            response += f"📝 Данные: {user_data}\n"
        else:
            response += f"❌ Пользователь не найден в БД\n"
        
        await msg.answer(response)
        
    except Exception as e:
        await msg.answer(f"❌ Ошибка при отладке: {e}")

@dp.message_handler(commands=['test_start'], state='*')
async def test_start_cmd(msg: types.Message, state: FSMContext):
    """Тестирует команду /start без ошибок"""
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    
    try:
        await state.finish()  # Сброс состояния
        await msg.answer("🔄 Тестирую команду /start...")
        
        # Вызываем start функцию напрямую
        await start(msg, state)
        
        await msg.answer("✅ Команда /start выполнена успешно!")
        
    except Exception as e:
        await msg.answer(f"❌ Ошибка при тестировании /start: {e}")
        logging.error(f"Ошибка при тестировании /start: {e}")

@dp.message_handler(commands=['test_date'], state='*')
async def test_date_cmd(msg: types.Message, state: FSMContext):
    """Тестирует выбор даты"""
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    
    try:
        await state.finish()  # Сброс состояния
        
        # Показываем меню выбора даты
        await show_main_menu(msg, state)
        
        await msg.answer("✅ Меню выбора даты показано. Выберите 'Bugun' или 'Kecha' для тестирования.")
        
    except Exception as e:
        await msg.answer(f"❌ Ошибка при тестировании даты: {e}")
        logging.error(f"Ошибка при тестировании даты: {e}")

@dp.message_handler(commands=['test_google_sheet'], state='*')
async def test_google_sheet_cmd(msg: types.Message, state: FSMContext):
    """Тестирует запись в Google Sheet"""
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    
    try:
        await state.finish()  # Сброс состояния
        
        # Создаем тестовые данные
        test_data = {
            'object_name': 'Test Object',
            'type': 'Кирим',
            'expense_type': 'Test Expense',
            'comment': 'Test comment',
            'amount': '1000000',
            'currency_type': 'Сом',
            'payment_type': 'Test Payment',
            'dt_for_sheet': '8/28/2025',
            'vaqt': '12:00',
            'user_id': msg.from_user.id
        }
        
        await msg.answer("🔄 Тестирую запись в Google Sheet...")
        
        # Пытаемся записать в Google Sheet
        success = add_to_google_sheet(test_data)
        
        if success:
            await msg.answer("✅ Тестовая запись успешно добавлена в Google Sheet!")
        else:
            await msg.answer("❌ Ошибка при записи в Google Sheet")
        
    except Exception as e:
        await msg.answer(f"❌ Ошибка при тестировании Google Sheet: {e}")
        logging.error(f"Ошибка при тестировании Google Sheet: {e}")

@dp.message_handler(commands=['check_google_config'], state='*')
async def check_google_config_cmd(msg: types.Message, state: FSMContext):
    """Проверяет конфигурацию Google Sheets"""
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    
    try:
        await state.finish()  # Сброс состояния
        
        response = "🔍 <b>Проверка конфигурации Google Sheets:</b>\n\n"
        
        # Проверяем переменные окружения
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        # Проверяем CREDENTIALS_FILE
        credentials_file = os.getenv('CREDENTIALS_FILE', 'credentials.json')
        if os.path.exists(credentials_file):
            response += f"✅ Файл credentials: {credentials_file}\n"
        else:
            response += f"❌ Файл credentials не найден: {credentials_file}\n"
        
        # Проверяем SHEET_ID
        sheet_id = os.getenv('SHEET_ID', '')
        if sheet_id:
            response += f"✅ Sheet ID: {sheet_id[:10]}...\n"
        else:
            response += f"❌ Sheet ID не найден\n"
        
        # Проверяем SHEET_NAME
        sheet_name = os.getenv('SHEET_NAME', '')
        if sheet_name:
            response += f"✅ Sheet Name: {sheet_name}\n"
        else:
            response += f"❌ Sheet Name не найден\n"
        
        # Проверяем SCOPES
        scopes = os.getenv('SCOPES', '')
        if scopes:
            response += f"✅ Scopes: {scopes}\n"
        else:
            response += f"❌ Scopes не найдены\n"
        
        await msg.answer(response)
        
    except Exception as e:
        await msg.answer(f"❌ Ошибка при проверке конфигурации: {e}")
        logging.error(f"Ошибка при проверке конфигурации: {e}")

@dp.message_handler(commands=['add_tolov'], state='*')
async def add_paytype_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    await state.finish()  # Сброс состояния
    await msg.answer('Yangi To\'lov turi nomini yuboring:')
    await state.set_state('add_paytype')

@dp.message_handler(state='add_paytype', content_types=types.ContentTypes.TEXT)
async def add_paytype_save(msg: types.Message, state: FSMContext):
    name = msg.text.strip()
    conn = get_db_conn()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO pay_types (name) VALUES (%s)', (name,))
        conn.commit()
        await msg.answer(f'✅ Yangi To\'lov turi qo\'shildi: {name}')
    except IntegrityError:
        await msg.answer('❗️ Bu nom allaqachon mavjud.')
        conn.rollback()
    conn.close()
    await state.finish()

@dp.message_handler(commands=['add_category'], state='*')
async def add_category_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    await state.finish()  # Сброс состояния
    await msg.answer('Yangi kategoriya nomini yuboring:')
    await state.set_state('add_category')

@dp.message_handler(state='add_category', content_types=types.ContentTypes.TEXT)
async def add_category_save(msg: types.Message, state: FSMContext):
    # Удаляем эмодзи из названия категории
    name = clean_emoji(msg.text.strip())
    conn = get_db_conn()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO categories (name) VALUES (%s)', (name,))
        conn.commit()
        await msg.answer(f'✅ Yangi kategoriya qo\'shildi: {name}')
    except IntegrityError:
        await msg.answer('❗️ Bu nom allaqachon mavjud.')
        conn.rollback()
    conn.close()
    await state.finish()

# --- Удаление и изменение To'lov turi ---
@dp.message_handler(commands=['del_tolov'], state='*')
async def del_tolov_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    await state.finish()  # Сброс состояния
    kb = InlineKeyboardMarkup(row_width=1)
    for name in get_pay_types():
        kb.add(InlineKeyboardButton(f'❌ {name}', callback_data=f'del_tolov_{name}'))
    await msg.answer('O\'chirish uchun To\'lov turini tanlang:', reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('del_tolov_'))
async def del_tolov_cb(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer('Faqat admin uchun!', show_alert=True)
        return
    name = call.data[len('del_tolov_'):]
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('DELETE FROM pay_types WHERE name=%s', (name,))
    conn.commit()
    conn.close()
    await safe_edit_text(call.message, f'❌ To\'lov turi o\'chirildi: {name}')
    await safe_answer_callback(call)

@dp.message_handler(commands=['edit_tolov'], state='*')
async def edit_tolov_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    await state.finish()  # Сброс состояния
    kb = InlineKeyboardMarkup(row_width=1)
    for name in get_pay_types():
        kb.add(InlineKeyboardButton(f'✏️ {name}', callback_data=f'edit_tolov_{name}'))
    await msg.answer('Tahrirlash uchun To\'lov turini tanlang:', reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('edit_tolov_'))
async def edit_tolov_cb(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer('Faqat admin uchun!', show_alert=True)
        return
    old_name = call.data[len('edit_tolov_'):]
    await state.update_data(edit_tolov_old=old_name)
    await call.message.answer(f'Yangi nomini yuboring (eski: {old_name}):')
    await state.set_state('edit_tolov_new')
    await safe_answer_callback(call)

@dp.message_handler(state='edit_tolov_new', content_types=types.ContentTypes.TEXT)
async def edit_tolov_save(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    old_name = data.get('edit_tolov_old')
    new_name = msg.text.strip()
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('UPDATE pay_types SET name=%s WHERE name=%s', (new_name, old_name))
    conn.commit()
    conn.close()
    await msg.answer(f'✏️ To\'lov turi o\'zgartirildi: {old_name} -> {new_name}')
    await state.finish()

# --- Удаление и изменение Kotegoriyalar ---
@dp.message_handler(commands=['del_category'], state='*')
async def del_category_cmd(msg: types.Message, state: FSMContext):
    if msg.from_user.id not in ADMINS:
        await msg.answer('Faqat admin uchun!')
        return
    await state.finish()  # Сброс состояния
    kb = InlineKeyboardMarkup(row_width=1)
    for name in get_categories():
        kb.add(InlineKeyboardButton(f'❌ {name}', callback_data=f'del_category_{name}'))
    await msg.answer('O\'chirish uchun kategoriya tanlang:', reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('del_category_'))
async def del_category_cb(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer('Faqat admin uchun!', show_alert=True)
        return
    name = call.data[len('del_category_'):]
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('DELETE FROM categories WHERE name=%s', (name,))
    conn.commit()
    conn.close()
    await safe_edit_text(call.message, f'❌ Kategoriya o\'chirildi: {name}')
    await safe_answer_callback(call)

@dp.message_handler(commands=['edit_category'], state='*')
async def edit_category_cmd(msg: types.Message, state: FSMContext):
    if msg.from_user.id not in ADMINS:
        await msg.answer('Faqat admin uchun!')
        return
    await state.finish()  # Сброс состояния
    kb = InlineKeyboardMarkup(row_width=1)
    for name in get_categories():
        kb.add(InlineKeyboardButton(f'✏️ {name}', callback_data=f'edit_category_{name}'))
    await msg.answer('Tahrirlash uchun kategoriya tanlang:', reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('edit_category_'))
async def edit_category_cb(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer('Faqat admin uchun!', show_alert=True)
        return
    old_name = call.data[len('edit_category_'):]
    await state.update_data(edit_category_old=old_name)
    await call.message.answer(f'Yangi nomini yuboring (eski: {old_name}):')
    await state.set_state('edit_category_new')
    await safe_answer_callback(call)

@dp.message_handler(state='edit_category_new', content_types=types.ContentTypes.TEXT)
async def edit_category_save(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    old_name = data.get('edit_category_old')
    new_name = msg.text.strip()
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('UPDATE categories SET name=%s WHERE name=%s', (new_name, old_name))
    conn.commit()
    conn.close()
    await msg.answer(f'✏️ Kategoriya o\'zgartirildi: {old_name} -> {new_name}')
    await state.finish()

# --- Команды для управления объектами ---
@dp.message_handler(commands=['add_object'], state='*')
async def add_object_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    await state.finish()
    await msg.answer('Yangi объект номини yuboring:')
    await state.set_state('add_object')

@dp.message_handler(state='add_object', content_types=types.ContentTypes.TEXT)
async def add_object_save(msg: types.Message, state: FSMContext):
    name = msg.text.strip()
    conn = get_db_conn()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO object_names (name) VALUES (%s)', (name,))
        conn.commit()
        await msg.answer(f'✅ Yangi объект номи qo\'shildi: {name}')
    except IntegrityError:
        await msg.answer('❗️ Bu nom allaqachon mavjud.')
        conn.rollback()
    conn.close()
    await state.finish()

@dp.message_handler(commands=['add_expense'], state='*')
async def add_expense_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    await state.finish()
    await msg.answer('Yangi харажат турини yuboring:')
    await state.set_state('add_expense')

@dp.message_handler(state='add_expense', content_types=types.ContentTypes.TEXT)
async def add_expense_save(msg: types.Message, state: FSMContext):
    name = msg.text.strip()
    conn = get_db_conn()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO expense_types (name) VALUES (%s)', (name,))
        conn.commit()
        await msg.answer(f'✅ Yangi харажат тури qo\'shildi: {name}')
    except IntegrityError:
        await msg.answer('❗️ Bu nom allaqachon mavjud.')
        conn.rollback()
    conn.close()
    await state.finish()

@dp.message_handler(commands=['del_object'], state='*')
async def del_object_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    await state.finish()
    kb = InlineKeyboardMarkup(row_width=1)
    for name in get_object_names():
        kb.add(InlineKeyboardButton(f'❌ {name}', callback_data=f'del_object_{name}'))
    await msg.answer('O\'chirish uchun объект номини tanlang:', reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('del_object_'))
async def del_object_cb(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer('Faqat admin uchun!', show_alert=True)
        return
    name = call.data[len('del_object_'):]
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('DELETE FROM object_names WHERE name=%s', (name,))
    conn.commit()
    conn.close()
    await safe_edit_text(call.message, f'❌ Объект номи o\'chirildi: {name}')
    await safe_answer_callback(call)

@dp.message_handler(commands=['del_expense'], state='*')
async def del_expense_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    await state.finish()
    kb = InlineKeyboardMarkup(row_width=1)
    for name in get_expense_types():
        kb.add(InlineKeyboardButton(f'❌ {name}', callback_data=f'del_expense_{name}'))
    await msg.answer('O\'chirish uchun харажат турини tanlang:', reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('del_expense_'))
async def del_expense_cb(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer('Faqat admin uchun!', show_alert=True)
        return
    name = call.data[len('del_expense_'):]
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('DELETE FROM expense_types WHERE name=%s', (name,))
    conn.commit()
    conn.close()
    await safe_edit_text(call.message, f'❌ Харажат тури o\'chirildi: {name}')
    await safe_answer_callback(call)

@dp.message_handler(commands=['check_sheets'], state='*')
async def check_sheets_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    await state.finish()
    
    sheet_names = get_sheet_names()
    if sheet_names:
        response = "📋 Доступные листы в Google Sheet:\n\n"
        for i, name in enumerate(sheet_names, 1):
            response += f"{i}. {name}\n"
        await msg.answer(response)
    else:
        await msg.answer("❌ Не удалось получить список листов")

@dp.message_handler(commands=['update_lists'], state='*')
async def update_lists_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    
    try:
        conn = get_db_conn()
        c = conn.cursor()
        
        # Очищаем старые данные
        c.execute('DELETE FROM object_names')
        c.execute('DELETE FROM expense_types')
        
        # Добавляем новые объекты
        for obj in object_names:
            c.execute('INSERT INTO object_names (name) VALUES (%s)', (obj,))
        
        # Добавляем новые типы расходов
        for exp in expense_types:
            c.execute('INSERT INTO expense_types (name) VALUES (%s)', (exp,))
        
        conn.commit()
        conn.close()
        
        await msg.answer('✅ Списки объектов и типов расходов обновлены!')
    except Exception as e:
        await msg.answer(f'❌ Ошибка при обновлении списков: {e}')

@dp.message_handler(commands=['userslist'], state='*')
async def users_list_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    await state.finish()  # Сброс состояния
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT user_id, name, phone, reg_date FROM users WHERE status='approved'")
    rows = c.fetchall()
    conn.close()
    if not rows:
        await msg.answer('Hali birorta ham tasdiqlangan foydalanuvchi yo\'q.')
        return
    text = '<b>Tasdiqlangan foydalanuvchilar:</b>\n'
    for i, (user_id, name, phone, reg_date) in enumerate(rows, 1):
        text += f"\n{i}. <b>{name}</b>\nID: <code>{user_id}</code>\nTelefon: <code>{phone}</code>\nRo'yxatdan o'tgan: {reg_date}\n"
    await msg.answer(text)

@dp.message_handler(commands=['block_user'], state='*')
async def block_user_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    await state.finish()  # Сброс состояния
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT user_id, name FROM users WHERE status='approved'")
    rows = c.fetchall()
    conn.close()
    if not rows:
        await msg.answer('Hali birorta ham tasdiqlangan foydalanuvchi yo\'q.')
        return
    kb = InlineKeyboardMarkup(row_width=1)
    for user_id, name in rows:
        kb.add(InlineKeyboardButton(f'🚫 {name} ({user_id})', callback_data=f'blockuser_{user_id}'))
    await msg.answer('Bloklash uchun foydalanuvchini tanlang:', reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('blockuser_'))
async def block_user_cb(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer('Faqat admin uchun!', show_alert=True)
        return
    user_id = int(call.data[len('blockuser_'):])
    update_user_status(user_id, 'denied')
    try:
        await bot.send_message(user_id, '❌ Sizga botdan foydalanishga ruxsat berilmagan. (Admin tomonidan bloklandi)')
    except Exception:
        pass
    await safe_edit_text(call.message, f'🚫 Foydalanuvchi bloklandi: {user_id}')
    await safe_answer_callback(call)

@dp.message_handler(commands=['approve_user'], state='*')
async def approve_user_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    await state.finish()  # Сброс состояния
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT user_id, name FROM users WHERE status='denied'")
    rows = c.fetchall()
    conn.close()
    if not rows:
        await msg.answer('Hali birorta ham bloklangan foydalanuvchi yo\'q.')
        return
    kb = InlineKeyboardMarkup(row_width=1)
    for user_id, name in rows:
        kb.add(InlineKeyboardButton(f'✅ {name} ({user_id})', callback_data=f'approveuser_{user_id}'))
    await msg.answer('Qayta tasdiqlash uchun foydalanuvchini tanlang:', reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('approveuser_'))
async def approve_user_cb(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer('Faqat admin uchun!', show_alert=True)
        return
    user_id = int(call.data[len('approveuser_'):])
    update_user_status(user_id, 'approved')
    try:
        await bot.send_message(user_id, '✅ Sizga botdan foydalanishga yana ruxsat berildi! /start')
    except Exception:
        pass
    await safe_edit_text(call.message, f'✅ Foydalanuvchi qayta tasdiqlandi: {user_id}')
    await safe_answer_callback(call)

# --- Команды для управления админами ---
@dp.message_handler(commands=['add_admin'], state='*')
async def add_admin_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    await state.finish()
    await msg.answer('Yangi admin ID raqamini yuboring:')
    await state.set_state('add_admin_id')

@dp.message_handler(state='add_admin_id', content_types=types.ContentTypes.TEXT)
async def add_admin_id_save(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    
    try:
        user_id = int(msg.text.strip())
        if user_id <= 0:
            await msg.answer('❌ Noto\'g\'ri ID raqam!')
            await state.finish()
            return
        
        # Проверяем, не является ли уже админом
        if is_admin(user_id):
            await msg.answer('❌ Bu foydalanuvchi allaqachon admin!')
            await state.finish()
            return
        
        # Сохраняем ID для следующего шага
        await state.update_data(admin_id=user_id)
        await msg.answer('Yangi admin ismini yuboring:')
        await state.set_state('add_admin_name')
        
    except ValueError:
        await msg.answer('❌ Noto\'g\'ri format! Faqat raqam kiriting.')
        await state.finish()

@dp.message_handler(state='add_admin_name', content_types=types.ContentTypes.TEXT)
async def add_admin_name_save(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    
    data = await state.get_data()
    user_id = data.get('admin_id')
    admin_name = msg.text.strip()
    
    if add_admin(user_id, admin_name, msg.from_user.id):
        await msg.answer(f"✅ Yangi admin qo'shildi:\nID: <code>{user_id}</code>\nIsmi: <b>{admin_name}</b>")
        try:
            await bot.send_message(user_id, f'🎉 Sizga admin huquqlari berildi! Botda barcha admin funksiyalaridan foydalanishingiz mumkin.')
        except Exception:
            pass
    else:
        await msg.answer('❌ Xatolik yuz berdi!')
    
    await state.finish()

@dp.message_handler(commands=['remove_admin'], state='*')
async def remove_admin_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    await state.finish()
    
    admins = get_all_admins()
    if not admins:
        await msg.answer("Hali birorta ham admin yo'q.")

        return
    
    kb = InlineKeyboardMarkup(row_width=1)
    for user_id, name, added_date in admins:
        kb.add(InlineKeyboardButton(f'👤 {name} ({user_id})', callback_data=f'removeadmin_{user_id}'))
    
    await msg.answer("O'chirish uchun adminni tanlang:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('removeadmin_'))
async def remove_admin_cb(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer('Faqat admin uchun!', show_alert=True)
        return
    
    user_id = int(call.data[len('removeadmin_'):])
    
    # Нельзя удалить самого себя
    if user_id == call.from_user.id:
        await call.answer("❌ O'zingizni o'chira olmaysiz!", show_alert=True)
        return
    
    if remove_admin(user_id):
        await safe_edit_text(call.message, f"✅ Admin o'chirildi: {user_id}")
        try:
            await bot.send_message(user_id, '❌ Sizning admin huquqlaringiz olib tashlandi.')
        except Exception:
            pass
    else:
        await safe_edit_text(call.message, '❌ Xatolik yuz berdi!')
    
    await safe_answer_callback(call)

@dp.message_handler(commands=['admins_list'], state='*')
async def admins_list_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    await state.finish()
    
    admins = get_all_admins()
    if not admins:
        await msg.answer("Hali birorta ham admin yo'q.")
        return
    
    text = "<b>📋 Adminlar ro'yxati:</b>\n\n"
    for i, (user_id, name, added_date) in enumerate(admins, 1):
        text += f"{i}. <b>{name}</b>\nID: <code>{user_id}</code>\nQo'shilgan: {added_date}\n\n"
    
    await msg.answer(text)

@dp.message_handler(commands=['check_admins'], state='*')
async def check_admins_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    
    admins = get_all_admins()
    if admins:
        admin_list = "📋 <b>Ro'yxatdagi adminlar:</b>\n\n"
        for i, (admin_id, name, added_date) in enumerate(admins, 1):
            admin_list += f"{i}. <b>{name}</b> (ID: {admin_id})\n"
            admin_list += f"   Qo'shilgan: {added_date}\n\n"
        await msg.answer(admin_list)
    else:
        await msg.answer("❌ Adminlar topilmadi.")

@dp.message_handler(commands=['pending_approvals'], state='*')
async def pending_approvals_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer('Faqat admin uchun!')
        return
    
    await state.finish()  # Сброс состояния
    
    pending_list = get_all_pending_approvals()
    if pending_list:
        response = "📋 <b>Kutilayotgan tasdiqlashlar:</b>\n\n"
        for i, approval in enumerate(pending_list, 1):
            data = approval['data']
            user_name = get_user_name(approval['user_id']) or f"User {approval['user_id']}"
            response += f"{i}. <b>{user_name}</b> (ID: {approval['user_id']})\n"
            response += f"   Tur: {data.get('type', 'N/A')}\n"
            response += f"   Summa: {data.get('amount', 'N/A')} {data.get('currency_type', '')}\n"
            response += f"   Vaqt: {approval['created_at']}\n"
            response += f"   Key: {approval['approval_key']}\n\n"
        await msg.answer(response)
    else:
        await msg.answer("✅ Kutilayotgan tasdiqlashlar yo'q.")

async def set_user_commands(dp):
    commands = [
        types.BotCommand("start", "Botni boshlash"),
        types.BotCommand("reboot", "Qayta boshlash - FSM ni to'xtatish"),
        # Здесь можно добавить другие публичные команды
    ]
    await dp.bot.set_my_commands(commands)

async def notify_all_users(bot):
    """Отправляет уведомления всем одобренным пользователям"""
    try:
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE status='approved'")
        rows = c.fetchall()
        conn.close()
        
        total_users = len(rows)
        successful_sends = 0
        failed_sends = 0
        
        logger.info(f"📤 Отправка уведомлений {total_users} пользователям...")
        
        for (user_id,) in rows:
            try:
                await bot.send_message(user_id, "Iltimos, /start ni bosing va botdan foydalanishni davom eting!")
                successful_sends += 1
                # Небольшая задержка между отправками для избежания спама
                await asyncio.sleep(0.1)
            except Exception as e:
                failed_sends += 1
                error_msg = str(e)
                if "bot was blocked" in error_msg.lower() or "user is deactivated" in error_msg.lower():
                    logger.warning(f"⚠️ Пользователь {user_id} заблокировал бота или деактивирован")
                elif "chat not found" in error_msg.lower():
                    logger.warning(f"⚠️ Чат с пользователем {user_id} не найден")
                else:
                    logger.warning(f"⚠️ Не удалось отправить сообщение пользователю {user_id}: {e}")
        
        logger.info(f"✅ Уведомления отправлены: {successful_sends}/{total_users} успешно, {failed_sends} неудачно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке уведомлений: {e}")
        raise

# --- Функции для работы с данными одобрения в базе данных ---
def save_pending_approval(approval_key, user_id, data):
    import json
    from datetime import datetime
    
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            return super().default(obj)
    
    conn = get_db_conn()
    c = conn.cursor()
    try:
        # Создаем копию данных для безопасного изменения
        data_copy = data.copy()
        
        # Конвертируем datetime объекты в строки
        for key, value in data_copy.items():
            if isinstance(value, datetime):
                data_copy[key] = value.strftime('%Y-%m-%d %H:%M:%S')
        
        json_data = json.dumps(data_copy, cls=DateTimeEncoder)
        logging.info(f"Сохраняем данные в БД. Ключ: {approval_key}")
        logging.info(f"Данные: {data_copy}")
        
        c.execute('INSERT INTO pending_approvals (approval_key, user_id, data) VALUES (%s, %s, %s) ON CONFLICT (approval_key) DO NOTHING',
                  (approval_key, user_id, json_data))
        
        # Проверяем, была ли вставка выполнена
        if c.rowcount > 0:
            conn.commit()
            logging.info(f"✅ Данные успешно сохранены в БД для ключа: {approval_key}")
            return True
        else:
            logging.warning(f"⚠️ Запись с ключом {approval_key} уже существует в БД")
            conn.rollback()
            return False
        
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения данных одобрения: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_pending_approval(approval_key):
    import json
    conn = get_db_conn()
    c = conn.cursor()
    try:
        c.execute('SELECT data FROM pending_approvals WHERE approval_key = %s', (approval_key,))
        row = c.fetchone()
        if row:
            data = row[0]
            logging.info(f"Получены данные из БД для ключа {approval_key}. Тип: {type(data)}")
            
            # Если данные уже словарь, возвращаем как есть
            if isinstance(data, dict):
                logging.info(f"Данные уже в формате словаря: {data}")
                return data
            # Если это строка JSON, парсим её
            elif isinstance(data, str):
                logging.info(f"Парсим JSON строку: {data[:100]}...")
                return json.loads(data)
            else:
                logging.error(f"Неожиданный тип данных: {type(data)}, значение: {data}")
                return None
        else:
            logging.info(f"Данные не найдены в БД для ключа: {approval_key}")
        return None
    except Exception as e:
        logging.error(f"Ошибка получения данных одобрения: {e}")
        return None
    finally:
        conn.close()

def delete_pending_approval(approval_key):
    conn = get_db_conn()
    c = conn.cursor()
    try:
        c.execute('DELETE FROM pending_approvals WHERE approval_key = %s', (approval_key,))
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Ошибка удаления данных одобрения: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_all_pending_approvals():
    import json
    conn = get_db_conn()
    c = conn.cursor()
    try:
        c.execute('SELECT approval_key, user_id, data, created_at FROM pending_approvals ORDER BY created_at DESC')
        rows = c.fetchall()
        result = []
        for row in rows:
            data = row[2]
            # Если данные уже словарь, используем как есть
            if isinstance(data, dict):
                parsed_data = data
            # Если это строка JSON, парсим её
            elif isinstance(data, str):
                parsed_data = json.loads(data)
            else:
                logging.error(f"Неожиданный тип данных: {type(data)}")
                continue
                
            result.append({
                'approval_key': row[0],
                'user_id': row[1],
                'data': parsed_data,
                'created_at': row[3]
            })
        return result
    except Exception as e:
        logging.error(f"Ошибка получения всех данных одобрения: {e}")
        return []
    finally:
        conn.close()

def check_approval_status(approval_key):
    """Проверяет, существует ли заявка в базе данных"""
    conn = get_db_conn()
    c = conn.cursor()
    try:
        c.execute('SELECT COUNT(*) FROM pending_approvals WHERE approval_key = %s', (approval_key,))
        count = c.fetchone()[0]
        logging.info(f"Проверка статуса заявки {approval_key}: найдено {count} записей")
        return count > 0
    except Exception as e:
        logging.error(f"Ошибка проверки статуса заявки {approval_key}: {e}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    from aiogram import executor
    import asyncio
    
    async def on_startup(dp):
        logger.info("🚀 Бот запускается...")
        try:
            await set_user_commands(dp)
            logger.info("✅ Команды бота установлены")
            await notify_all_users(dp.bot)
            logger.info("✅ Уведомления отправлены")
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске: {e}")
        logger.info("✅ Бот успешно запущен и готов к работе")
    
    async def on_shutdown(dp):
        logger.info("🛑 Бот останавливается...")
        try:
            await dp.storage.close()
            await dp.storage.wait_closed()
            logger.info("✅ Хранилище закрыто")
        except Exception as e:
            logger.error(f"❌ Ошибка при остановке: {e}")
    
    try:
        logger.info("🔄 Запуск бота...")
        executor.start_polling(
            dp, 
            skip_updates=True, 
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            timeout=60,
            relax=0.1
        )
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
        raise
