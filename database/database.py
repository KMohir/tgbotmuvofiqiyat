from typing import List, Optional, Dict
import json
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, conn):
        self.conn = conn

    def get_viewed_videos(self, user_id: int) -> List[int]:
        """Получить список просмотренных видео для пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT viewed_videos FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            if result and result[0]:
                return json.loads(result[0])
            return []
        except Exception as e:
            logger.error(f"Ошибка при получении просмотренных видео: {e}")
            return []
        finally:
            cursor.close()

    def mark_video_as_viewed(self, user_id: int, video_index: int) -> None:
        """Отметить видео как просмотренное для пользователя"""
        try:
            cursor = self.conn.cursor()
            viewed_videos = self.get_viewed_videos(user_id)
            if video_index not in viewed_videos:
                viewed_videos.append(video_index)
                cursor.execute(
                    "UPDATE users SET viewed_videos = ? WHERE user_id = ?",
                    (json.dumps(viewed_videos), user_id)
                )
                self.conn.commit()
                logger.info(f"Видео {video_index} отмечено как просмотренное для пользователя {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при отметке видео как просмотренного: {e}")
        finally:
            cursor.close()

    def get_video_by_index(self, video_index: int) -> Optional[Dict]:
        """Получить видео по индексу"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM videos WHERE video_index = ?", (video_index,))
            result = cursor.fetchone()
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
        finally:
            cursor.close()

    def update_video_index(self, user_id: int, video_index: int) -> bool:
        """Обновить индекс видео для пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE users SET current_video_index = ? WHERE user_id = ?",
                (video_index, user_id)
            )
            self.conn.commit()
            logger.info(f"Обновлен индекс видео для пользователя {user_id} на {video_index}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении индекса видео: {e}")
            return False
        finally:
            cursor.close()

    def get_video_index(self, user_id: int) -> int:
        """Получить текущий индекс видео для пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT current_video_index FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Ошибка при получении индекса видео: {e}")
            return 0
        finally:
            cursor.close()

    def get_subscription_status(self, user_id: int) -> bool:
        """Получить статус подписки пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT is_subscribed FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return bool(result[0]) if result else False
        except Exception as e:
            logger.error(f"Ошибка при получении статуса подписки: {e}")
            return False
        finally:
            cursor.close() 