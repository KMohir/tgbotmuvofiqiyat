from aiogram import types
import asyncio
from db import db
from loader import dp, bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

# Список из 14 видео
VIDEO_LIST = [
    'video_2.mp4',
    'video_3.mp4',
    'video_4.mp4',
    'video_5.mp4',
    'video_6.mp4',
    'video_7.mp4',
    'video_8.mp4',
    'video_9.mp4',
    'video_10.mp4',
    'video_11.mp4',
    'video_12.mp4',
    'video_13.mp4',
    'video_14.mp4',
    'video_15.mp4'
]

# Список из 14 уникальных описаний для каждого видео
CAPTION_LIST = [
    "Тема: Введение в Centris Towers\n\nИбрагим Мамасаидов, основатель проекта\n\n<a href=\"https://youtu.be/Dg4H7JhGRFI\">Смотреть в 4K</a>\n\nCentris Towers - ваш новый бизнес-центр!\n\n📞 Для связи: <a href=\"tel:+998501554444\">+998501554444</a>\n\n<a href=\"https://t.me/centris1\">Связаться с менеджером</a>\n\n(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Адрес: г. Ташкент, ул. Нуронийлар, 2</a>)\n🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • 📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • ⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",
    "Тема: Лобби Centris Towers\n\nИбрагим Мамасаидов представляет\n\n<a href=\"https://youtu.be/Dg4H7JhGRFI\">Смотреть в 4K</a>\n\nСовременный стиль и комфорт\n\n📞 Для связи: <a href=\"tel:+998501554444\">+998501554444</a>\n\n<a href=\"https://t.me/centris1\">Связаться с менеджером</a>\n\n(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Адрес: г. Ташкент, ул. Нуронийлар, 2</a>)\n🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • 📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • ⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",
    "Тема: Офисные пространства\n\nИбрагим Мамасаидов рассказывает\n\n<a href=\"https://youtu.be/Dg4H7JhGRFI\">Смотреть в 4K</a>\n\nИдеальное место для вашего бизнеса\n\n📞 Для связи: <a href=\"tel:+998501554444\">+998501554444</a>\n\n<a href=\"https://t.me/centris1\">Связаться с менеджером</a>\n\n(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Адрес: г. Ташкент, ул. Нуронийлар, 2</a>)\n🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • 📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • ⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",
    "Тема: Инфраструктура Centris Towers\n\nИбрагим Мамасаидов делится\n\n<a href=\"https://youtu.be/Dg4H7JhGRFI\">Смотреть в 4K</a>\n\nВсе для вашего удобства\n\n📞 Для связи: <a href=\"tel:+998501554444\">+998501554444</a>\n\n<a href=\"https://t.me/centris1\">Связаться с менеджером</a>\n\n(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Адрес: г. Ташкент, ул. Нуронийлар, 2</a>)\n🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • 📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • ⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",
    "Тема: Конференц-залы\n\nИбрагим Мамасаидов показывает\n\n<a href=\"https://youtu.be/Dg4H7JhGRFI\">Смотреть в 4K</a>\n\nИдеально для встреч и мероприятий\n\n📞 Для связи: <a href=\"tel:+998501554444\">+998501554444</a>\n\n<a href=\"https://t.me/centris1\">Связаться с менеджером</a>\n\n(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Адрес: г. Ташкент, ул. Нуронийлар, 2</a>)\n🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • 📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • ⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",
    "Тема: Парковка Centris Towers\n\nИбрагим Мамасаидов объясняет\n\n<a href=\"https://youtu.be/Dg4H7JhGRFI\">Смотреть в 4K</a>\n\nУдобная и безопасная парковка\n\n📞 Для связи: <a href=\"tel:+998501554444\">+998501554444</a>\n\n<a href=\"https://t.me/centris1\">Связаться с менеджером</a>\n\n(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Адрес: г. Ташкент, ул. Нуронийлар, 2</a>)\n🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • 📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • ⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",
    "Тема: Зоны отдыха\n\nИбрагим Мамасаидов представляет\n\n<a href=\"https://youtu.be/Dg4H7JhGRFI\">Смотреть в 4K</a>\n\nМесто для релакса и общения\n\n📞 Для связи: <a href=\"tel:+998501554444\">+998501554444</a>\n\n<a href=\"https://t.me/centris1\">Связаться с менеджером</a>\n\n(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Адрес: г. Ташкент, ул. Нуронийлар, 2</a>)\n🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • 📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • ⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",
    "Тема: Безопасность Centris Towers\n\nИбрагим Мамасаидов рассказывает\n\n<a href=\"https://youtu.be/Dg4H7JhGRFI\">Смотреть в 4K</a>\n\nСовременные системы безопасности\n\n📞 Для связи: <a href=\"tel:+998501554444\">+998501554444</a>\n\n<a href=\"https://t.me/centris1\">Связаться с менеджером</a>\n\n(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Адрес: г. Ташкент, ул. Нуронийлар, 2</a>)\n🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • 📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • ⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",
    "Тема: Технологии Centris Towers\n\nИбрагим Мамасаидов делится\n\n<a href=\"https://youtu.be/Dg4H7JhGRFI\">Смотреть в 4K</a>\n\nИнновации для вашего бизнеса\n\n📞 Для связи: <a href=\"tel:+998501554444\">+998501554444</a>\n\n<a href=\"https://t.me/centris1\">Связаться с менеджером</a>\n\n(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Адрес: г. Ташкент, ул. Нуронийлар, 2</a>)\n🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • 📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • ⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",
    "Тема: Экологичность Centris Towers\n\nИбрагим Мамасаидов показывает\n\n<a href=\"https://youtu.be/Dg4H7JhGRFI\">Смотреть в 4K</a>\n\nЭкологичные решения для будущего\n\n📞 Для связи: <a href=\"tel:+998501554444\">+998501554444</a>\n\n<a href=\"https://t.me/centris1\">Связаться с менеджером</a>\n\n(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Адрес: г. Ташкент, ул. Нуронийлар, 2</a>)\n🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • 📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • ⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",
    "Тема: Рестораны и кафе\n\nИбрагим Мамасаидов объясняет\n\n<a href=\"https://youtu.be/Dg4H7JhGRFI\">Смотреть в 4K</a>\n\nВкусная еда прямо в здании\n\n📞 Для связи: <a href=\"tel:+998501554444\">+998501554444</a>\n\n<a href=\"https://t.me/centris1\">Связаться с менеджером</a>\n\n(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Адрес: г. Ташкент, ул. Нуронийлар, 2</a>)\n🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • 📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • ⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",
    "Тема: Фитнес-центр\n\nИбрагим Мамасаидов представляет\n\n<a href=\"https://youtu.be/Dg4H7JhGRFI\">Смотреть в 4K</a>\n\nПоддерживайте форму с нами\n\n📞 Для связи: <a href=\"tel:+998501554444\">+998501554444</a>\n\n<a href=\"https://t.me/centris1\">Связаться с менеджером</a>\n\n(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Адрес: г. Ташкент, ул. Нуронийлар, 2</a>)\n🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • 📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • ⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",
    "Тема: Дизайн интерьера\n\nИбрагим Мамасаидов рассказывает\n\n<a href=\"https://youtu.be/Dg4H7JhGRFI\">Смотреть в 4K</a>\n\nСтиль и элегантность в каждой детали\n\n📞 Для связи: <a href=\"tel:+998501554444\">+998501554444</a>\n\n<a href=\"https://t.me/centris1\">Связаться с менеджером</a>\n\n(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Адрес: г. Ташкент, ул. Нуронийлар, 2</a>)\n🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • 📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • ⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",
    "Тема: Транспортная доступность\n\nИбрагим Мамасаидов делится\n\n<a href=\"https://youtu.be/Dg4H7JhGRFI\">Смотреть в 4K</a>\n\nЛегко добраться из любой точки города\n\n📞 Для связи: <a href=\"tel:+998501554444\">+998501554444</a>\n\n<a href=\"https://t.me/centris1\">Связаться с менеджером</a>\n\n(<a href=\"https://yandex.ru/maps/org/110775045050\">📍Адрес: г. Ташкент, ул. Нуронийлар, 2</a>)\n🚀<a href=\"https://t.me/centris_towers\">Телеграм</a> • 📷<a href=\"https://www.instagram.com/centristowers_uz/\">Инстаграм</a> • ⏸<a href=\"https://www.youtube.com/@CentrisTowers\">You Tube</a>",
]

# Инициализация планировщика (без вызова start())
scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

# Функция для отправки видео всем пользователям
async def send_daily_video():
    current_index = db.get_video_index()
    video_path = VIDEO_LIST[current_index]
    caption = CAPTION_LIST[current_index]

    users = db.get_all_users()
    for user_id in users:
        try:
            with open(video_path, 'rb') as video:
                await bot.send_video(
                    chat_id=user_id,
                    video=video,
                    caption=caption,
                    parse_mode="HTML",
                    supports_streaming=True,
                    protect_content=True
                )
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Не удалось отправить видео пользователю {user_id}: {e}")
            continue

    next_index = (current_index + 1) % len(VIDEO_LIST)
    db.update_video_index(next_index)

# Добавляем задачу в планировщик после определения функции send_daily_video
scheduler.add_job(send_daily_video, 'cron', hour=2, minute=4)