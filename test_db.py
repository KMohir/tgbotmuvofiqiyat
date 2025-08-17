#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки работы базы данных
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

print("🔍 Тестирование подключения к базе данных...")
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_PORT: {os.getenv('DB_PORT')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_PASS: {'*' * len(os.getenv('DB_PASS', ''))}")

try:
    from db import db
    print("✅ Модуль db импортирован успешно")
    
    # Проверяем подключение
    print("🔍 Проверяем подключение к базе данных...")
    
    # Пробуем получить сезоны
    print("📋 Получаем сезоны Centris...")
    centris_seasons = db.get_seasons_by_project("centris")
    print(f"Найдено сезонов Centris: {len(centris_seasons)}")
    for season_id, name in centris_seasons:
        print(f"  - ID {season_id}: {name}")
    
    print("📋 Получаем сезоны Golden...")
    golden_seasons = db.get_seasons_by_project("golden")
    print(f"Найдено сезонов Golden: {len(golden_seasons)}")
    
    # Пробуем добавить тестовый сезон
    print("\n🧪 Тестируем добавление сезона...")
    test_links = ["https://test1.com", "https://test2.com"]
    test_titles = ["Тест видео 1", "Тест видео 2"]
    
    result = db.add_season_with_videos("centris", "Тестовый сезон из Python", test_links, test_titles)
    
    if result:
        print(f"✅ Сезон добавлен успешно!")
        print(f"  - ID: {result['season_id']}")
        print(f"  - Проект: {result['project']}")
        print(f"  - Название: {result['season_name']}")
        print(f"  - Количество видео: {result['video_count']}")
    else:
        print("❌ Ошибка при добавлении сезона")
    
    # Проверяем, что сезон добавился
    print("\n📋 Проверяем обновленный список сезонов...")
    updated_seasons = db.get_seasons_by_project("centris")
    print(f"Всего сезонов Centris: {len(updated_seasons)}")
    for season_id, name in updated_seasons:
        print(f"  - ID {season_id}: {name}")
    
    print("\n✅ Тест завершен успешно!")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
except Exception as e:
    print(f"❌ Общая ошибка: {e}")
    import traceback
    traceback.print_exc()
