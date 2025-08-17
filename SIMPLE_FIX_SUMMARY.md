# 🔧 УПРОЩЕНИЕ КОДА ДЛЯ CENTRIS TOWERS

## 🎯 Проблема
Код для Centris Towers был сложнее, чем для Golden Lake, что приводило к разному поведению.

## ✅ Решение
Упростил код для Centris Towers, сделав его точно таким же, как для Golden Lake.

### 🔄 Что изменено:

1. **Функция `centris_towers_menu`** - упрощена, убрана сложная логика проверки
2. **Функция `golden_lake_menu`** - также упрощена для единообразия
3. **Функция `get_season_keyboard`** - убрано сложное кэширование, всегда получает свежие данные из БД
4. **Функция `clear_season_keyboard_cache`** - упрощена

### 📝 Новый простой код:

```python
# Centris Towers - упрощенная версия
async def centris_towers_menu(message: types.Message, state: FSMContext):
    await state.update_data(project="centris")
    
    # Простая очистка кэша
    clear_season_keyboard_cache("centris")
    
    # Получаем клавиатуру
    season_keyboard = get_season_keyboard("centris")
    
    await message.answer("Sezonni tanlang:", reply_markup=season_keyboard)
    await message.answer("Qaysi sezonni ko'rmoqchisiz?")
    await state.set_state(VideoStates.season_select.state)
```

### 🧪 Как проверить:

1. **Запустите бота** - `python app.py`
2. **Добавьте новый сезон** через `/add_season`
3. **Проверьте Centris Towers** - новый сезон должен отобразиться сразу

### 🎉 Результат:
Теперь Centris Towers работает точно так же, как Golden Lake - просто и надежно!
