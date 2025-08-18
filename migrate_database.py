#!/usr/bin/env python3
"""
Скрипт для миграции базы данных
Обновляет структуру group_video_settings
"""

import psycopg2
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def connect_db():
    """Подключение к базе данных"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            dbname=os.getenv('DB_NAME', 'centris_bot'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASS'),
            port=os.getenv('DB_PORT', '5432')
        )
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return None

def backup_table():
    """Создать резервную копию таблицы"""
    conn = connect_db()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        print("💾 Создаю резервную копию...")
        
        # Создаем резервную таблицу
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_video_settings_backup AS 
            SELECT * FROM group_video_settings
        """)
        
        conn.commit()
        print("✅ Резервная копия создана: group_video_settings_backup")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при создании резервной копии: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def migrate_data():
    """Мигрировать данные в новую структуру"""
    conn = connect_db()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        print("🔄 Мигрирую данные...")
        
        # Получаем все существующие записи
        cursor.execute("SELECT * FROM group_video_settings")
        rows = cursor.fetchall()
        
        print(f"📊 Найдено {len(rows)} записей для миграции")
        
        migrated = 0
        for row in rows:
            chat_id, centris_enabled, centris_season, centris_start_season_id, centris_start_video, \
            golden_enabled, golden_start_season_id, golden_start_video, viewed_videos, is_subscribed = row
            
            # Определяем правильные season_id
            centris_season_id = centris_start_season_id if centris_start_season_id else None
            golden_season_id = golden_start_season_id if golden_start_season_id else None
            
            # Обновляем запись
            cursor.execute("""
                UPDATE group_video_settings 
                SET centris_season_id = %s, golden_season_id = %s
                WHERE chat_id = %s
            """, (centris_season_id, golden_season_id, chat_id))
            
            migrated += 1
            print(f"  ✅ Мигрирована группа {chat_id}")
        
        conn.commit()
        print(f"✅ Успешно мигрировано {migrated} групп!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def verify_migration():
    """Проверить результат миграции"""
    conn = connect_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        print("\n🔍 Проверяю результат миграции...")
        
        # Проверяем структуру таблицы
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'group_video_settings' 
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        print("📋 Структура таблицы после миграции:")
        for col_name, data_type in columns:
            print(f"  - {col_name}: {data_type}")
        
        # Проверяем данные
        cursor.execute("SELECT * FROM group_video_settings LIMIT 3")
        rows = cursor.fetchall()
        
        print(f"\n📊 Данные после миграции (первые 3):")
        for row in rows:
            print(f"  {row}")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
    finally:
        cursor.close()
        conn.close()

def main():
    print("🗄️ Миграция базы данных - обновление структуры group_video_settings")
    print("=" * 70)
    
    while True:
        print("\n📋 Выберите действие:")
        print("1. 💾 Создать резервную копию")
        print("2. 🔄 Мигрировать данные")
        print("3. 🔍 Проверить результат")
        print("4. 🚪 Выход")
        
        choice = input("\nВведите номер действия (1-4): ").strip()
        
        if choice == "1":
            if backup_table():
                print("✅ Резервная копия создана успешно!")
            else:
                print("❌ Ошибка при создании резервной копии")
                
        elif choice == "2":
            confirm = input("⚠️ Мигрировать данные? (yes/no): ").strip().lower()
            if confirm == "yes":
                if migrate_data():
                    print("✅ Миграция завершена успешно!")
                else:
                    print("❌ Ошибка при миграции")
            else:
                print("❌ Операция отменена")
                
        elif choice == "3":
            verify_migration()
            
        elif choice == "4":
            print("👋 До свидания!")
            break
            
        else:
            print("❌ Неверный выбор. Введите число от 1 до 4.")

if __name__ == "__main__":
    main()
