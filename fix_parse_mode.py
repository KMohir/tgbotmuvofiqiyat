#!/usr/bin/env python3
"""
Скрипт для автоматического добавления parse_mode="Markdown" 
к сообщениям с форматированием ** в Telegram боте
"""

import re
import os

def fix_parse_mode_in_file(filepath):
    """Исправляет parse_mode в указанном файле"""
    print(f"Обрабатываю файл: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Регулярное выражение для поиска message.answer с ** форматированием без parse_mode
    pattern = r'(await\s+message\.answer\([^)]*\*\*[^)]*\))(?!\s*,\s*parse_mode)'
    
    # Подсчитываем количество совпадений
    matches = re.findall(pattern, content)
    if not matches:
        print(f"  ✅ В файле {filepath} не найдено сообщений без parse_mode")
        return 0
    
    print(f"  🔍 Найдено {len(matches)} сообщений без parse_mode")
    
    # Заменяем каждое совпадение
    def replace_func(match):
        original = match.group(1)
        # Проверяем, есть ли уже parse_mode
        if 'parse_mode' in original:
            return original
        
        # Добавляем parse_mode="Markdown" перед закрывающей скобкой
        if original.endswith(')'):
            return original[:-1] + ', parse_mode="Markdown")'
        else:
            return original + ', parse_mode="Markdown"'
    
    # Применяем замены
    new_content = re.sub(pattern, replace_func, content)
    
    # Также исправляем другие варианты
    patterns = [
        # message.reply с ** форматированием
        (r'(await\s+message\.reply\([^)]*\*\*[^)]*\))(?!\s*,\s*parse_mode)', r'\1, parse_mode="Markdown"'),
        # callback_query.message.answer с ** форматированием
        (r'(await\s+callback_query\.message\.answer\([^)]*\*\*[^)]*\))(?!\s*,\s*parse_mode)', r'\1, parse_mode="Markdown"'),
        # callback_query.message.edit_text с ** форматированием
        (r'(await\s+callback_query\.message\.edit_text\([^)]*\*\*[^)]*\))(?!\s*,\s*parse_mode)', r'\1, parse_mode="Markdown"'),
    ]
    
    total_fixes = 0
    for pattern, replacement in patterns:
        matches = re.findall(pattern, new_content)
        if matches:
            print(f"  🔧 Исправляю {len(matches)} дополнительных совпадений")
            new_content = re.sub(pattern, replacement, new_content)
            total_fixes += len(matches)
    
    # Записываем обновленный контент
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"  ✅ Исправлено {len(matches) + total_fixes} сообщений в {filepath}")
    return len(matches) + total_fixes

def main():
    """Основная функция"""
    files_to_fix = [
        'handlers/users/group_video_commands.py',
        'handlers/users/user_commands.py', 
        'handlers/users/video_selector.py',
        'handlers/users/help.py',
        'handlers/users/support_call.py',
        'handlers/users/security.py',
        'handlers/users/admin_security.py',
        'handlers/groups/group_handler.py',
    ]
    
    total_fixes = 0
    
    print("🔧 ИСПРАВЛЕНИЕ PARSE_MODE В TELEGRAM БОТЕ\n")
    
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            fixes = fix_parse_mode_in_file(filepath)
            total_fixes += fixes
        else:
            print(f"  ⚠️  Файл {filepath} не найден")
    
    print(f"\n✅ ЗАВЕРШЕНО! Всего исправлено {total_fixes} сообщений")
    print("\nТеперь все сообщения с ** форматированием будут корректно отображаться в Telegram!")

if __name__ == "__main__":
    main()
