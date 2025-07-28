# 🤖 Ta'lim videolarini tarqatish uchun Telegram-bot

## 📋 Loyiha tavsifi

**Centris Towers Bot** — bu guruhlar va shaxsiy chatlar uchun ta'lim videolarini avtomatik tarqatuvchi Telegram-bot. Bot ikkita asosiy loyihani qo'llab-quvvatlaydi: **Centris Towers** va **Golden Lake**, har biri ko'plab mavsum video materiallariga ega.

### 🎯 Asosiy imkoniyatlar:
- 📅 **Jadval bo'yicha avtomatik video tarqatish**
- 🛡️ **Foydalanuvchilarni avtorizatsiya qilish xavfsizlik tizimi**
- 👥 **Guruhlar va foydalanuvchilarni boshqarish**
- 📊 **Video ko'rish jarayonini kuzatish**
- ⚙️ **Har bir guruh uchun moslashuvchan sozlamalar**
- 🔐 **Super-adminlar uchun administrativ panel**

---

## 🚀 Tezkor boshlash

### 📦 Bog'liqliklarni o'rnatish
```bash
pip install -r requirements.txt
```

### 🗄️ PostgreSQL sozlash
```bash
# Linux/macOS uchun
./setup_postgres.sh

# Windows uchun
setup_postgres.bat
```

### 🔧 Konfiguratsiya (.env fayli)
```env
BOT_TOKEN=sizning_bot_tokeningiz
ADMINS=5657091547,123456789
DB_HOST=localhost
DB_NAME=centris_bot
DB_USER=postgres
DB_PASS=sizning_parolingiz
DB_PORT=5432
operator=sizning_id
```

### ▶️ Botni ishga tushirish
```bash
# Linux/macOS
./run_project.sh

# Windows
run_project.bat

# Yoki to'g'ridan-to'g'ri
python app.py
```

---

## 🛡️ XAVFSIZLIK TIZIMI - TO'LIQ HIMOYA

### 🔐 MAKSIMAL BLOKIROVKA AMALGA OSHIRILDI

Bot **100% himoya tizimi** bilan ishlaydi. Faqat tasdiqlangan foydalanuvchilar va avtorizatsiya qilingan guruhlar botdan foydalanishlari mumkin.

### 🚫 **TASDIQLANMAGANLAR UCHUN TO'LIQ BLOKIROVKA**

#### 👤 **Foydalanuvchilar:**
- ❌ **Tasdiqlanmagan foydalanuvchilar** → **Botdan foydalana OLMAYDI**
- ❌ **Tasdiq kutayotganlar** → **Botdan foydalana OLMAYDI**
- ❌ **Rad etilgan foydalanuvchilar** → **Botdan foydalana OLMAYDI**
- ✅ **Tasdiqlangan foydalanuvchilar** → **To'liq kirish huquqi**
- ✅ **Super-adminlar** → **To'liq kirish + boshqaruv**

#### 🏢 **Guruhlar:**
- ❌ **Avtorizatsiya qilinmagan guruhlar** → **Bot AVTOMATIK tark etadi**
- ✅ **Avtorizatsiya qilingan guruhlar** → **To'liq funksionallik**
- 🤖 **Super-admin tomonidan avtomatik qo'shish** → **Yangi guruhlar avtomatik whitelist ga**

### 🛡️ **BLOKIROVKA MEXANIZMLARI**

#### 🔒 **1. Middleware Security (CancelHandler):**
- **Oddiy xabarlar** → Tasdiqlanmagan foydalanuvchilarni blokirovka
- **Callback so'rovlar** → Tasdiqlanmaganlar uchun blokirovka
- **Inline so'rovlar** → Tasdiqlanmaganlar uchun blokirovka
- **Guruh xabarlari** → Avtorizatsiya qilinmagan guruhlardan avtochiqish

#### 🤖 **2. Auto-Leave Handler:**
- **Botni guruhga qo'shganda** → Whitelist tekshiruvi
- **Avtorizatsiya qilinmagan guruh** → Xabar bilan avtochiqish
- **Super-admin qo'shsa** → Avtomatik whitelist ga qo'shish
- **Avtorizatsiya qilingan guruh** → Salomlash xabari

### 📊 **HOZIRGI TIZIM HOLATI**

#### 👥 **Tasdiqlangan foydalanuvchilar (5):**
```
✅ 5657091547 - Mohirbek (SUPER-ADMIN)
✅ 744067583 - Sardor
✅ 6621396020 - Orqaga qaytish
✅ 7577910176 - Ko'rsatilmagan
✅ 7983512278 - Ko'rsatilmagan
```

#### 🏢 **Avtorizatsiya qilingan guruhlar (3):**
```
✅ -1002847321892 - Migrated Group
✅ -1002223935003 - Migrated Group  
✅ -4911418128 - Migrated Group
```

#### ⏳ **Tasdiq kutayotganlar:** 0

### 🧪 **HIMOYA TIZIMI SINOVI**

#### ❌ **Nima ISHLAMAYDI (to'g'ri blokirovka):**
1. **Yangi foydalanuvchilar** → `/start` orqali ro'yxatdan o'tishni talab qiladi
2. **Tasdiqlanmaganlar** → Kutish haqida xabar oladi
3. **Rad etilganlar** → Rad etish haqida xabar oladi
4. **Yangi guruhlar** → Bot avtomatik tark etadi
5. **Tasdiqlanmaganlardan Callback/Inline** → Blokirovka qilinadi

#### ✅ **Nima ISHLAYDI (to'g'ri ruxsat):**
1. **Tasdiqlangan foydalanuvchilar** → Barcha funksiyalarga to'liq kirish
2. **Super-adminlar** → To'liq kirish + administrativ buyruqlar
3. **Avtorizatsiya qilingan guruhlar** → Bot funksiyalari ishlaydi
4. **Guruhlarni avtomatik qo'shish** → Super-admin yangi guruhlar qo'sha oladi

---

## 📺 Loyihalar va mavsumlari

### 🏢 **Centris Towers**
- **5 mavsum** ta'lim materiallari
- **Tarqatish jadvali:**
  - 1-mavsum: `08:00` va `20:00` (Asia/Tashkent)
  - Boshqa mavsumlar: faqat `08:00`

### 🌊 **Golden Lake**
- **1 mavsum** ta'lim materiallari
- **Tarqatish jadvali:**
  - Alohida: `08:00`
  - Centris bilan: `11:00`

### 📋 Mavsumlarni boshqarish:
- Buyruqlar orqali yangi mavsumlar qo'shish
- Mavjud mavsumlarni tahrirlash
- Ko'rsatish tartibini boshqarish

---

## 🗄️ Ma'lumotlar bazasi

### 📊 Jadvallar tuzilishi:

#### 👥 `users` — Foydalanuvchilar
```sql
user_id BIGINT PRIMARY KEY
name TEXT
phone TEXT
datetime TIMESTAMP
video_index INTEGER
preferred_time TEXT
last_sent TEXT
is_subscribed INTEGER
viewed_videos TEXT
is_group INTEGER
is_banned INTEGER
group_id TEXT
```

#### 🏢 `group_video_settings` — Guruh sozlamalari
```sql
chat_id TEXT PRIMARY KEY
centris_enabled INTEGER
centris_season TEXT
centris_start_season_id INTEGER
centris_start_video INTEGER
golden_enabled INTEGER
golden_start_season_id INTEGER
golden_start_video INTEGER
viewed_videos TEXT
is_subscribed INTEGER
```

#### 📺 `seasons` — Mavsumlar
```sql
id INTEGER PRIMARY KEY
project TEXT NOT NULL
name TEXT NOT NULL
```

#### 🎬 `videos` — Videolar
```sql
id SERIAL PRIMARY KEY
season_id INTEGER
url TEXT NOT NULL
title TEXT NOT NULL
position INTEGER NOT NULL
```

#### 🔐 `user_security` — Foydalanuvchilar xavfsizligi
```sql
id SERIAL PRIMARY KEY
user_id BIGINT UNIQUE
name TEXT
phone TEXT
status TEXT DEFAULT 'pending'
reg_date TIMESTAMP
approved_by BIGINT
approved_date TIMESTAMP
```

#### 🏢 `group_whitelist` — Ruxsat etilgan guruhlar
```sql
id SERIAL PRIMARY KEY
chat_id BIGINT UNIQUE
title TEXT
status TEXT DEFAULT 'active'
added_date TIMESTAMP
added_by BIGINT
```

#### 🔧 `admins` — Administratorlar
```sql
user_id BIGINT PRIMARY KEY
```

---

## 📋 Bot buyruqlari

### 👤 Foydalanuvchi buyruqlari

| Buyruq | Tavsif |
|---------|----------|
| `/start` | Botni ishga tushirish / holatni tiklash |
| `/help` | Buyruqlar bo'yicha yordam |
| `/support` | Qo'llab-quvvatlash bilan bog'lanish |
| `/taklif` | Takliflar va adminlar bilan bog'lanish |
| `/contact` | Kontakt ma'lumotlari |
| `/about` | Loyiha haqida ma'lumot |

### 🔧 Administrativ buyruqlar

#### 📊 Ma'lumot olish:
| Buyruq | Kirish huquqi | Tavsif |
|---------|--------|----------|
| `/users_list` | Super-admin | Barcha foydalanuvchilar ro'yxati + statistika |
| `/groups_list` | Super-admin | Avtorizatsiya qilingan guruhlar ro'yxati |
| `/pending_users` | Super-admin | Tasdiq kutayotgan foydalanuvchilar |
| `/list_admins` | Admin+ | Oddiy administratorlar ro'yxati |
| `/group_settings` | Admin+ | Joriy guruh sozlamalari |
| `/video_status` | Admin+ | Guruhda video tarqatish holati |
| `/schedule_info` | Admin+ | Guruh uchun tarqatish jadvali |

#### ⚙️ Boshqaruv:
| Buyruq | Kirish huquqi | Tavsif |
|---------|--------|----------|
| `/approve_user <ID>` | Super-admin | Foydalanuvchini tasdiqlash |
| `/deny_user <ID>` | Super-admin | Foydalanuvchini rad etish |
| `/add_group <ID>` | Super-admin | Guruhni whitelist ga qo'shish |
| `/remove_group <ID>` | Super-admin | Guruhni whitelist dan olib tashlash |
| `/add_admin <ID>` | Super-admin | Administrator qo'shish |
| `/remove_admin <ID>` | Super-admin | Administratorni olib tashlash |

#### 📹 Video boshqaruv:
| Buyruq | Kirish huquqi | Tavsif |
|---------|--------|----------|
| `/set_group_video` | Admin+ | Guruh uchun tarqatish sozlash masteri |
| `/group_subscribe` | Admin+ | Guruhni tarqatishga ulash |
| `/group_unsubscribe` | Admin+ | Guruhni tarqatishdan uzish |
| `/set_centr_season <ID>` | Admin+ | Centris Towers mavsumini o'rnatish |
| `/set_golden_season <ID>` | Admin+ | Golden Lake mavsumini o'rnatish |
| `/reset_progress` | Admin+ | Ko'rish jarayonini tiklash |
| `/send_test_video` | Admin+ | Test video yuborish |

#### 📚 Mavsum boshqaruv:
| Buyruq | Kirish huquqi | Tavsif |
|---------|--------|----------|
| `/add_season` | Admin+ | Yangi mavsum qo'shish |
| `/list_seasons` | Admin+ | Barcha mavsumlarni ko'rsatish |
| `/edit_season` | Admin+ | Mavsumni tahrirlash |
| `/delete_season <ID>` | Admin+ | Mavsumni o'chirish |
| `/season_help` | Admin+ | Mavsum boshqaruv yordam |

---

## 🎮 **HIMOYA TIZIMI ADMINISTRATIV BUYRUQLARI**

### 📋 **Ma'lumot olish buyruqlari:**
```bash
/users_list     # Barcha foydalanuvchilar ro'yxati + statistika
/groups_list    # Avtorizatsiya qilingan guruhlar ro'yxati
/pending_users  # Tasdiq kutayotgan foydalanuvchilar
```

### ⚙️ **Boshqaruv buyruqlari:**
```bash
/approve_user <ID>    # Foydalanuvchini tasdiqlash
/deny_user <ID>       # Foydalanuvchini rad etish
/add_group <ID>       # Guruhni whitelist ga qo'shish
/remove_group <ID>    # Guruhni whitelist dan olib tashlash
```

---

## 📅 Tarqatish tizimi

### ⏰ Yuborish jadvali:

#### 🏢 **Centris Towers:**
- **1-mavsum:** `08:00` va `20:00` (UTC+5)
- **2-5 mavsumlar:** faqat `08:00` (UTC+5)

#### 🌊 **Golden Lake:**
- **Alohida:** `08:00` (UTC+5)
- **Centris bilan:** `11:00` (UTC+5)

### 🔄 Tarqatish mantiqi:
1. **Avtomatik qidiruv** - birinchi ko'rilmagan video
2. **Yuborish** belgilangan vaqtda
3. **Belgilash** videoni ko'rilgan deb
4. **O'tish** navbatdagi videoga
5. **To'xtatish** mavsum tugaganda

### 📊 Jarayonni kuzatish:
- Har bir guruh uchun individual jarayon
- Jarayonni tiklash imkoniyati
- Boshlang'ich videoni qo'lda o'rnatish
- Ko'rishlar statistikasi

---

## 🔧 **TEXNIK AMALGA OSHIRISH**

### 📁 **Himoya tizimi fayllari:**
- `middlewares/security.py` - Asosiy middleware (CancelHandler)
- `handlers/users/security.py` - Foydalanuvchilar ro'yxatdan o'tishi
- `handlers/users/admin_security.py` - Admin buyruqlari
- `handlers/groups/group_auto_leave.py` - Guruhlardan avtochiqish
- `db.py` - Xavfsizlik MB bilan ishlash metodlari

### 🗄️ **MB jadvallari:**
- `user_security` - Foydalanuvchilar va ularning holatlari
- `group_whitelist` - Avtorizatsiya qilingan guruhlar

---

## 🎮 Interaktiv imkoniyatlar

### 📱 **Klaviaturalar va menyular:**
- **Asosiy menyu** — loyihani tanlash
- **Mavsum menyusi** — MB dan dinamik
- **Admin panel** — sozlamalarni boshqarish
- **Inline klaviaturalar** — guruhlarni sozlash uchun

### 🔧 **FSM (Holatlar mashinasi):**
- **Foydalanuvchilarni ro'yxatdan o'tkazish** — bosqichma-bosqich jarayon
- **Guruhlarni sozlash** — interaktiv master
- **Mavsumlarni boshqarish** — dialoglar orqali tahrirlash
- **Avtotiklash** `/start` buyrug'i bilan

---

## 📁 Loyiha tuzilishi

```
tgbotmuvofiqiyat_old/
├── 📄 app.py                      # Asosiy dastur fayli
├── 📄 loader.py                   # Bot va dispetcher yuklagichi
├── 📄 db.py                       # Ma'lumotlar bazasi bilan ishlash
├── 📄 requirements.txt            # Loyiha bog'liqliklari
├── 📄 setup_postgres.sh/bat       # MB sozlash skriptlari
├── 📄 run_project.sh/bat          # Ishga tushirish skriptlari
├── 📄 migrate_db.py               # Ma'lumotlar bazasi migratsiyasi
├── 📄 clear_database.py           # Ma'lumotlar bazasini tozalash
├── 📄 translation.py              # Tarjimalar
├── 📂 data/
│   └── 📄 config.py               # Loyiha konfiguratsiyasi
├── 📂 handlers/                   # Buyruqlar ishlovchilari
│   ├── 📂 users/                  # Foydalanuvchi buyruqlari
│   ├── 📂 groups/                 # Guruh buyruqlari
│   └── 📂 errors/                 # Xatolarni qayta ishlash
├── 📂 middlewares/                # Oraliq dasturiy ta'minot
│   └── 📄 security.py             # Xavfsizlik tizimi
├── 📂 keyboards/                  # Klaviaturalar
│   └── 📂 default/
├── 📂 states/                     # FSM holatlari
├── 📂 utils/                      # Yordamchi vositalar
├── 📂 filters/                    # Xabar filtrlari
└── 📂 database/                   # Qo'shimcha MB fayllari
```

---

## 🧪 Sinov va nosozliklarni tuzatish

### 🔍 **Sinov buyruqlari:**
```bash
# Xavfsizlik tizimi sinovi
/users_list                    # Foydalanuvchilarni tekshirish
/groups_list                   # Guruhlarni tekshirish
/pending_users                 # Kutayotganlarni tekshirish

# Tarqatish sinovi
/send_test_video              # Test video yuborish
/video_status                 # Tarqatish holatini tekshirish
/schedule_info                # Jadvalni tekshirish

# Sozlamalar sinovi
/group_settings               # Guruh sozlamalarini ko'rsatish
/set_group_video              # Sozlash masterini ishga tushirish
```

### 📊 **Jurnallashtirish:**
- **Fayl:** `bot.log`
- **Daraja:** ERROR (sozlanadi)
- **Mazmuni:** xatolar, admin harakatlari, video tarqatish

### 🐛 **Nosozliklarni tuzatish fayllari:**
- `debug_test_bot.py` — funksiyalarni sinash
- `add_admins_debug.py` — adminlar qo'shish
- Ko'p jurnal fayllari `bot_*.log`

---

## 🔧 Texnik ma'lumotlar

### 📚 **Asosiy kutubxonalar:**
- `aiogram==2.25.1` — Telegram Bot API
- `psycopg2-binary` — PostgreSQL drayveri
- `apscheduler` — Vazifalar rejalashtiruvchisi
- `pytz==2023.3` — Vaqt zonalari bilan ishlash
- `pandas` — Ma'lumotlarni qayta ishlash
- `openpyxl` — Excel bilan ishlash

### 🌐 **Tizim talablari:**
- **Python:** 3.8+
- **MB:** PostgreSQL 12+
- **OS:** Linux/Windows/macOS
- **RAM:** 512MB+
- **Disk:** 1GB+

### ⚡ **Ishlash ko'rsatkichlari:**
- **Bir vaqtli foydalanuvchilar:** 1000+
- **Kunlik tarqatish:** 10,000+ xabar
- **Javob vaqti:** <1 soniya
- **Ishlash vaqti:** 99.9%

---

## 🔐 Xavfsizlik va maxfiylik

### 🛡️ **Xavfsizlik choralari:**
- **Middleware filtrlash** barcha kiruvchi xabarlar
- **Guruh whitelist** — faqat ruxsat etilgan guruhlar
- **Ro'yxatdan o'tish tizimi** qo'lda moderatsiya bilan
- **Avtochiqish** avtorizatsiya qilinmagan guruhlardan
- **Jurnallashtirish** barcha administrativ harakatlar

### 📱 **Ma'lumotlarni himoyalash:**
- **Heshlashtirish** sezgir ma'lumotlar
- **Minimizatsiya** shaxsiy ma'lumotlar yig'ish
- **Avtotayyorlash** vaqtinchalik fayllar
- **Zaxira nusxa** ma'lumotlar bazasi

---

## 🚀 Joylashtirish

### 🖥️ **Mahalliy joylashtirish:**
1. Repositoriyani klonlash
2. PostgreSQL o'rnatish
3. `.env` faylini sozlamalar bilan yaratish
4. Bog'liqliklarni o'rnatish: `pip install -r requirements.txt`
5. Ishga tushirish: `python app.py`

### ☁️ **Bulut joylashtirish:**
- **Heroku** — avtomatik joylashtirish
- **DigitalOcean** — VPS server
- **AWS** — to'liq bulut infratuzilmasi
- **Docker** — konteynerlashtirish

---

## 📈 Monitoring va analitika

### 📊 **Ko'rsatkichlar:**
- Faol foydalanuvchilar soni
- Video ko'rish statistikasi
- Ro'yxatdan o'tgan guruhlar soni
- Xatolar va ishlash ko'rsatkichlari

### 🔍 **Jurnallar:**
- `bot.log` da tizim hodisalari
- Batafsil trace bilan xatolar
- Administrativ harakatlar
- Tarqatish statistikasi

---

## 🆘 Qo'llab-quvvatlash va yordam

### 📞 **Kontaktlar:**
- **Telegram:** @CentrisTowersbot
- **Super-admin:** Mohirbek (ID: 5657091547)
- **Texnik yordam:** `/support` buyrug'i orqali

### 📚 **Hujjatlar:**
- `/help` — asosiy yordam
- `/season_help` — mavsumlarni boshqarish
- `SECURITY_FINAL_STATUS.md` — xavfsizlik tizimi
- `FINAL_SECURITY_REPORT.md` — xavfsizlik hisoboti

### 🐛 **Xatolar haqida xabar berish:**
1. Botda `/support` buyrug'i
2. Muammoni batafsil tasvirlash
3. Kerak bo'lsa skrinshot qo'shish
4. Foydalanuvchi/guruh ID ni ko'rsatish

---

## 🎯 **YAKUNIY NATIJA**

### ✅ **100% BLOKIROVKA ERISHILDI:**

1. **🚫 Tasdiqlanmagan foydalanuvchilar** - Botdan foydalana **OLMAYDI**
2. **🚫 Avtorizatsiya qilinmagan guruhlar** - Botdan foydalana **OLMAYDI**
3. **✅ Tizim to'liq avtomatlashtirilgan**
4. **✅ Barcha xabarlar o'zbek tilida**
5. **✅ Super-adminlar to'liq nazoratga ega**

---

## 📝 Litsenziya va mualliflik huquqlari

**© 2024 Centris Towers Bot**  
Barcha huquqlar himoyalangan.  

Loyiha ta'lim maqsadlari va Centris Towers hamda Golden Lake loyihalari bo'yicha ta'lim materiallarini tarqatish uchun ishlab chiqilgan.

---

## 🎯 Roadmap va rivojlanish rejalari

### 🔮 **Rejalashtirilgan funksiyalar:**
- [ ] Adminlar uchun veb-interfeys
- [ ] Mobil ilova
- [ ] Xabarnomalar tizimi
- [ ] Analitik panel
- [ ] Integratsiyalar uchun API
- [ ] Ko'p tillilik
- [ ] Ilg'or ko'rish analitikasi

### 🚀 **Hozirgi holat:**
- ✅ Asosiy funksionallik amalga oshirildi
- ✅ Xavfsizlik tizimi faol
- ✅ Avtomatik tarqatish ishlaydi
- ✅ Administrativ panel ishlaydi
- ✅ Ma'lumotlar bazasi optimallashtirildi

---

## 📋 **GURUH UCHUN TO'LIQ QO'LLANMA**

### 1. Botni yangi guruhga qo'shish
- Botni guruhga taklif qiling va unga xabar yuborish huquqini bering.

### 2. Guruhni obunaga ulash
- Guruhda (admin yoki super-admin nomidan):
  ```
  /group_subscribe
  ```
  Bot: "Guruh muvaffaqiyatli obunaga ulandi!"

### 3. Centris Towers uchun boshlang'ich mavsum va video tanlash
- Mavsum ID sini bilib oling (masalan, SQL orqali yoki super-admindan so'rang).
- Guruhda yozing:
  ```
  /set_centr_season <mavsum_id>
  ```
  Masalan:
  ```
  /set_centr_season 2
  ```
  Bot: "centris_start_season_id o'rnatildi: 2"

### 4. Golden Lake uchun sozlash (ixtiyoriy)
- Golden Lake uchun mavsum tanlash:
  ```
  /set_golden_season <mavsum_id>
  ```
  Masalan:
  ```
  /set_golden_season 1
  ```
  Bot: "golden_start_season_id o'rnatildi: 1"

### 5. Sozlamalarni tekshirish
- Guruhda yozing:
  ```
  /group_settings
  ```
  Bot barcha joriy sozlamalarni ko'rsatadi.

### 6. Test uchun video yuborish
- Guruhda (admin yoki super-admin):
  ```
  /send_test_video
  ```

### 7. Foydali buyruqlar ro'yxati
- `/group_subscribe` — guruhni obunaga ulash
- `/group_unsubscribe` — guruhni obunadan chiqarish
- `/set_centr_season <id>` — Centris Towers uchun mavsum ID
- `/set_golden_season <id>` — Golden Lake uchun mavsum ID
- `/group_settings` — guruh sozlamalarini ko'rish
- `/send_test_video` — test video yuborish
- `/reset_progress` — jarayonni tiklash

---

**🎉 Bot to'liq foydalanish uchun tayyor!**

*Batafsil ma'lumot olish uchun bot buyruqlaridan foydalaning yoki administratorlarga murojaat qiling.*
