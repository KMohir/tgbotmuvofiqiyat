# Описание Telegram-бота для рассылки обучающих видео

## Общая логика работы
Бот автоматически рассылает обучающие видео в Telegram-группы по индивидуальному расписанию и настройкам. Управление ботом и настройками осуществляется через команды, доступные администраторам и супер-администраторам.

---

## Роли пользователей
- **Супер-админы** — только из переменной окружения `.env` (ADMINS=5657091547,5310261745 и т.д.), их нельзя добавить или удалить через команды, только изменить в файле и перезапустить бота.
- **Обычные админы** — хранятся в базе данных, их может добавлять/удалять только супер-админ через команды `/add_admin` и `/remove_admin`.
- **Пользователи** — все остальные, могут только получать видео и использовать базовые команды.

---

## Логика рассылки видео
- Видео отправляются в группы по расписанию, с учётом выбранных курсов (Centris Towers, Golden Lake) и выбранного для каждого курса сезона. Для каждого курса рассылка начинается с первого непросмотренного видео выбранного сезона.
- **Centris Towers (centris):**
  - 1-й сезон — видео отправляются в 08:00 и 20:00 (Asia/Tashkent).
  - Остальные сезоны — только в 08:00 (Asia/Tashkent).
- **Golden Lake:**
  - Если выбран только Golden Lake — видео отправляются в 08:00 (Asia/Tashkent).
  - Если выбран вместе с Centris Towers — видео отправляются в 11:00 (Asia/Tashkent).
- Если оба потока включены — оба расписания работают параллельно.
- За один запуск отправляется только одно непросмотренное видео.
- После отправки видео оно отмечается как просмотренное для этой группы.

---

## Работа с просмотренными видео
- Для каждой группы ведётся список просмотренных видео.
- Бот всегда ищет первое непросмотренное видео из выбранного сезона и отправляет его.
- Если все видео просмотрены — рассылка для этой группы останавливается до сброса прогресса.

---

## FSM (машина состояний)
- FSM используется для управления состояниями пользователя (например, при регистрации, настройках и т.д.).
- Любой админ или супер-админ может сбросить состояние FSM командой `/start` (в группе или личке).
- Все попытки сброса и сам факт сброса логируются.

---

## Работа с базой данных
- Бот использует PostgreSQL (через библиотеку `psycopg2`).
- Все данные о группах, видео, сезонах, администраторах и просмотренных видео хранятся в базе.

---

## Логирование
- Все ключевые действия (отправка видео, сброс FSM, админские команды) и ошибки записываются в лог-файл для диагностики.

---

## Описание всех команд

### Пользовательские команды
| Команда                | Описание                                                                                   |
|------------------------|--------------------------------------------------------------------------------------------|
| `/start`               | Сброс FSM (машины состояний) для пользователя или группы.                                  |
| `/help`                | Получить справку по командам и возможностям бота.                                          |
| `/support`             | Связаться с поддержкой (отправить сообщение админам/супер-админу).                         |
| `/language`            | Выбрать язык интерфейса (если реализовано).                                                |

### Команды для админов и супер-админов
| Команда                | Кто может использовать | Описание                                                                                   |
|------------------------|-----------------------|--------------------------------------------------------------------------------------------|
| `/add_admin`           | Только супер-админ    | Добавить нового администратора по ID.                                                      |
| `/remove_admin`        | Только супер-админ    | Удалить администратора по ID.                                                              |
| `/list_admins`         | Админ, супер-админ    | Показать список всех обычных администраторов из базы.                                      |
| `/set_season`          | Админ, супер-админ    | Выбрать сезон для группы (например, 1-й или 2-й).                                          |
| `/set_start_video`     | Админ, супер-админ    | Установить стартовое видео для рассылки в группе.                                          |
| `/reset_progress`      | Админ, супер-админ    | Сбросить прогресс просмотра видео для группы (начать рассылку заново).                     |
| `/add_video`           | Админ, супер-админ    | Добавить новое видео в выбранный сезон.                                                    |
| `/add_season`          | Админ, супер-админ    | Добавить новый сезон (например, для нового потока обучения).                               |
| `/video_status`        | Админ, супер-админ    | Показать статус рассылки видео в группе (какие просмотрены, какое следующее).              |
| `/schedule_info`       | Админ, супер-админ    | Показать текущее расписание рассылки для группы.                                           |

---

## Примеры работы команд
- **/add_admin 123456789** — добавить пользователя с ID 123456789 в список обычных админов (только супер-админ может выполнять).
- **/remove_admin 123456789** — удалить пользователя с ID 123456789 из списка обычных админов (только супер-админ).
- **/list_admins** — показать всех обычных админов из базы.
- **/set_group_video centris 2** — установить для группы 2-й сезон Centris Towers.
- **/set_group_video golden 1** — установить для группы 1-й сезон Golden Lake.
- **/set_group_video both 2 1** — установить для группы 2-й сезон Centris Towers и 1-й сезон Golden Lake.
- **/reset_progress** — сбросить прогресс — все видео снова будут считаться непросмотренными, рассылка начнётся с начала.
- **/video_status** — показать, какие видео уже отправлены, какое будет следующим.

---

## Права и роли
- **Супер-админ** — только из `.env`, может добавлять/удалять обычных админов, имеет полный доступ.
- **Обычный админ** — добавляется супер-админом, может управлять настройками групп, но не может добавлять/удалять других админов.
- **Пользователи** — могут только получать видео и использовать базовые команды.

---

## Работа с базой данных
- Все данные о группах, видео, сезонах, администраторах и просмотренных видео хранятся в PostgreSQL.
- Для тестов можно быстро переключиться на SQLite (оставлен комментарий в коде).

---

## Логирование
- Все ключевые действия (отправка видео, сброс FSM, админские команды) и ошибки записываются в лог-файл для диагностики.

---

## Прочие функции
- Можно добавлять новые сезоны и видео через команды.
- Можно сбрасывать прогресс группы.
- Все лишние времена рассылки удалены — остались только нужные по ТЗ.

---

## Схема работы команд и ролей

```
Пользователь:
  /start, /help, /support, /language
Обычный админ:
  /set_season, /set_start_video, /reset_progress, /add_video, /add_season, /video_status, /schedule_info, /list_admins
Супер-админ:
  /add_admin, /remove_admin, /list_admins (и все команды обычных админов)
```

---

Если нужна расшифровка какой-то команды или логики — обратитесь к разработчику или в поддержку.

# Подробная логика команд и их работы

## Пользовательские команды

- **/start**
  - Сбрасывает состояние FSM (машины состояний) пользователя или группы.
  - В группе: если бот не зарегистрирован — добавляет группу в базу, сообщает об активации.
  - В личке: если пользователь не зарегистрирован — запускает регистрацию (запрашивает имя, телефон), после чего отправляет приветственное сообщение и первое видео.
  - Для админов и супер-админов логируется попытка сброса FSM.

- **/help**
  - Отправляет краткую справку по основным командам и возможностям бота.

- **/support** (или /taklif)
  - Позволяет пользователю отправить сообщение в поддержку (админам/супер-админу).

- **/language**
  - Позволяет выбрать язык интерфейса (если реализовано).

---

## Админские и супер-админские команды

- **/add_admin <user_id>**
  - Только для супер-админа.
  - Добавляет пользователя с указанным ID в список обычных админов.
  - Проверяет, не является ли пользователь уже админом.
  - В случае успеха — сообщает об успешном добавлении, иначе — об ошибке.

- **/remove_admin <user_id>**
  - Только для супер-админа.
  - Удаляет пользователя с указанным ID из списка админов.
  - Проверяет, является ли пользователь админом.
  - В случае успеха — сообщает об успешном удалении, иначе — об ошибке.

- **/list_admins**
  - Для админов и супер-админов.
  - Показывает список всех обычных админов из базы.

- **/set_group_video**
  - Для админов и супер-админов, только в группах.
  - Запускает пошаговый мастер настройки рассылки видео для группы:
    1. Выбор проекта (Centris Towers, Golden Lake, оба).
    2. Выбор сезона для каждого проекта.
    3. Выбор стартового видео (если нужно).
    4. Сохраняет настройки в базе, сбрасывает прогресс просмотра, активирует рассылку.
  - Все действия сопровождаются интерактивными клавиатурами.

- **/set_start_video**
  - Для админов и супер-админов.
  - Позволяет вручную выбрать, с какого видео начинать ежедневную рассылку (по номеру видео).
  - Сохраняет выбранный номер в базе.

- **/reset_progress**
  - Для админов и супер-админов.
  - Сбрасывает прогресс просмотра видео для группы — все видео снова считаются непросмотренными, рассылка начинается с начала.

- **/add_video**
  - Для админов и супер-админов.
  - Позволяет добавить новое видео в выбранный сезон (через пошаговый ввод).

- **/add_season**
  - Для админов и супер-админов.
  - Позволяет добавить новый сезон (через пошаговый ввод: название, ссылки на видео, названия видео).

- **/video_status**
  - Для админов и супер-админов.
  - Показывает статус рассылки видео в группе: какие видео уже отправлены, какое будет следующим.

- **/schedule_info**
  - Для админов и супер-админов.
  - Показывает текущее расписание рассылки для группы.

---

## Примеры работы команд

- `/add_admin 123456789` — добавить пользователя с ID 123456789 в админы.
- `/remove_admin 123456789` — удалить пользователя с ID 123456789 из админов.
- `/list_admins` — показать всех обычных админов.
- `/set_group_video centris 2` — установить для группы 2-й сезон Centris Towers.
- `/set_group_video golden 1` — установить для группы 1-й сезон Golden Lake.
- `/set_group_video both 2 1` — установить для группы 2-й сезон Centris Towers и 1-й сезон Golden Lake.
- `/reset_progress` — сбросить прогресс просмотра видео.
- `/video_status` — показать, какие видео уже отправлены, какое будет следующим.

---

## Важные детали

- Все команды для админов и супер-админов требуют проверки прав пользователя.
- Все действия логируются для диагностики и аудита.
- Для большинства команд используется FSM (машина состояний) для пошагового взаимодействия.
- Все данные о группах, видео, сезонах, администраторах и просмотренных видео хранятся в PostgreSQL.

---

# Guruh uchun to‘liq qo‘llanma (O‘zbekcha)

## 1. Botni yangi guruhga qo‘shish
- Botni guruhga taklif qiling va unga xabar yuborish huquqini bering.

## 2. Guruhni obunaga ulash
- Guruhda (admin yoki super-admin nomidan):
  ```
  /group_subscribe
  ```
  Bot: "Guruh muvaffaqiyatli obunaga ulandi!"

## 3. Centris Towers uchun boshlang‘ich mavsum va video tanlash
- Mavsum ID sini bilib oling (masalan, SQL orqali yoki super-admindan so‘rang).
- Guruhda yozing:
  ```
  /set_centr_season <mavsum_id>
  ```
  Masalan:
  ```
  /set_centr_season 2
  ```
  Bot: "centris_start_season_id o‘rnatildi: 2"

- Boshlang‘ich video pozitsiyasini o‘zgartirish uchun (agar kerak bo‘lsa, 0 — birinchi video):
  ```
  /set_centr_video <pozitsiya>
  ```
  (Agar bu buyruq yo‘q bo‘lsa, super-admin SQL orqali o‘zgartirishi mumkin.)

## 4. Golden Lake uchun sozlash (ixtiyoriy)
- Golden Lake uchun mavsum tanlash:
  ```
  /set_golden_season <mavsum_id>
  ```
  Masalan:
  ```
  /set_golden_season 1
  ```
  Bot: "golden_start_season_id o‘rnatildi: 1"

## 5. Sozlamalarni tekshirish
- Guruhda yozing:
  ```
  /group_settings
  ```
  Bot barcha joriy sozlamalarni ko‘rsatadi (qaysi loyiha yoqilgan, qaysi mavsum va video, obuna holati va boshqalar).

## 6. Test uchun video yuborish
- Guruhda (admin yoki super-admin):
  ```
  /send_test_video
  ```
  Bot tanlangan mavsum va videodan boshlab test videosini yuboradi.

## 7. Eski ma’lumotlarni migratsiya qilish (faqat super-admin)
- Agar eski guruhdan o‘tkazilsa:
  ```
  /migrate_group_video_settings
  ```
  Bot: "Migratsiya yakunlandi! Yangilangan guruhlar soni: ..."

## 8. Golden Lake uchun ham mavsumni o‘zgartirish (faqat super-admin)
- Guruhda:
  ```
  /set_golden_season <mavsum_id>
  ```

## 9. Centris Towers uchun mavsumni o‘zgartirish (faqat super-admin)
- Guruhda:
  ```
  /set_centr_season <mavsum_id>
  ```

## 10. Obunani o‘chirish
- Guruhda (admin yoki super-admin):
  ```
  /group_unsubscribe
  ```
  Bot: "Guruh obunadan chiqarildi!"

---

## Loyihalar bo‘yicha ishlash tartibi

### Faqat Centris Towers yoqilgan bo‘lsa
- Faqat Centris Towers videolari yuboriladi (08:00 va 20:00 yoki faqat 08:00 — mavsumga qarab).

### Faqat Golden Lake yoqilgan bo‘lsa
- Faqat Golden Lake videolari yuboriladi (08:00).

### Ikkalasi ham yoqilgan bo‘lsa
- Centris Towers va Golden Lake videolari alohida-alohida, o‘z vaqtida yuboriladi (Centris — 08:00 va 20:00, Golden — 11:00).

---

## Foydali buyruqlar ro‘yxati

- `/group_subscribe` — guruhni obunaga ulash
- `/group_unsubscribe` — guruhni obunadan chiqarish
- `/set_centr_season <id>` — Centris Towers uchun mavsum ID ni o‘rnatish
- `/set_golden_season <id>` — Golden Lake uchun mavsum ID ni o‘rnatish
- `/group_settings` — guruhning barcha joriy sozlamalarini ko‘rish
- `/send_test_video` — test uchun video yuborish (admin/super-admin)
- `/migrate_group_video_settings` — eski ma’lumotlarni migratsiya qilish (faqat super-admin)

---

Agar savollar bo‘lsa yoki yangi guruh uchun yordam kerak bo‘lsa — super-adminlarga murojaat qiling!
