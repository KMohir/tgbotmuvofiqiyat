import psycopg2
import json
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'mydatabase'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASS', '7777')
        )

    def get_viewed_videos(self, user_id: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT viewed_videos FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            if result and result[0]:
                return json.loads(result[0])
            return []
        except Exception as e:
            logger.error(f"Ошибка при получении просмотренных видео: {e}")
            return []

    def mark_video_as_viewed(self, user_id: int, video_index: int):
        try:
            viewed_videos = self.get_viewed_videos(user_id)
            if video_index not in viewed_videos:
                viewed_videos.append(video_index)
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE users SET viewed_videos = %s WHERE user_id = %s",
                    (json.dumps(viewed_videos), user_id)
                )
                self.conn.commit()
                cursor.close()
                logger.info(f"Видео {video_index} отмечено как просмотренное для пользователя {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при отметке видео как просмотренного: {e}")

    def get_video_by_index(self, video_index: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM videos WHERE position = %s", (video_index,))
            result = cursor.fetchone()
            cursor.close()
            if result:
                return {
                    'video_index': result[0],
                    'file_id': result[1],
                    'caption': result[2]
                }
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении видео по индексу {video_index}: {e}")
            return None

    def update_video_index(self, user_id: int, video_index: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE users SET video_index = %s WHERE user_id = %s",
                (video_index, user_id)
            )
            self.conn.commit()
            cursor.close()
            logger.info(f"Обновлен индекс видео для пользователя {user_id} на {video_index}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении индекса видео: {e}")
            return False

    def get_video_index(self, user_id: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT video_index FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Ошибка при получении индекса видео: {e}")
            return 0

    def get_subscription_status(self, user_id: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT is_subscribed FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return bool(result[0]) if result else False
        except Exception as e:
            logger.error(f"Ошибка при получении статуса подписки: {e}")
            return False

    def add_admin(self, user_id: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO admins (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении админа: {e}")
            return False

    def remove_admin(self, user_id: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM admins WHERE user_id = %s", (user_id,))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении админа: {e}")
            return False

    def is_admin(self, user_id: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM admins WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return result is not None
        except Exception as e:
            logger.error(f"Ошибка при проверке админа: {e}")
            return False

    def get_all_admins(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id FROM admins")
            result = cursor.fetchall()
            cursor.close()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Ошибка при получении списка админов: {e}")
            return [] 