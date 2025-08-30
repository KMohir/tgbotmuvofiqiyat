#!/usr/bin/env python3
"""
Скрипт для исправления ошибок с parse_mode в keyboard функциях
"""

import re

def fix_keyboard_parse_mode_errors(filepath):
    """Исправляет ошибки с parse_mode в keyboard функциях"""
    print(f"Исправляю ошибки с parse_mode в keyboard функциях: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixes_count = 0
    
    # Паттерн 1: Убираем parse_mode из keyboard функций
    keyboard_patterns = [
        # get_project_keyboard(), parse_mode="Markdown" -> get_project_keyboard()
        (r'reply_markup=get_project_keyboard\(\),\s*parse_mode="Markdown"', r'reply_markup=get_project_keyboard()'),
        
        # get_time_selection_keyboard(), parse_mode="Markdown" -> get_time_selection_keyboard()
        (r'reply_markup=get_time_selection_keyboard\(\),\s*parse_mode="Markdown"', r'reply_markup=get_time_selection_keyboard()'),
        
        # get_group_selection_keyboard(, parse_mode="Markdown") -> get_group_selection_keyboard()
        (r'reply_markup=get_group_selection_keyboard\(,\s*parse_mode="Markdown"\)', r'reply_markup=get_group_selection_keyboard()'),
        
        # get_season_keyboard("centris", parse_mode="Markdown") -> get_season_keyboard("centris")
        (r'get_season_keyboard\("centris",\s*parse_mode="Markdown"\)', r'get_season_keyboard("centris")'),
        (r'get_season_keyboard\("golden",\s*parse_mode="Markdown"\)', r'get_season_keyboard("golden")'),
        
        # get_video_keyboard_from_db(..., parse_mode="Markdown") -> get_video_keyboard_from_db(...)
        (r'get_video_keyboard_from_db\([^)]+\),\s*parse_mode="Markdown"\)', r'get_video_keyboard_from_db(db.get_videos_by_season(season_id), [])'),
    ]
    
    for pattern, replacement in keyboard_patterns:
        matches = re.findall(pattern, content)
        if matches:
            print(f"  🔧 Исправляю {len(matches)} ошибок с паттерном: {pattern[:50]}...")
            content = re.sub(pattern, replacement, content)
            fixes_count += len(matches)
    
    # Записываем исправленный контент
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ Исправлено {fixes_count} ошибок с keyboard функциями")
    return fixes_count

def main():
    """Основная функция"""
    filepath = 'handlers/users/group_video_commands.py'
    
    print("🔧 ИСПРАВЛЕНИЕ ОШИБОК С KEYBOARD ФУНКЦИЯМИ\n")
    
    fixes = fix_keyboard_parse_mode_errors(filepath)
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
