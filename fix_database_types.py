#!/usr/bin/env python3
"""
Скрипт для исправления типов данных в SQL запросах
Исправляет проблему: operator does not exist: text = bigint
"""

import re
import os

def fix_db_types():
    """Исправить типы данных в db.py"""
    
    db_file = "db.py"
    
    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Создаем бэкап
        backup_file = f"{db_file}.backup"
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Создан бэкап: {backup_file}")
        
        # Список исправлений
        fixes = [
            # Исправляем передачу chat_id в SQL запросы для таблицы group_video_settings
            (r'(\(.*?), (chat_id)\)', r'\1, str(\2))'),
            (r'(\(.*?), (chat_id), (.*?)\)', r'\1, str(\2), \3)'),
            (r'(\([^)]*), (chat_id)(\))', r'\1, str(\2)\3'),
            
            # Специфические исправления для конкретных методов
            (r'cursor\.execute\([\'"]([^"\']*WHERE chat_id = %s)[\'"], \((.*?chat_id.*?)\)\)', 
             r'cursor.execute("\1", (\2,))' if 'str(' not in r'\2' else r'cursor.execute("\1", (\2))'),
        ]
        
        new_content = content
        
        # Ручные исправления для каждой проблемной строки
        replacements = [
            # Строка 242
            ('FROM group_video_settings WHERE chat_id = %s", (chat_id,)', 
             'FROM group_video_settings WHERE chat_id = %s", (str(chat_id),)'),
            
            # Строки с UPDATE и SELECT для group_video_settings
            ('WHERE chat_id = %s",\n                    (json.dumps(viewed_videos), chat_id)', 
             'WHERE chat_id = %s",\n                    (json.dumps(viewed_videos), str(chat_id))'),
            
            ('WHERE chat_id = %s", (chat_id,)', 'WHERE chat_id = %s", (str(chat_id),)'),
            ('WHERE chat_id = %s", (chat_id)', 'WHERE chat_id = %s", (str(chat_id))'),
            ('WHERE chat_id = %s\', (chat_id,)', 'WHERE chat_id = %s\', (str(chat_id),)'),
            ('WHERE chat_id = %s\', (chat_id)', 'WHERE chat_id = %s\', (str(chat_id))'),
            
            # Для методов с несколькими параметрами
            (', chat_id)', ', str(chat_id))'),
            (', chat_id,)', ', str(chat_id),)'),
        ]
        
        for old, new in replacements:
            new_content = new_content.replace(old, new)
        
        # Проверяем что изменения были сделаны
        if new_content != content:
            with open(db_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Файл {db_file} обновлен")
            print("📋 Основные изменения:")
            print("   - Все chat_id в SQL запросах теперь приводятся к str()")
            print("   - Исправлена проблема 'operator does not exist: text = bigint'")
            return True
        else:
            print("⚠️ Изменения не потребовались")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def restore_backup():
    """Восстановить из бэкапа"""
    backup_file = "db.py.backup"
    db_file = "db.py"
    
    try:
        if os.path.exists(backup_file):
            with open(backup_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            with open(db_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Восстановлено из {backup_file}")
            return True
        else:
            print("❌ Файл бэкапа не найден")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при восстановлении: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Исправление типов данных в db.py")
    print("=" * 40)
    
    print("📋 Выберите действие:")
    print("1. 🔧 Исправить типы данных")
    print("2. 🔄 Восстановить из бэкапа")
    print("3. 🚪 Выход")
    
    choice = input("\nВыберите (1-3): ").strip()
    
    if choice == "1":
        if fix_db_types():
            print("\n🎉 Исправления применены!")
            print("🔄 Перезапустите бота для применения изменений")
        else:
            print("❌ Ошибка при исправлении")
            
    elif choice == "2":
        if restore_backup():
            print("🔄 Перезапустите бота для применения изменений")
        else:
            print("❌ Ошибка при восстановлении")
            
    elif choice == "3":
        print("👋 Выход")
        
    else:
        print("❌ Неверный выбор") 