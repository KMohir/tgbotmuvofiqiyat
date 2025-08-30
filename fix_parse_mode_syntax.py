#!/usr/bin/env python3
"""
Скрипт для исправления конкретных синтаксических ошибок с parse_mode
"""

import re
import os

def fix_parse_mode_syntax(filepath):
    """Исправляет синтаксические ошибки с parse_mode"""
    print(f"Исправляю parse_mode синтаксис в: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Исправляем ошибки типа: func("text")), parse_mode="Markdown"
    # Должно быть: func("text", parse_mode="Markdown")
    
    # Паттерн 1: ), parse_mode="Markdown" -> , parse_mode="Markdown")
    pattern1 = r'\),\s*parse_mode="Markdown"'
    replacement1 = r', parse_mode="Markdown")'
    
    matches1 = re.findall(pattern1, content)
    if matches1:
        print(f"  🔧 Исправляю {len(matches1)} ошибок типа '), parse_mode='")
        content = re.sub(pattern1, replacement1, content)
    
    # Паттерн 2: reply_markup=something(), parse_mode="Markdown" 
    # Должно быть: reply_markup=something(), parse_mode="Markdown")
    pattern2 = r'(reply_markup=[^,)]+\(\)),\s*parse_mode="Markdown"'
    replacement2 = r'\1, parse_mode="Markdown")'
    
    matches2 = re.findall(pattern2, content)
    if matches2:
        print(f"  🔧 Исправляю {len(matches2)} ошибок с reply_markup")
        content = re.sub(pattern2, replacement2, content)
    
    # Записываем исправленный контент
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    total_fixes = len(matches1) + len(matches2)
    print(f"  ✅ Исправлено {total_fixes} синтаксических ошибок")
    return total_fixes

def main():
    """Основная функция"""
    filepath = 'handlers/users/group_video_commands.py'
    
    print("🔧 ИСПРАВЛЕНИЕ PARSE_MODE СИНТАКСИСА\n")
    
    if os.path.exists(filepath):
        fixes = fix_parse_mode_syntax(filepath)
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
    else:
        print(f"❌ Файл {filepath} не найден")

if __name__ == "__main__":
    main()
