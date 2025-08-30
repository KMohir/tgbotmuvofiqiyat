# 🎬 CENTRIS TOWERS & GOLDEN LAKE TELEGRAM BOTI
## Texnik Prezentatsiya va Ish Jarayoni Diagrammalari

---

## 📋 SLAYD 1: LOYIHA HAQIDA UMUMIY MA'LUMOT

### 🎯 **BOT MAQSADI**
- **Ta'lim videolarini avtomatik tarqatish**
- **Ikki loyiha:** Centris Towers va Golden Lake
- **Guruhlar va shaxsiy chatlar uchun**
- **Jadval bo'yicha avtomatik yuborish**

### 📊 **ASOSIY RAQAMLAR**
- **12+ buyruq** foydalanuvchilar uchun
- **20+ admin buyruqlari** boshqaruv uchun
- **100% xavfsizlik tizimi** - faqat tasdiqlangan foydalanuvchilar
- **PostgreSQL** ma'lumotlar bazasi
- **APScheduler** avtomatik yuborish uchun

---

## 📋 SLAYD 2: BOT ARXITEKTURASI DIAGRAMMASI

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   TELEGRAM      │    │    BOT CORE     │    │   DATABASE      │
│                 │    │                 │    │                 │
│ • Foydalanuvchi │◄──►│ • aiogram 2.x   │◄──►│ • PostgreSQL    │
│ • Guruhlar      │    │ • Handlers      │    │ • 8 jadval      │
│ • Adminlar      │    │ • Middlewares   │    │ • Xavfsizlik    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│  SCHEDULER      │◄─────────────┘
                        │                 │
                        │ • APScheduler   │
                        │ • Avtomatik     │
                        │ • Jadval        │
                        └─────────────────┘
```

---

## 📋 SLAYD 3: XAVFSIZLIK TIZIMI DIAGRAMMASI

```
                    FOYDALANUVCHI KIRISHI
                            │
                            ▼
                ┌───────────────────────┐
                │   XAVFSIZLIK CHECK    │
                │                       │
                │ • user_security table│
                │ • status checking     │
                └───────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   PENDING   │    │  APPROVED   │    │   DENIED    │
│             │    │             │    │             │
│ ❌ BLOKLANGAN│    │ ✅ RUXSAT   │    │ ❌ BLOKLANGAN│
│ Kutish holati│    │ To'liq kirish│    │ Rad etilgan │
└─────────────┘    └─────────────┘    └─────────────┘
```

---

## 📋 SLAYD 4: VIDEO TARQATISH TIZIMI

```
                    GURUH SOZLAMALARI
                            │
                            ▼
                ┌───────────────────────┐
                │  GROUP_VIDEO_SETTINGS │
                │                       │
                │ • centris_enabled     │
                │ • golden_enabled      │
                │ • season_id           │
                │ • start_video         │
                │ • send_times          │
                └───────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   SCHEDULER   │
                    │               │
                    │ Kunlik:       │
                    │ • 08:00       │
                    │ • 20:00       │
                    └───────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │    VIDEO YUBORISH     │
                │                       │
                │ 1. Keyingi videoni    │
                │    topish             │
                │ 2. Guruhga yuborish   │
                │ 3. Ko'rilgan deb      │
                │    belgilash          │
                └───────────────────────┘
```

---

## 📋 SLAYD 5: MA'LUMOTLAR BAZASI SXEMASI

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     USERS       │    │    SEASONS      │    │     VIDEOS      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • user_id (PK)  │    │ • id (PK)       │    │ • id (PK)       │
│ • name          │    │ • season_name   │    │ • season_id (FK)│
│ • phone         │    │ • project       │    │ • video_name    │
│ • time_to_send  │    │ • description   │    │ • file_id       │
│ • is_subscribed │    │ • created_at    │    │ • video_order   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│GROUP_VIDEO_SETT │◄─────────────┘
                        │                 │
                        │ • chat_id (PK)  │
                        │ • centris_enable│
                        │ • golden_enabled│
                        │ • season_ids    │
                        │ • viewed_videos │
                        └─────────────────┘

┌─────────────────┐    ┌─────────────────┐
│ USER_SECURITY   │    │ GROUP_WHITELIST │
├─────────────────┤    ├─────────────────┤
│ • user_id (PK)  │    │ • chat_id (PK)  │
│ • name          │    │ • title         │
│ • phone         │    │ • status        │
│ • status        │    │ • added_date    │
│ • reg_date      │    │ • added_by      │
└─────────────────┘    └─────────────────┘
```

---

## 📋 SLAYD 6: BUYRUQLAR TIZIMI

### 👤 **FOYDALANUVCHI BUYRUQLARI**
```
/start          → Botni ishga tushirish
/centris_towers → Centris videolarini ko'rish
/golden_lake    → Golden Lake videolarini ko'rish
/about          → Loyiha haqida ma'lumot
/contact        → Bog'lanish
```

### 🔧 **ADMIN BUYRUQLARI**
```
/set_group_video           → Guruh sozlamalari
/show_group_video_settings → Sozlamalarni ko'rish
/update_video_progress     → Progress yangilash
/test_send_video_all_groups→ Test yuborish
/send_all_planned_videos   → Barcha videolarni yuborish
```

### 👑 **SUPER-ADMIN BUYRUQLARI**
```
/users_list     → Foydalanuvchilar ro'yxati
/approve_user   → Foydalanuvchini tasdiqlash
/add_group      → Guruhni qo'shish
/remove_group   → Guruhni olib tashlash
```

---

## 📋 SLAYD 7: FOYDALANUVCHI REGISTRATSIYA JARAYONI

```
                    YANGI FOYDALANUVCHI
                            │
                            ▼
                    ┌───────────────┐
                    │   /start      │
                    │               │
                    │ Xavfsizlik    │
                    │ tekshiruvi    │
                    └───────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   REGISTRATSIYA       │
                │                       │
                │ 1. Ism kiritish       │
                │ 2. Telefon kiritish   │
                │ 3. Admin tasdiqi      │
                └───────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   ADMIN       │
                    │   TASDIQ      │
                    │               │
                    │ ✅ Approve    │
                    │ ❌ Deny       │
                    └───────────────┘
```

---

## 📋 SLAYD 8: GURUH VIDEO SOZLASH JARAYONI

```
                    ADMIN: /set_group_video
                            │
                            ▼
                ┌───────────────────────┐
                │   LOYIHA TANLASH      │
                │                       │
                │ • Centris Towers      │
                │ • Golden Lake         │
                │ • Ikkalasi            │
                └───────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   MAVSUM TANLASH      │
                │                       │
                │ • 1-mavsum            │
                │ • 2-mavsum            │
                │ • 3-mavsum            │
                └───────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   VAQT SOZLASH        │
                │                       │
                │ • 08:00, 20:00        │
                │ • Custom vaqtlar      │
                │ • Maksimal 5 ta       │
                └───────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   SAQLASH     │
                    │               │
                    │ ✅ Tayyor     │
                    └───────────────┘
```

---

## 📋 SLAYD 9: AVTOMATIK YUBORISH ALGORITMI

```
                    SCHEDULER ISHGA TUSHISHI
                            │
                            ▼
                ┌───────────────────────┐
                │   BARCHA GURUHLAR     │
                │                       │
                │ • Faol guruhlarni     │
                │   olish               │
                │ • Whitelist tekshir   │
                └───────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   HAR BIR GURUH       │
                │                       │
                │ 1. Sozlamalarni olish │
                │ 2. Keyingi videoni    │
                │    topish             │
                │ 3. Video yuborish     │
                │ 4. Progress yangilash │
                └───────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   NATIJA      │
                    │               │
                    │ ✅ Yuborildi  │
                    │ ❌ Xato       │
                    │ ⏭️ Keyingisi  │
                    └───────────────┘
```

---

## 📋 SLAYD 10: MIDDLEWARE VA XAVFSIZLIK

```
                    TELEGRAM XABAR KELISHI
                            │
                            ▼
                ┌───────────────────────┐
                │   SECURITY MIDDLEWARE │
                │                       │
                │ • Foydalanuvchi check │
                │ • Guruh whitelist     │
                │ • Admin huquqlari     │
                └───────────────────────┘
                            │
                    ┌───────┴───────┐
                    │               │
                    ▼               ▼
            ┌───────────────┐  ┌───────────────┐
            │   RUXSAT BOR  │  │  RUXSAT YO'Q  │
            │               │  │               │
            │ ✅ Handler    │  │ ❌ CancelHandler│
            │    ishga      │  │    to'xtatish │
            │    tushirish  │  │               │
            └───────────────┘  └───────────────┘
```

---

## 📋 SLAYD 11: LOYIHALAR VA MAVSUMLAR

### 🏢 **CENTRIS TOWERS**
- **5 mavsum** mavjud
- **Har bir mavsumda 15-20 video**
- **Yuborish vaqti:** 08:00 va 20:00
- **Boshlang'ich mavsum:** Admin tomonidan tanlanadi

### 🌊 **GOLDEN LAKE**
- **3 mavsum** mavjud  
- **Har bir mavsumda 10-15 video**
- **Yuborish vaqti:** 08:00 (yoki 11:00 Centris bilan)
- **Mustaqil yoki Centris bilan birgalikda**

### 📊 **STATISTIKA**
- **Jami videolar:** 150+
- **Faol guruhlar:** 50+
- **Kunlik yuborish:** 200+ video

---

## 📋 SLAYD 12: TEXNIK STACK

```
┌─────────────────────────────────────────────┐
│                FRONTEND                     │
│                                             │
│ • Telegram Bot API                          │
│ • Inline Keyboards                          │
│ • Reply Keyboards                           │
│ • FSM (Finite State Machine)               │
└─────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────┐
│                BACKEND                      │
│                                             │
│ • Python 3.13                              │
│ • aiogram 2.x                              │
│ • APScheduler                              │
│ • asyncio / asyncpg                        │
└─────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────┐
│               DATABASE                      │
│                                             │
│ • PostgreSQL 13+                           │
│ • 8 jadval                                 │
│ • Indexlar va optimizatsiya                │
│ • Backup va recovery                       │
└─────────────────────────────────────────────┘
```

---

## 📋 SLAYD 13: KELAJAK REJALAR

### 🚀 **REJALASHTIRILGAN YANGILIKLAR**
- 📊 **Web Admin Panel** - brauzer orqali boshqaruv
- 📱 **Mobil Ilova** - iOS va Android uchun
- 🔔 **Push Notifications** - muhim xabarlar uchun
- 📈 **Analitik Dashboard** - batafsil statistika
- 🌐 **API Integration** - tashqi tizimlar bilan
- 🗣️ **Ko'p tillilik** - ingliz, rus tillari qo'shish

### ⚡ **TEXNIK YAXSHILASHLAR**
- 🔄 **Real-time Updates** - jonli yangilanishlar
- 🛡️ **Advanced Security** - 2FA va encryption
- 📦 **Docker Support** - oson deploy qilish
- 🔍 **Logging System** - batafsil loglar
- 📊 **Performance Monitoring** - tizim monitoring

---

## 📋 SLAYD 14: XULOSA

### ✅ **HOZIRGI HOLAT**
- **100% ishlaydigan** avtomatik video tarqatish tizimi
- **Maksimal xavfsizlik** - faqat tasdiqlangan foydalanuvchilar
- **Moslashuvchan sozlamalar** - har bir guruh uchun individual
- **Barqaror ishlash** - 24/7 avtomatik yuborish
- **O'zbek tilida** - to'liq lokalizatsiya

### 🎯 **ASOSIY AFZALLIKLAR**
- 📅 **Avtomatlashtirish** - manual ish kerak emas
- 🛡️ **Xavfsizlik** - to'liq himoya tizimi  
- ⚙️ **Moslashuvchanlik** - oson sozlash va boshqaruv
- 📊 **Kuzatish** - batafsil hisobotlar va statistika
- 🚀 **Scalability** - katta miqdordagi foydalanuvchilar uchun

### 💡 **LOYIHA MUVAFFAQIYATI**
Bu bot Centris Towers va Golden Lake loyihalari uchun **samarali ta'lim video tarqatish tizimi** yaratdi va minglab foydalanuvchilarga **sifatli ta'lim materiallarini** yetkazib bermoqda.

---

**🎬 CENTRIS TOWERS & GOLDEN LAKE TELEGRAM BOTI**  
**Texnik Prezentatsiya - 2024**
