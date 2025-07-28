#!/usr/bin/env python3
"""
Быстрый скрипт для одобрения пользователя
Использование: python quick_approve_user.py USER_ID
"""

import sys
import psycopg2
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def quick_approve_user(user_id: int):
    """Быстро одобрить пользователя"""
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
        
        # Проверяем, существует ли пользователь
        cursor.execute("SELECT status FROM user_security WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        
        if result:
            current_status = result[0]
            if current_status == 'approved':
                print(f"✅ Пользователь {user_id} уже одобрен!")
                return True
            
            # Обновляем статус
            cursor.execute("""
                UPDATE user_security 
                SET status = 'approved', approved_by = 5657091547, approved_date = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (user_id,))
            print(f"✅ Пользователь {user_id} одобрен!")
        else:
            # Добавляем нового пользователя как одобренного
            cursor.execute("""
                INSERT INTO user_security (user_id, name, phone, status, approved_by, approved_date)
                VALUES (%s, 'Не указано', 'Не указано', 'approved', 5657091547, CURRENT_TIMESTAMP)
            """, (user_id,))
            print(f"✅ Пользователь {user_id} добавлен и одобрен!")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("📝 Использование: python quick_approve_user.py USER_ID")
        print("📝 Пример: python quick_approve_user.py 123456789")
        sys.exit(1)
    
    try:
        user_id = int(sys.argv[1])
        print(f"🔄 Одобряю пользователя {user_id}...")
        quick_approve_user(user_id)
    except ValueError:
        print("❌ USER_ID должен быть числом!")
        sys.exit(1) 