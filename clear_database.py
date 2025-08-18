#!/usr/bin/env python3
"""
Скрипт для очистки базы данных
ВНИМАНИЕ: Используйте осторожно!
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

def show_current_data():
    """Показать текущие данные"""
    conn = connect_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        # Группы в users
        cursor.execute("SELECT user_id, name FROM users WHERE is_group = 1")
        groups = cursor.fetchall()
        print(f"\n📋 Групп в users: {len(groups)}")
        for group_id, name in groups:
            print(f"  - {group_id}: {name}")
        
        # Группы в whitelist
        cursor.execute("SELECT chat_id, title FROM group_whitelist")
        whitelist = cursor.fetchall()
        print(f"\n✅ Групп в whitelist: {len(whitelist)}")
        for chat_id, title in whitelist:
            print(f"  - {chat_id}: {title}")
        
        # Пользователи в security
        cursor.execute("SELECT user_id, name FROM user_security")
        users = cursor.fetchall()
        print(f"\n👥 Пользователей в security: {len(users)}")
        for user_id, name in users:
            print(f"  - {user_id}: {name}")
            
    except Exception as e:
        print(f"❌ Ошибка при получении данных: {e}")
    finally:
        cursor.close()
        conn.close()

def clear_all_groups():
    """Очистить все группы"""
    conn = connect_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        print("\n🗑️ Очищаю все группы...")
        
        # Удаляем из group_video_settings
        cursor.execute("DELETE FROM group_video_settings")
        print(f"  - Удалено настроек групп: {cursor.rowcount}")
        
        # Удаляем из group_whitelist
        cursor.execute("DELETE FROM group_whitelist")
        print(f"  - Удалено из whitelist: {cursor.rowcount}")
        
        # Удаляем из users
        cursor.execute("DELETE FROM users WHERE is_group = 1")
        print(f"  - Удалено групп из users: {cursor.rowcount}")
        
        conn.commit()
        print("✅ Все группы успешно удалены!")
        
    except Exception as e:
        print(f"❌ Ошибка при очистке: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def clear_specific_group(group_id):
    """Очистить конкретную группу"""
    conn = connect_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        print(f"\n🗑️ Очищаю группу {group_id}...")
        
        # Удаляем настройки
        cursor.execute("DELETE FROM group_video_settings WHERE chat_id = %s", (str(group_id),))
        print(f"  - Удалено настроек: {cursor.rowcount}")
        
        # Удаляем из whitelist
        cursor.execute("DELETE FROM group_whitelist WHERE chat_id = %s", (group_id,))
        print(f"  - Удалено из whitelist: {cursor.rowcount}")
        
        # Удаляем из users
        cursor.execute("DELETE FROM users WHERE user_id = %s AND is_group = 1", (group_id,))
        print(f"  - Удалено из users: {cursor.rowcount}")
        
        conn.commit()
        print(f"✅ Группа {group_id} успешно удалена!")
        
    except Exception as e:
        print(f"❌ Ошибка при удалении группы: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def clear_all_users():
    """Очистить всех пользователей"""
    conn = connect_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        print("\n🗑️ Очищаю всех пользователей...")
        
        # Удаляем из user_security
        cursor.execute("DELETE FROM user_security")
        print(f"  - Удалено пользователей из security: {cursor.rowcount}")
        
        # Удаляем обычных пользователей (не группы) из users
        cursor.execute("DELETE FROM users WHERE is_group = 0")
        print(f"  - Удалено пользователей из users: {cursor.rowcount}")
        
        conn.commit()
        print("✅ Все пользователи успешно удалены!")
        
    except Exception as e:
        print(f"❌ Ошибка при очистке: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def main():
    print("🗄️ Скрипт очистки базы данных")
    print("=" * 50)
    
    while True:
        print("\n📋 Выберите действие:")
        print("1. 👀 Показать текущие данные")
        print("2. 🗑️ Очистить все группы")
        print("3. 🗑️ Очистить конкретную группу")
        print("4. 🗑️ Очистить всех пользователей")
        print("5. 🗑️ Очистить ВСЕ данные (ОПАСНО!)")
        print("6. 🚪 Выход")
        
        choice = input("\nВведите номер действия (1-6): ").strip()
        
        if choice == "1":
            show_current_data()
            
        elif choice == "2":
            confirm = input("⚠️ Вы уверены, что хотите удалить ВСЕ группы? (yes/no): ").strip().lower()
            if confirm == "yes":
                clear_all_groups()
            else:
                print("❌ Операция отменена")
                
        elif choice == "3":
            try:
                group_id = int(input("🆔 Введите ID группы: ").strip())
                clear_specific_group(group_id)
            except ValueError:
                print("❌ Неверный ID группы")
                
        elif choice == "4":
            confirm = input("⚠️ Вы уверены, что хотите удалить ВСЕХ пользователей? (yes/no): ").strip().lower()
            if confirm == "yes":
                clear_all_users()
            else:
                print("❌ Операция отменена")
                
        elif choice == "5":
            confirm = input("🚨 ВНИМАНИЕ! Это удалит ВСЕ данные! Вы уверены? (YES/NO): ").strip()
            if confirm == "YES":
                clear_all_groups()
                clear_all_users()
                print("🚨 ВСЕ данные удалены!")
            else:
                print("❌ Операция отменена")
                
        elif choice == "6":
            print("👋 До свидания!")
            break
            
        else:
            print("❌ Неверный выбор. Введите число от 1 до 6.")

if __name__ == "__main__":
    main() 