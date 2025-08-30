#!/usr/bin/env python3
"""
Скрипт для исправления всех синтаксических ошибок в parse_mode
"""

import re
import os

def fix_all_syntax_errors(filepath):
    """Исправляет все синтаксические ошибки в файле"""
    print(f"Исправляю все синтаксические ошибки в: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixes_count = 0
    
    # Паттерн 1: func(, parse_mode="Markdown") -> func(), parse_mode="Markdown"
    pattern1 = r'(\w+\(),\s*parse_mode="Markdown"'
    replacement1 = r'\1, parse_mode="Markdown"'
    matches1 = re.findall(pattern1, content)
    if matches1:
        print(f"  🔧 Исправляю {len(matches1)} ошибок типа 'func(, parse_mode'")
        content = re.sub(pattern1, replacement1, content)
        fixes_count += len(matches1)
    
    # Паттерн 2: func("text"), parse_mode="Markdown" -> func("text", parse_mode="Markdown")
    pattern2 = r'(\w+\([^)]*\)),\s*parse_mode="Markdown"'
    replacement2 = r'\1, parse_mode="Markdown"'
    matches2 = re.findall(pattern2, content)
    if matches2:
        print(f"  🔧 Исправляю {len(matches2)} ошибок типа 'func()), parse_mode'")
        content = re.sub(pattern2, replacement2, content)
        fixes_count += len(matches2)
    
    # Паттерн 3: reply_markup=func(, parse_mode="Markdown") -> reply_markup=func(), parse_mode="Markdown"
    pattern3 = r'(reply_markup=\w+\(),\s*parse_mode="Markdown"'
    replacement3 = r'\1, parse_mode="Markdown"'
    matches3 = re.findall(pattern3, content)
    if matches3:
        print(f"  🔧 Исправляю {len(matches3)} ошибок с reply_markup")
        content = re.sub(pattern3, replacement3, content)
        fixes_count += len(matches3)
    
    # Паттерн 4: parse_mode внутри строки
    pattern4 = r'(f"[^"]*), parse_mode="Markdown"([^"]*")'
    replacement4 = r'\1\2'
    matches4 = re.findall(pattern4, content)
    if matches4:
        print(f"  🔧 Исправляю {len(matches4)} ошибок с parse_mode в f-string")
        content = re.sub(pattern4, replacement4, content)
        fixes_count += len(matches4)
    
    # Записываем исправленный контент
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ Исправлено {fixes_count} синтаксических ошибок")
    return fixes_count

def main():
    """Основная функция"""
    filepath = 'handlers/users/group_video_commands.py'
    
    print("🔧 ИСПРАВЛЕНИЕ ВСЕХ СИНТАКСИЧЕСКИХ ОШИБОК\n")
    
    if os.path.exists(filepath):
        fixes = fix_all_syntax_errors(filepath)
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
