#!/usr/bin/env python3
"""
Временное отключение/включение системы безопасности
"""

import os
import re

def toggle_security(enable=True):
    """Включить/отключить систему безопасности"""
    
    # Путь к файлу middlewares/__init__.py
    middleware_init = "middlewares/__init__.py"
    
    try:
        with open(middleware_init, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if enable:
            # Включить систему безопасности
            new_content = content.replace("# dp.middleware.setup(VideoSecurityMiddleware())", "dp.middleware.setup(VideoSecurityMiddleware())")
            print("✅ Система безопасности ВКЛЮЧЕНА")
        else:
            # Отключить систему безопасности
            new_content = content.replace("dp.middleware.setup(VideoSecurityMiddleware())", "# dp.middleware.setup(VideoSecurityMiddleware())")
            print("❌ Система безопасности ОТКЛЮЧЕНА")
        
        with open(middleware_init, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print("🔄 Нужно перезапустить бота: python3 app.py")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    print("🛡️ Управление системой безопасности")
    print("=" * 40)
    
    if len(sys.argv) == 2:
        action = sys.argv[1].lower()
        if action == "off":
            toggle_security(False)
        elif action == "on":
            toggle_security(True)
        else:
            print("❌ Используйте: python3 disable_security_temp.py [on|off]")
    else:
        print("📋 Выберите действие:")
        print("1. ❌ Отключить систему безопасности")
        print("2. ✅ Включить систему безопасности")
        print("3. 🚪 Выход")
        
        choice = input("\nВыберите (1-3): ").strip()
        
        if choice == "1":
            toggle_security(False)
        elif choice == "2":
            toggle_security(True)
        elif choice == "3":
            print("👋 Выход")
        else:
            print("❌ Неверный выбор") 