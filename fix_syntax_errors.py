#!/usr/bin/env python3
"""
Скрипт для исправления синтаксических ошибок в parse_mode
"""

import re
import os

def fix_syntax_errors_in_file(filepath):
    """Исправляет синтаксические ошибки в файле"""
    print(f"Исправляю синтаксические ошибки в: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Исправляем ошибки типа: func("text")), parse_mode="Markdown"
    # Должно быть: func("text", parse_mode="Markdown")
    patterns = [
        # Исправляем закрывающую скобку перед запятой
        (r'(\w+\([^)]*\))\),\s*parse_mode="Markdown"', r'\1, parse_mode="Markdown")'),
        
        # Исправляем двойные скобки
        (r'(\w+\([^)]*\))\)\),\s*parse_mode="Markdown"', r'\1, parse_mode="Markdown")'),
        
        # Исправляем случаи где parse_mode попал внутрь строки
        (r'(f"[^"]*), parse_mode="Markdown"([^"]*")', r'\1\2'),
        
        # Исправляем случаи где parse_mode в f-string
        (r'datetime\.now\(\),\s*parse_mode="Markdown"\.strftime', r'datetime.now().strftime'),
    ]
    
    fixes_count = 0
    for pattern, replacement in patterns:
        matches = re.findall(pattern, content)
        if matches:
            print(f"  🔧 Исправляю {len(matches)} ошибок типа: {pattern[:50]}...")
            content = re.sub(pattern, replacement, content)
            fixes_count += len(matches)
    
    # Записываем исправленный контент
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ Исправлено {fixes_count} синтаксических ошибок в {filepath}")
    return fixes_count

def main():
    """Основная функция"""
    files_to_fix = [
        'handlers/users/group_video_commands.py',
        'handlers/users/security.py',
        'handlers/users/user_commands.py',
        'handlers/groups/group_handler.py',
    ]
    
    total_fixes = 0
    
    print("🔧 ИСПРАВЛЕНИЕ СИНТАКСИЧЕСКИХ ОШИБОК\n")
    
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            fixes = fix_syntax_errors_in_file(filepath)
            total_fixes += fixes
        else:
            print(f"  ⚠️  Файл {filepath} не найден")
    
    print(f"\n✅ ЗАВЕРШЕНО! Всего исправлено {total_fixes} синтаксических ошибок")

if __name__ == "__main__":
    main()
