#!/usr/bin/env python3
"""
Скрипт для очистки базы данных Telegram бота
ВНИМАНИЕ: Этот скрипт НАВСЕГДА удаляет данные!
"""

import psycopg2
import os
from environs import Env

# Загружаем переменные окружения
env = Env()
env.read_env()

DB_HOST = env.str("DB_HOST")
DB_NAME = env.str("DB_NAME") 
DB_USER = env.str("DB_USER")
DB_PASSWORD = env.str("DB_PASS")

def connect_db():
    """Подключение к базе данных"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return None

def clear_security_tables():
    """Очистить только таблицы безопасности"""
    conn = connect_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        print("🧹 Проверяю таблицы безопасности...")
        
        # Проверяем существование таблиц безопасности
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name IN ('user_security', 'group_whitelist') AND table_schema = 'public';")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        if not existing_tables:
            print("ℹ️  Таблицы безопасности не найдены (уже удалены или не создавались)")
            return
            
        for table in existing_tables:
            cursor.execute(f"DELETE FROM {table};")
            print(f"🗑️  Очищена таблица: {table}")
        
        conn.commit()
        print("✅ Таблицы безопасности очищены!")
        
    except Exception as e:
        print(f"❌ Ошибка очистки: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def clear_all_data():
    """Очистить все данные из всех таблиц"""
    conn = connect_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        print("💥 Получаю список всех таблиц...")
        
        # Получаем список всех существующих таблиц
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            print("ℹ️  Таблицы не найдены - база данных пуста")
            return
            
        print(f"📋 Найдено таблиц: {len(tables)}")
        
        # Очищаем каждую таблицу
        cleared_count = 0
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count_before = cursor.fetchone()[0]
                
                cursor.execute(f"DELETE FROM {table};")
                
                print(f"🗑️  {table}: удалено {count_before} записей")
                cleared_count += 1
            except Exception as table_error:
                print(f"⚠️  Ошибка очистки таблицы {table}: {table_error}")
        
        conn.commit()
        print(f"✅ Очищено таблиц: {cleared_count} из {len(tables)}")
        
    except Exception as e:
        print(f"❌ Ошибка очистки: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def drop_security_tables():
    """Удалить таблицы безопасности"""
    conn = connect_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        print("🔥 Удаляю таблицы безопасности...")
        cursor.execute("DROP TABLE IF EXISTS user_security CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS group_whitelist CASCADE;")
        
        conn.commit()
        print("✅ Таблицы безопасности удалены!")
        
    except Exception as e:
        print(f"❌ Ошибка удаления: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def drop_all_tables():
    """Удалить все таблицы"""
    conn = connect_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        print("💀 Получаю список всех таблиц для удаления...")
        
        # Получаем список всех существующих таблиц
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            print("ℹ️  Таблицы не найдены - база данных уже пуста")
            return
            
        print(f"📋 Найдено таблиц для удаления: {len(tables)}")
        for table in tables:
            print(f"   📊 {table}")
        
        # Удаляем каждую таблицу
        dropped_count = 0
        for table in tables:
            try:
                cursor.execute(f"DROP TABLE {table} CASCADE;")
                print(f"🔥 Удалена таблица: {table}")
                dropped_count += 1
            except Exception as table_error:
                print(f"⚠️  Ошибка удаления таблицы {table}: {table_error}")
        
        conn.commit()
        print(f"✅ Удалено таблиц: {dropped_count} из {len(tables)}")
        
    except Exception as e:
        print(f"❌ Ошибка удаления: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def show_menu():
    """Показать меню выбора"""
    print("\n" + "="*50)
    print("🗄️  МЕНЮ ОЧИСТКИ БАЗЫ ДАННЫХ")
    print("="*50)
    print("1. 🧹 Очистить только таблицы безопасности")
    print("2. 💥 Очистить ВСЕ данные (оставить таблицы)")
    print("3. 🔥 Удалить таблицы безопасности")
    print("4. 💀 Удалить ВСЕ таблицы")
    print("5. ❌ Выход")
    print("="*50)
    print("⚠️  ВНИМАНИЕ: Удаленные данные НЕ ВОССТАНАВЛИВАЮТСЯ!")
    print("="*50)

def main():
    """Главная функция"""
    while True:
        show_menu()
        choice = input("\n🔢 Выберите действие (1-5): ").strip()
        
        if choice == "1":
            confirm = input("❓ Очистить таблицы безопасности? (да/нет): ").lower()
            if confirm in ['да', 'yes', 'y']:
                clear_security_tables()
            else:
                print("❌ Отменено")
                
        elif choice == "2":
            confirm = input("❓ Очистить ВСЕ данные? (да/нет): ").lower()
            if confirm in ['да', 'yes', 'y']:
                clear_all_data()
            else:
                print("❌ Отменено")
                
        elif choice == "3":
            confirm = input("❓ Удалить таблицы безопасности? (да/нет): ").lower()
            if confirm in ['да', 'yes', 'y']:
                drop_security_tables()
            else:
                print("❌ Отменено")
                
        elif choice == "4":
            confirm = input("❓ Удалить ВСЕ таблицы? (ОПАСНО!) (да/нет): ").lower()
            if confirm in ['да', 'yes', 'y']:
                double_confirm = input("❓ Вы ТОЧНО уверены? Это удалит ВСЕ! (да/нет): ").lower()
                if double_confirm in ['да', 'yes', 'y']:
                    drop_all_tables()
                else:
                    print("❌ Отменено")
            else:
                print("❌ Отменено")
                
        elif choice == "5":
            print("👋 До свидания!")
            break
            
        else:
            print("❌ Неверный выбор! Введите цифру от 1 до 5")

if __name__ == "__main__":
    print("🗄️ Скрипт очистки базы данных запущен")
    print(f"📋 База: {DB_NAME} на {DB_HOST}")
    
    # Проверяем подключение
    test_conn = connect_db()
    if test_conn:
        test_conn.close()
        print("✅ Подключение к базе данных успешно")
        main()
    else:
        print("❌ Не удалось подключиться к базе данных")
        print("🔧 Проверьте настройки в .env файле") 