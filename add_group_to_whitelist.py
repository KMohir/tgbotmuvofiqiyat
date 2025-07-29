#!/usr/bin/env python3
"""
Скрипт для добавления групп в whitelist
"""

import psycopg2
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def add_group_to_whitelist(chat_id: int, title: str = "Migrated Group"):
    """Добавить группу в whitelist"""
    try:
        # Подключение к БД
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            dbname=os.getenv('DB_NAME', 'centris_bot'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASS'),
            port=os.getenv('DB_PORT', '5432')
        )
        cursor = conn.cursor()
        
        # Проверяем, существует ли группа
        cursor.execute("SELECT status FROM group_whitelist WHERE chat_id = %s", (chat_id,))
        result = cursor.fetchone()
        
        if result:
            if result[0] == 'active':
                print(f"✅ Группа {chat_id} уже в whitelist")
                return True
            else:
                # Активируем группу
                cursor.execute("""
                    UPDATE group_whitelist 
                    SET status = 'active', added_date = CURRENT_TIMESTAMP
                    WHERE chat_id = %s
                """, (chat_id,))
                print(f"✅ Группа {chat_id} активирована в whitelist")
        else:
            # Добавляем новую группу
            cursor.execute("""
                INSERT INTO group_whitelist (chat_id, title, status, added_by)
                VALUES (%s, %s, 'active', 5657091547)
            """, (chat_id, title))
            print(f"✅ Группа {chat_id} добавлена в whitelist")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении группы: {e}")
        return False

def list_whitelist_groups():
    """Показать все группы в whitelist"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            dbname=os.getenv('DB_NAME', 'centris_bot'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASS'),
            port=os.getenv('DB_PORT', '5432')
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT chat_id, title, status, added_date 
            FROM group_whitelist 
            ORDER BY added_date DESC
        """)
        
        groups = cursor.fetchall()
        
        print("\n📋 **Группы в whitelist:**")
        print("-" * 50)
        
        for group in groups:
            chat_id, title, status, added_date = group
            status_icon = "✅" if status == 'active' else "❌"
            print(f"{status_icon} {chat_id} - {title} ({added_date})")
        
        print(f"\n📊 Всего групп: {len(groups)}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при получении списка: {e}")

# Известные группы из документации
KNOWN_GROUPS = [
    (-1002847321892, "Migrated Group"),
    (-1002223935003, "Migrated Group"),
    (-4911418128, "Migrated Group"),
]

if __name__ == "__main__":
    print("🏢 Управление whitelist групп")
    print("=" * 50)
    
    while True:
        print("\n📋 Выберите действие:")
        print("1. ✅ Добавить группу в whitelist")
        print("2. 📊 Показать все группы")
        print("3. 🔄 Добавить все известные группы")
        print("4. 🚪 Выход")
        
        choice = input("\nВведите номер действия (1-4): ").strip()
        
        if choice == "1":
            try:
                chat_id = int(input("🆔 Введите ID группы: ").strip())
                title = input("📝 Введите название группы (или Enter для 'Migrated Group'): ").strip()
                
                if not title:
                    title = "Migrated Group"
                
                add_group_to_whitelist(chat_id, title)
                
            except ValueError:
                print("❌ Неверный формат ID. Введите число.")
                
        elif choice == "2":
            list_whitelist_groups()
            
        elif choice == "3":
            print("\n🔄 Добавляю известные группы...")
            for chat_id, title in KNOWN_GROUPS:
                add_group_to_whitelist(chat_id, title)
            print("\n✅ Готово!")
            
        elif choice == "4":
            print("👋 До свидания!")
            break
            
        else:
            print("❌ Неверный выбор. Введите число от 1 до 4.") 