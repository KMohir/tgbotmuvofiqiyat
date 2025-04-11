import sqlite3
from datetime import datetime


class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        # Вызываем create_database при инициализации
        create_database(db_name)

    def user_exists(self, user_id):
        result = self.cursor.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone()
        return result is not None

    def update(self, lang, user_id, name, phone):
        self.cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, lang, name, phone, datetime) VALUES (?, ?, ?, ?, ?)",
            (user_id, lang, name, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        self.conn.commit()

    def get_lang(self, user_id):
        result = self.cursor.execute("SELECT lang FROM users WHERE user_id=?", (user_id,)).fetchone()
        if result is None:
            return 'uz'  # Возвращаем язык по умолчанию, если пользователь не найден
        return result[0]

    def get_name(self, user_id):
        result = self.cursor.execute("SELECT name FROM users WHERE user_id=?", (user_id,)).fetchone()
        return result[0] if result else "Не указано"

    def get_phone(self, user_id):
        result = self.cursor.execute("SELECT phone FROM users WHERE user_id=?", (user_id,)).fetchone()
        return result[0] if result else "Не указано"

    def change_lang(self, user_id, lang):
        self.cursor.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))
        self.conn.commit()

    def get_registration_time(self, user_id):
        result = self.cursor.execute("SELECT datetime FROM users WHERE user_id=?", (user_id,)).fetchone()
        return result[0] if result else None

    def get_all_users(self):
        result = self.cursor.execute("SELECT user_id FROM users").fetchall()
        return [row[0] for row in result]

    def get_all_users_data(self):
        result = self.cursor.execute("SELECT user_id, lang, name, phone, datetime FROM users").fetchall()
        return result

    def get_video_index(self):
        result = self.cursor.execute("SELECT value FROM settings WHERE key='video_index'").fetchone()
        if result is None:
            self.cursor.execute("INSERT INTO settings (key, value) VALUES ('video_index', 0)")
            self.conn.commit()
            return 0
        return int(result[0])

    def update_video_index(self, index):
        self.cursor.execute("UPDATE settings SET value=? WHERE key='video_index'", (index,))
        self.conn.commit()

    def add_questions(self, user_id, message_id):
        self.cursor.execute(
            "INSERT INTO support (user_id, message, datetime) VALUES (?, ?, ?)",
            (user_id, str(message_id), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        self.conn.commit()

    def get_id(self):
        result = self.cursor.execute("SELECT id FROM support ORDER BY id DESC LIMIT 1").fetchone()
        return result[0] if result else 1

    def get_question(self, user_id):
        result = self.cursor.execute("SELECT message FROM support WHERE user_id=?", (user_id,)).fetchone()
        return int(result[0]) if result else None

    def close(self):
        self.conn.close()


def create_database(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Создаём таблицу users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            lang TEXT NOT NULL,
            name TEXT,
            phone TEXT,
            datetime TEXT
        )
    ''')

    # Создаём таблицу support с правильной структурой
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS support (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            datetime TEXT
        )
    ''')

    # Создаём таблицу settings для хранения индекса видео
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    conn.commit()
    conn.close()


# Создаём экземпляр Database
db = Database("databaseprotestim.db")