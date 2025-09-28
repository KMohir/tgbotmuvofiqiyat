# Система уведомлений об ошибках

## Описание

Система автоматически отправляет уведомления об ошибках пользователю с ID `5657091547` при возникновении любых исключений в боте.

## Компоненты системы

### 1. Глобальный обработчик ошибок (`app.py`)

Автоматически перехватывает все необработанные исключения в боте и отправляет уведомления.

```python
# Регистрируется автоматически при запуске бота
dp.errors_handler()(global_error_handler)
```

### 2. Функции уведомлений (`utils/safe_admin_notify.py`)

#### `safe_send_error_notification(bot, error_message, error_details=None, **kwargs)`
Отправляет уведомление об ошибке конкретному пользователю (ID: 5657091547).

**Параметры:**
- `bot` - экземпляр бота
- `error_message` - основное сообщение об ошибке
- `error_details` - дополнительные детали ошибки (опционально)
- `**kwargs` - дополнительные параметры для send_message

**Возвращает:** `bool` - True если сообщение отправлено успешно

#### `safe_send_error_to_all_admins(bot, error_message, error_details=None, **kwargs)`
Отправляет уведомление об ошибке всем администраторам и конкретному пользователю.

**Возвращает:** `int` - количество успешно отправленных сообщений

### 3. Декораторы для хендлеров (`utils/error_handler.py`)

#### `@error_handler(bot)`
Автоматически обрабатывает ошибки в хендлерах с отправкой уведомлений.

```python
from utils.error_handler import error_handler
from loader import bot

@error_handler(bot)
async def my_handler(message: types.Message):
    # Ваш код хендлера
    pass
```

#### `@error_handler_with_reply(bot, reply_text="Кастомный текст")`
Обрабатывает ошибки с кастомным ответом пользователю.

```python
@error_handler_with_reply(bot, "Произошла ошибка, попробуйте позже")
async def my_handler(message: types.Message):
    # Ваш код хендлера
    pass
```

### 4. Вспомогательная функция (`handlers/users/group_video_commands.py`)

#### `handle_error_with_notification(error, context, message=None)`
Обрабатывает ошибку с отправкой уведомления и ответом пользователю.

```python
try:
    # Ваш код
    pass
except Exception as e:
    await handle_error_with_notification(e, "название_функции", message)
```

## Формат уведомлений

Уведомления об ошибках отправляются в следующем формате:

```
🚨 **Ошибка в боте**

⏰ **Время:** 2024-01-15 14:30:25
❌ **Ошибка:** Ошибка в grant_access_command: Database connection failed
📋 **Детали:** Traceback (most recent call last):...

🔧 **ID пользователя:** 5657091547
```

## Настройка

### ID пользователя для уведомлений

ID пользователя настраивается в `data/config.py`:

```python
SUPER_ADMIN_ID = 5657091547  # ID пользователя для уведомлений об ошибках
```

### Логирование

Все ошибки логируются в файл `bot.log` с уровнем ERROR и выше.

## Использование в существующих хендлерах

### Вариант 1: Использование декоратора

```python
from utils.error_handler import error_handler
from loader import bot

@dp.message_handler(commands=['test'])
@error_handler(bot)
async def test_command(message: types.Message):
    # Ваш код - ошибки будут обработаны автоматически
    raise Exception("Тестовая ошибка")
```

### Вариант 2: Ручная обработка

```python
@dp.message_handler(commands=['test'])
async def test_command(message: types.Message):
    try:
        # Ваш код
        pass
    except Exception as e:
        await handle_error_with_notification(e, "test_command", message)
```

### Вариант 3: Прямой вызов функции уведомления

```python
from utils.safe_admin_notify import safe_send_error_notification

@dp.message_handler(commands=['test'])
async def test_command(message: types.Message):
    try:
        # Ваш код
        pass
    except Exception as e:
        await safe_send_error_notification(
            bot=bot,
            error_message=f"Ошибка в test_command: {str(e)}",
            error_details=str(e)
        )
        await message.answer("❌ Произошла ошибка")
```

## Безопасность

- Все уведомления отправляются безопасно с обработкой исключений
- Если отправка уведомления не удается, ошибка логируется, но не прерывает работу бота
- Детали ошибок ограничены по размеру (1000 символов) для предотвращения переполнения

## Тестирование

Для тестирования системы используйте файл `test_error_notification.py`:

```bash
python test_error_notification.py
```

## Мониторинг

Проверить работу системы можно через команду `/system_check` в боте, которая покажет статус всех компонентов системы.
