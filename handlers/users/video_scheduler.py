from aiogram import types
import asyncio
from datetime import datetime, timedelta
from db import db
from loader import dp, bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

# Список из 15 ссылок на сообщения в канале
VIDEO_LIST = [
    'https://t.me/c/2550852551/59',
    'https://t.me/c/2550852551/61',
    'https://t.me/c/2550852551/62',
    'https://t.me/c/2550852551/63',
    'https://t.me/c/2550852551/64',
    'https://t.me/c/2550852551/65',
    'https://t.me/c/2550852551/66',
    'https://t.me/c/2550852551/67',
    'https://t.me/c/2550852551/68',
    'https://t.me/c/2550852551/69',
    'https://t.me/c/2550852551/70',
    'https://t.me/c/2550852551/71',
    'https://t.me/c/2550852551/72',
    'https://t.me/c/2550852551/73',
    'https://t.me/c/2550852551/74'
]

# Инициализация планировщика
scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

# Функция для отправки видео
async def send_video_to_user(user_id, current_index):
    try:
        if current_index >= len(VIDEO_LIST):
            print(f"Ошибка: Индекс {current_index} превышает длину VIDEO_LIST ({len(VIDEO_LIST)})")
            current_index = 0
            db.update_video_index(user_id, current_index)

        video_url = VIDEO_LIST[current_index]
        message_id = int(video_url.split("/")[-1])  # Извлекаем message_id из ссылки

        print(f"Пересылка видео из канала {video_url} (message_id: {message_id}) пользователю {user_id} с индексом {current_index}")
        await bot.copy_message(
            chat_id=user_id,
            from_chat_id=-1002550852551,  # ID канала
            message_id=message_id,
            parse_mode="HTML",
            protect_content=True
        )
        await asyncio.sleep(1)

        next_index = (current_index + 1) % len(VIDEO_LIST)
        db.update_video_index(user_id, next_index)
        print(f"Видео пересыловано пользователю {user_id}, новый индекс: {next_index}")

    except Exception as e:
        print(f"Не удалось переслать видео пользователю {user_id}: {e}")

# Функция для проверки и отправки видео
async def check_and_send_videos():
    current_time = datetime.now(pytz.timezone("Asia/Tashkent"))
    current_time_str = current_time.strftime("%H:%M")
    print(f"Проверка времени: Текущее время = {current_time_str}")

    users = db.get_all_users()
    print(f"Найдено пользователей: {len(users)}")

    for user_id in users:
        try:
            # Проверяем статус подписки
            if not db.get_subscription_status(user_id):
                print(f"Пользователь {user_id} отписался, пропускаем.")
                continue

            reg_time_str = db.get_registration_time(user_id)
            preferred_time = db.get_preferred_time(user_id)
            print(f"Пользователь {user_id}: preferred_time = {preferred_time}, reg_time = {reg_time_str}")

            # Проверяем, совпадает ли текущее время с preferred_time
            current_minutes = current_time.hour * 60 + current_time.minute
            preferred_hours, preferred_minutes = map(int, preferred_time.split(":"))
            preferred_minutes_total = preferred_hours * 60 + preferred_minutes
            time_diff_minutes = abs(current_minutes - preferred_minutes_total)
            print(f"Разница времени для пользователя {user_id}: {time_diff_minutes} минут")
            if time_diff_minutes > 1:
                print(f"Время не совпадает: {current_time_str} != {preferred_time}")
                continue

            # Проверяем, сколько времени прошло с момента регистрации
            reg_time = datetime.strptime(reg_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone("Asia/Tashkent"))
            time_diff = current_time - reg_time
            print(f"Время с момента регистрации пользователя {user_id}: {time_diff}")

            # Если не прошло 24 часа с момента регистрации, пропускаем
            if time_diff < timedelta(days=1):
                print(f"Не прошло 24 часа с момента регистрации пользователя {user_id}")
                continue

            # Проверяем, отправляли ли видео сегодня
            last_sent_time = db.cursor.execute(
                "SELECT last_sent FROM users WHERE user_id=?", (user_id,)
            ).fetchone()
            if last_sent_time and last_sent_time[0]:
                last_sent = datetime.strptime(last_sent_time[0], "%Y-%m-%d").replace(tzinfo=pytz.timezone("Asia/Tashkent"))
                if last_sent.date() == current_time.date():
                    print(f"Видео уже отправлено пользователю {user_id} сегодня")
                    continue
            else:
                print(f"last_sent для пользователя {user_id} пустое")

            # Получаем текущий video_index из базы данных
            current_index = db.get_video_index(user_id)
            print(f"Текущий video_index для пользователя {user_id}: {current_index}")

            # Отправляем видео
            await send_video_to_user(user_id, current_index)

            # Обновляем дату последней отправки
            db.cursor.execute(
                "UPDATE users SET last_sent=? WHERE user_id=?",
                (current_time.strftime("%Y-%m-%d"), user_id)
            )
            db.conn.commit()
            print(f"Дата последней отправки обновлена для {user_id}: {current_time.strftime('%Y-%m-%d')}")

        except Exception as e:
            print(f"Ошибка при обработке пользователя {user_id}: {e}")

# Добавляем задачу в планировщик (проверка каждую минуту)
scheduler.add_job(check_and_send_videos, 'interval', minutes=1)