#!/usr/bin/env python3
"""
Скрипт для быстрого добавления пользователя в список одобренных
"""

import psycopg2
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройки подключения к БД
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'dbname': os.getenv('DB_NAME', 'centris_bot'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASS'),
    'port': os.getenv('DB_PORT', '5432')
}

def add_user_to_approved(user_id: int, name: str = "Не указано", phone: str = "Не указано"):
    """
    Добавить пользователя в список одобренных
    
    Args:
        user_id (int): ID пользователя Telegram
        name (str): Имя пользователя
        phone (str): Телефон пользователя
    """
    try:
        # Подключение к БД
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь
        cursor.execute("SELECT status FROM user_security WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        
        if result:
            current_status = result[0]
            if current_status == 'approved':
                print(f"✅ Пользователь {user_id} уже одобрен")
                return True
            
            # Обновляем статус
            cursor.execute("""
                UPDATE user_security 
                SET status = 'approved', approved_by = 5657091547, approved_date = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (user_id,))
            print(f"✅ Статус пользователя {user_id} изменен на 'approved'")
        else:
            # Добавляем нового пользователя
            cursor.execute("""
                INSERT INTO user_security (user_id, name, phone, status, approved_by, approved_date)
                VALUES (%s, %s, %s, 'approved', 5657091547, CURRENT_TIMESTAMP)
            """, (user_id, name, phone))
            print(f"✅ Пользователь {user_id} добавлен в список одобренных")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении пользователя: {e}")
        return False

def remove_user_from_approved(user_id: int):
    """
    Удалить пользователя из списка одобренных
    
    Args:
        user_id (int): ID пользователя Telegram
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE user_security 
            SET status = 'denied', approved_by = 5657091547, approved_date = CURRENT_TIMESTAMP
            WHERE user_id = %s
        """, (user_id,))
        
        if cursor.rowcount > 0:
            print(f"❌ Пользователь {user_id} удален из списка одобренных")
        else:
            print(f"⚠️ Пользователь {user_id} не найден")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при удалении пользователя: {e}")
        return False

def list_approved_users():
    """Показать всех одобренных пользователей"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, name, phone, status, reg_date 
            FROM user_security 
            WHERE status = 'approved'
            ORDER BY approved_date DESC
        """)
        
        users = cursor.fetchall()
        
        print("\n📋 **Одобренные пользователи:**")
        print("-" * 50)
        
        for user in users:
            user_id, name, phone, status, reg_date = user
            print(f"✅ {user_id} - {name} (📱 {phone}) - {reg_date}")
        
        print(f"\n📊 Всего одобренных: {len(users)}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при получении списка: {e}")

if __name__ == "__main__":
    print("🤖 Управление одобренными пользователями Centris Towers Bot")
    print("=" * 60)
    
    while True:
        print("\n📋 Выберите действие:")
        print("1. ✅ Добавить пользователя в одобренные")
        print("2. ❌ Удалить пользователя из одобренных") 
        print("3. 📊 Показать всех одобренных пользователей")
        print("4. 🚪 Выход")
        
        choice = input("\nВведите номер действия (1-4): ").strip()
        
        if choice == "1":
            try:
                user_id = int(input("🆔 Введите ID пользователя: ").strip())
                name = input("👤 Введите имя пользователя (или Enter для 'Не указано'): ").strip()
                phone = input("📱 Введите телефон (или Enter для 'Не указано'): ").strip()
                
                if not name:
                    name = "Не указано"
                if not phone:
                    phone = "Не указано"
                
                add_user_to_approved(user_id, name, phone)
                
            except ValueError:
                print("❌ Неверный формат ID. Введите число.")
                
        elif choice == "2":
            try:
                user_id = int(input("🆔 Введите ID пользователя для удаления: ").strip())
                remove_user_from_approved(user_id)
                
            except ValueError:
                print("❌ Неверный формат ID. Введите число.")
                
        elif choice == "3":
            list_approved_users()
            
        elif choice == "4":
            print("👋 До свидания!")
            break
            
        else:
            print("❌ Неверный выбор. Введите число от 1 до 4.") 