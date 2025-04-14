import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        create_database(db_name)

    def user_exists(self, user_id):
        result = self.cursor.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone()
        return result is not None

    def update(self, user_id, name, phone):
        self.cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, name, phone, datetime, video_index, preferred_time, last_sent, is_subscribed) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, name, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0, "09:00", None, 1)
        )
        self.conn.commit()

    def get_name(self, user_id):
        result = self.cursor.execute("SELECT name FROM users WHERE user_id=?", (user_id,)).fetchone()
        return result[0] if result else "Не указано"

    def get_phone(self, user_id):
        result = self.cursor.execute("SELECT phone FROM users WHERE user_id=?", (user_id,)).fetchone()
        return result[0] if result else "Не указано"

    def get_registration_time(self, user_id):
        result = self.cursor.execute("SELECT datetime FROM users WHERE user_id=?", (user_id,)).fetchone()
        return result[0] if result else None

    def get_all_users(self):
        result = self.cursor.execute("SELECT user_id FROM users WHERE is_subscribed = 1").fetchall()
        return [row[0] for row in result]

    def get_all_users_data(self):
        result = self.cursor.execute("SELECT user_id, name, phone, datetime, video_index, preferred_time FROM users").fetchall()
        return result

    def get_video_index(self, user_id):
        result = self.cursor.execute("SELECT video_index FROM users WHERE user_id=?", (user_id,)).fetchone()
        if result is None:
            return 0
        return int(result[0])

    def update_video_index(self, user_id, index):
        self.cursor.execute("UPDATE users SET video_index=? WHERE user_id=?", (index, user_id))
        self.conn.commit()

    def get_preferred_time(self, user_id):
        result = self.cursor.execute("SELECT preferred_time FROM users WHERE user_id=?", (user_id,)).fetchone()
        return result[0] if result else "09:00"

    def set_preferred_time(self, user_id, time):
        print(f"Сохранение времени {time} для пользователя {user_id}")
        self.cursor.execute("UPDATE users SET preferred_time=? WHERE user_id=?", (time, user_id))
        self.conn.commit()
        updated_time = self.cursor.execute("SELECT preferred_time FROM users WHERE user_id=?", (user_id,)).fetchone()
        print(f"После обновления: preferred_time для {user_id} = {updated_time[0] if updated_time else 'Не найдено'}")

    def set_subscription_status(self, user_id, status):
        self.cursor.execute("UPDATE users SET is_subscribed=? WHERE user_id=?", (status, user_id))
        self.conn.commit()
        print(f"Статус подписки для пользователя {user_id} обновлён: is_subscribed = {status}")

    def get_subscription_status(self, user_id):
        result = self.cursor.execute("SELECT is_subscribed FROM users WHERE user_id=?", (user_id,)).fetchone()
        return result[0] if result else 1

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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            phone TEXT,
            datetime TEXT,
            video_index INTEGER DEFAULT 0,
            preferred_time TEXT DEFAULT "09:00",
            last_sent TEXT DEFAULT NULL,
            is_subscribed INTEGER DEFAULT 1
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS support (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            datetime TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    conn.commit()
    conn.close()

db = Database("databaseprotestim.db")