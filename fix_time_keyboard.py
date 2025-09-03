#!/usr/bin/env python3
"""
Скрипт для исправления конкретных ошибок с get_time_selection_keyboard
"""

import re

def fix_time_keyboard_errors(filepath):
    """Исправляет ошибки с get_time_selection_keyboard"""
    print(f"Исправляю ошибки с get_time_selection_keyboard в: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Исправляем: reply_markup=get_time_selection_keyboard(, parse_mode="Markdown")
    # На: reply_markup=get_time_selection_keyboard(), parse_mode="Markdown"
    pattern = r'reply_markup=get_time_selection_keyboard\(,\s*parse_mode="Markdown"\)'
    replacement = r'reply_markup=get_time_selection_keyboard(),\n            parse_mode="Markdown"'
    
    matches = re.findall(pattern, content)
    if matches:
        print(f"  🔧 Исправляю {len(matches)} ошибок с get_time_selection_keyboard")
        content = re.sub(pattern, replacement, content)
    
    # Записываем исправленный контент
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ Исправлено {len(matches)} ошибок")
    return len(matches)

def main():
    """Основная функция"""
    filepath = 'handlers/users/group_video_commands.py'
    
    print("🔧 ИСПРАВЛЕНИЕ ОШИБОК С TIME KEYBOARD\n")
    
    fixes = fix_time_keyboard_errors(filepath)
    print(f"\n✅ ЗАВЕРШЕНО! Исправлено {fixes} ошибок")
    
    # Проверяем компиляцию
    print("\n🔍 Проверяю компиляцию...")
    import subprocess
    result = subprocess.run(['python', '-m', 'py_compile', filepath], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Файл компилируется без ошибок!")
    else:
        print("❌ Все еще есть синтаксические ошибки:")
        print(result.stderr)

if __name__ == "__main__":
    main()
