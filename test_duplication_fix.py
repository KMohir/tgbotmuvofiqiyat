#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправлений дублирования регистрации
"""

import os
import sys
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from db import db
    
    def test_user_duplication():
        """Тестируем предотвращение дублирования пользователей"""
        print("🧪 Тестирование предотвращения дублирования пользователей...")
        
        # Тестовый пользователь
        test_user_id = 999999999
        test_name = "Test User"
        test_phone = "+998991234567"
        
        print(f"📝 Тестовый пользователь: ID={test_user_id}, Name={test_name}, Phone={test_phone}")
        
        # Проверяем, существует ли пользователь
        print("\n🔍 Проверка существования пользователя...")
        exists_before = db.user_exists(test_user_id)
        print(f"   Существовал до теста: {'✅ Да' if exists_before else '❌ Нет'}")
        
        # Первая попытка добавления
        print("\n1️⃣ Первая попытка добавления...")
        result1 = db.add_user(test_user_id, test_name, test_phone)
        print(f"   Результат: {'✅ Успешно' if result1 else '❌ Ошибка'}")
        
        # Проверяем существование после первого добавления
        exists_after1 = db.user_exists(test_user_id)
        print(f"   Существует после первого добавления: {'✅ Да' if exists_after1 else '❌ Нет'}")
        
        # Вторая попытка добавления (должна быть отклонена)
        print("\n2️⃣ Вторая попытка добавления...")
        result2 = db.add_user(test_user_id, test_name, test_phone)
        print(f"   Результат: {'✅ Успешно' if result2 else '❌ Ошибка (ожидаемо)'}")
        
        # Проверяем существование после второго добавления
        exists_after2 = db.user_exists(test_user_id)
        print(f"   Существует после второго добавления: {'✅ Да' if exists_after2 else '❌ Нет'}")
        
        # Проверяем данные пользователя
        print("\n📊 Данные пользователя:")
        name = db.get_name(test_user_id)
        phone = db.get_phone(test_user_id)
        reg_time = db.get_registration_time(test_user_id)
        
        print(f"   Имя: {name}")
        print(f"   Телефон: {phone}")
        print(f"   Время регистрации: {reg_time}")
        
        # Очищаем тестовые данные
        print("\n🧹 Очистка тестовых данных...")
        try:
            cursor = db.conn.cursor()
            cursor.execute("DELETE FROM users WHERE user_id = %s", (test_user_id,))
            db.conn.commit()
            print("   ✅ Тестовые данные удалены")
        except Exception as e:
            print(f"   ❌ Ошибка при удалении: {e}")
        
        print("\n🎯 Тест завершен!")
        
        if result1 and not result2 and exists_after1 and exists_after2:
            print("✅ Тест ПРОЙДЕН: Дублирование предотвращено")
        else:
            print("❌ Тест НЕ ПРОЙДЕН: Есть проблемы с логикой")
    
    def test_existing_users():
        """Проверяем существующих пользователей"""
        print("\n👥 Проверка существующих пользователей...")
        
        try:
            cursor = db.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            total = cursor.fetchone()[0]
            print(f"   Всего пользователей: {total}")
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_subscribed = 1")
            subscribed = cursor.fetchone()[0]
            print(f"   Подписанных: {subscribed}")
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
            banned = cursor.fetchone()[0]
            print(f"   Заблокированных: {banned}")
            
        except Exception as e:
            print(f"   ❌ Ошибка при проверке: {e}")
    
    if __name__ == "__main__":
        print("🚀 Запуск тестирования исправлений дублирования регистрации")
        print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        test_user_duplication()
        test_existing_users()
        
        print("\n" + "=" * 60)
        print("🏁 Тестирование завершено")

except Exception as e:
    print(f"❌ Ошибка при запуске теста: {e}")
    print("Убедитесь, что база данных доступна и все зависимости установлены")
