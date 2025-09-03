# 🏢 CENTRIS TOWERS VA GOLDEN LAKE VIDEO TARQATISH BOT TIZIMI

## 📋 LOYIHA HAQIDA

**Loyiha nomi:** Centris Towers va Golden Lake Video Tarqatish Bot Tizimi
**Versiya:** 2.0.0
**Til:** Python (aiogram framework)
**Ma'lumotlar bazasi:** PostgreSQL
**Ishlab chiqaruvchi:** Mohirbek
**Sana:** 2025-01-19

---

## 🎯 LOYIHA MAQSADI

Bu Telegram bot tizimi Centris Towers va Golden Lake loyihalari uchun video kontentni avtomatik ravishda guruhlar va foydalanuvchilarga tarqatish uchun yaratilgan.

### 🔑 ASOSIY VAZIFALAR:
- 📹 Video kontentni avtomatik tarqatish
- ⏰ Vaqt bo'yicha rejalashtirish
- 👥 Guruhlar boshqaruvi
- 🔐 Xavfsizlik va ruxsatlar tizimi
- 📊 Progress va statistika kuzatuvi

---

## 🏗️ TIZIM ARXITEKTURASI

### 📊 ASOSIY KOMPONENTLAR:

1. **🤖 Telegram Bot Interface**
   - Foydalanuvchi bilan o'zaro aloqa
   - Buyruqlar qayta ishlash
   - Xabarlar yuborish

2. **🔐 Xavfsizlik Tizimi**
   - Foydalanuvchilarni autentifikatsiya
   - Admin ruxsatlari
   - Guruhlar whitelist

3. **📊 Ma'lumotlar Bazasi (PostgreSQL)**
   - Foydalanuvchilar ma'lumotlari
   - Video va sezonlar
   - Guruh sozlamalari
   - Progress kuzatuvi

4. **⏰ Rejalashtiruvchi (APScheduler)**
   - Avtomatik video yuborish
   - Vaqt bo'yicha boshqaruv
   - Takrorlanuvchi vazifalar

5. **📹 Video Tarqatish Tizimi**
   - Kanallardan video olish
   - Guruhlar bo'yicha tarqatish
   - Progress kuzatuvi

---

## 💾 MA'LUMOTLAR BAZASI TUZILISHI

### 📋 ASOSIY JADVALLAR:

#### 👤 `users` - Foydalanuvchilar
```sql
- user_id (BIGINT) - Foydalanuvchi ID
- name (TEXT) - Ism
- phone (TEXT) - Telefon raqam
- is_group (BOOLEAN) - Guruh ekanligini ko'rsatadi
- is_banned (BOOLEAN) - Bloklangan holati
- reg_date (TIMESTAMP) - Ro'yxatdan o'tgan sana
- status (TEXT) - Holat (pending/approved/denied)
```

#### 🏢 `group_video_settings` - Guruh Video Sozlamalari
```sql
- chat_id (BIGINT) - Guruh ID
- centris_enabled (BOOLEAN) - Centris faol
- centris_season_id (INT) - Centris sezoni
- centris_start_video (INT) - Boshlash video pozitsiyasi
- golden_enabled (BOOLEAN) - Golden Lake faol
- golden_season_id (INT) - Golden Lake sezoni
- golden_start_video (INT) - Boshlash video pozitsiyasi
- viewed_videos (TEXT) - Ko'rilgan videolar (JSON)
- send_times (TEXT) - Yuborish vaqtlari (JSON)
```

#### 📺 `seasons` - Sezonlar
```sql
- id (SERIAL) - Seson ID
- project (TEXT) - Loyiha nomi (centris/golden)
- name (TEXT) - Seson nomi
```

#### 🎥 `videos` - Videolar
```sql
- id (SERIAL) - Video ID
- season_id (INT) - Seson ID
- url (TEXT) - Video URL
- title (TEXT) - Video sarlavhasi
- position (INT) - Video pozitsiyasi
```

---

## ⚙️ ASOSIY FUNKSIYALAR

### 🎮 FOYDALANUVCHI BUYRUQLARI

#### 🏠 Asosiy Buyruqlar:
- `/start` - Botni ishga tushirish
- `/help` - Yordam
- `/contact` - Kontakt ma'lumotlari
- `/about` - Loyiha haqida

#### 📹 Video Buyruqlari:
- `/centris_towers` - Centris Towers videolari
- `/golden_lake` - Golden Lake videolari

### 👨‍💼 ADMIN BUYRUQLARI

#### 📊 Ma'lumot Olish:
- `/users_list` - Foydalanuvchilar ro'yxati
- `/groups_list` - Guruhlar ro'yxati
- `/pending_users` - Tasdiq kutayotgan foydalanuvchilar
- `/group_settings` - Guruh sozlamalari
- `/video_status` - Video holati

#### ⚙️ Boshqaruv:
- `/approve_user <ID>` - Foydalanuvchini tasdiqlash
- `/deny_user <ID>` - Foydalanuvchini rad etish
- `/add_group <ID>` - Guruhni qo'shish
- `/remove_group <ID>` - Guruhni olib tashlash

#### 📹 Video Boshqaruv:
- `/set_group_video` - Guruh uchun video sozlash
- `/send_specific_video` - Maxsus video yuborish
- `/send_all_planned_videos` - Barcha rejalangan videolar
- `/update_group_names` - Guruh nomlarini yangilash
- `/test_send_video_all_groups` - Test video yuborish

#### 📚 Mavsum Boshqaruv:
- `/add_season` - Yangi mavsum qo'shish
- `/list_seasons` - Mavsumlar ro'yxati
- `/edit_season` - Mavsumni tahrirlash
- `/delete_season <ID>` - Mavsumni o'chirish

---

## 🔄 ISHLASH JARAYONI

### 1. 📋 RO'YXATDAN O'TISH
1. Foydalanuvchi `/start` buyrug'ini bosadi
2. Ism va telefon raqam kiritadi
3. Admin tomonidan tasdiqlanadi
4. Tizimga kirish ruxsati beriladi

### 2. 📹 VIDEO SOZLASH
1. Admin `/set_group_video` buyrug'ini ishlatadi
2. Loyihani tanlaydi (Centris/Golden/Ikkalasi)
3. Sezonni tanlaydi
4. Boshlash video pozitsiyasini belgilaydi
5. Yuborish vaqtlarini sozlaydi
6. Guruhni tanlaydi

### 3. ⏰ AVTOMATIK YUBORISH
1. Rejalashtiruvchi belgilangan vaqtda ishga tushadi
2. Ma'lumotlar bazasidan keyingi videoni oladi
3. Kanaldan videoni nusxalaydi
4. Guruhga videoni yuboradi
5. Progress ma'lumotlarini yangilaydi

### 4. 📊 MONITORING
1. Video yuborish holatini kuzatish
2. Xatoliklarni qayd etish
3. Statistika yig'ish
4. Performance kuzatuvi

---

## ⏰ YUBORISH JADVALI

### 🏢 CENTRIS TOWERS:
- **Ertalab:** 08:00 (Toshkent vaqti)
- **Kechqurun:** 20:00 (Toshkent vaqti)

### 🏊 GOLDEN LAKE:
- **Tushlik:** 11:00 (Toshkent vaqti)

### 🔄 AVTOMATIK REJALASHTIRISH:
- APScheduler yordamida
- Cron job formatida
- Vaqt zonasi: Asia/Tashkent (UTC+5)
- Xatolik holatlarda qayta urinish

---

## 🔐 XAVFSIZLIK XUSUSIYATLARI

### 🛡️ HIMOYA CHORALARI:
1. **Foydalanuvchilar Autentifikatsiyasi**
   - Ro'yxatdan o'tish majburiy
   - Admin tasdiqini kutish
   - Telefon raqam tasdiqlanishi

2. **Guruhlar Whitelist**
   - Faqat ruxsat etilgan guruhlar
   - Admin tomonidan qo'shish/olib tashlash
   - Avtomatik xavfsizlik tekshiruvi

3. **Admin Ruxsatlari**
   - Super admin va oddiy admin darajalari
   - Buyruqlarga kirish nazorati
   - Faoliyat loglash

4. **Ma'lumotlar Xavfsizligi**
   - PostgreSQL ma'lumotlar bazasi
   - SQL injection himoyasi
   - Ma'lumotlar shifrlash

---

## 📈 STATISTIKA VA MONITORING

### 📊 KUZATILAYOTGAN KO'RSATKICHLAR:
- Yuborilgan videolar soni
- Faol guruhlar soni
- Foydalanuvchilar faolligi
- Xatoliklar va istisno holatlar
- Sistema ishlash vaqti (uptime)
- Ma'lumotlar bazasi performance

### 📋 HISOBOTLAR:
- Kunlik faoliyat hisoboti
- Haftalik statistika
- Oylik xulosalar
- Xatoliklar tahlili

---

## 🚀 TEXNIK XUSUSIYATLAR

### 💻 TEXNOLOGIYALAR:
- **Dasturlash tili:** Python 3.8+
- **Framework:** aiogram 2.x
- **Ma'lumotlar bazasi:** PostgreSQL 13+
- **Rejalashtiruvchi:** APScheduler
- **Deployment:** Docker (ixtiyoriy)
- **Monitoring:** Logging va error tracking

### ⚡ PERFORMANCE:
- Bir vaqtda 100+ guruhga yuborish
- 1000+ foydalanuvchini qo'llab-quvvatlash
- 24/7 ishlab turish imkoniyati
- Avtomatik xatoliklardan tiklash

### 🔧 SOZLASH:
- Environment variables orqali konfiguratsiya
- Database migration tizimi
- Backup va restore imkoniyatlari
- Load balancing qo'llab-quvvatlashi

---

## 🛠️ O'RNATISH VA SOZLASH

### 1. 📋 TALABLAR:
```bash
Python 3.8+
PostgreSQL 13+
aiogram 2.x
APScheduler
psycopg2
```

### 2. ⚙️ SOZLASH:
```bash
# Repository klonlash
git clone [repository_url]

# Virtual environment yaratish
python -m venv venv
source venv/bin/activate

# Kutubxonalarni o'rnatish
pip install -r requirements.txt

# Ma'lumotlar bazasini sozlash
python setup_database.py

# Botni ishga tushirish
python app.py
```

### 3. 🔐 KONFIGURATSIYA:
```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://user:password@localhost/dbname
SUPER_ADMIN_ID=your_telegram_id
CHANNEL_ID=-1002550852551
```

---

## 🔮 KELAJAK REJALARI

### 📈 RIVOJLANISH YO'NALISHLARI:

#### 🌐 Web Dashboard:
- Admin panel yaratish
- Real-time monitoring
- Grafik statistika
- Foydalanuvchilar boshqaruvi

#### 📱 Mobile App:
- Android va iOS ilovalar
- Push notification
- Offline rejim
- Video preview

#### 🔗 API Integration:
- REST API yaratish
- Third-party integratsiyalar
- Webhook support
- OAuth autentifikatsiya

#### 🤖 AI Xususiyatlari:
- Kontentni avtomatik tahlil qilish
- Foydalanuvchi xulq-atvorini o'rganish
- Personallashtirilgan tavsiyalar
- Chatbot yordamchisi

#### 📊 Analytics:
- Detallashtirilgan statistika
- Foydalanuvchi segmentatsiyasi
- A/B testing
- Performance optimization

---

## 👥 JAMOA VA HISSA

### 👨‍💻 ISHLAB CHIQARUVCHI:
- **Ism:** Mohirbek
- **Rol:** Lead Developer
- **Telegram:** @mohirbek
- **Email:** mohirbek@centris.uz
- **Tajriba:** 5+ yil Python dasturlash

### 🙏 MINNATDORCHILIK:
- Python va aiogram jamoasi
- PostgreSQL ishlab chiqaruvchilar
- Open source jamiyat
- Beta testerlar va foydalanuvchilar

### 💝 QOLAB-QUVVATLASH:
Loyihani qo'llab-quvvatlash uchun:
- ⭐ GitHub'da star qo'ying
- 🐛 Bug report yuboring
- 💡 Yangi g'oyalar taklif qiling
- 📖 Hujjatlarni yaxshilashga yordam bering

---

## 📞 ALOQA

### 📧 KONTAKT MA'LUMOTLARI:
- **Telegram:** @mohirbek
- **Email:** info@centris.uz
- **Website:** https://centris.uz
- **Support:** support@centris.uz
- **Address:** Toshkent shahri, O'zbekiston

### 🆘 YORDAM:
- **Technical Support:** 24/7
- **Bug Reports:** GitHub Issues
- **Feature Requests:** Telegram
- **Documentation:** Wiki sahifalar

---

## 📄 LITSENZIYA

**Turi:** Proprietary License
**Egasi:** Centris Towers & Golden Lake
**Foydalanish:** Faqat ushbu loyihalar uchun
**Tahrirlash:** Ruxsat yo'q
**Tarqatish:** Taqiqlangan

---

## 🎯 XULOSA

Ushbu Telegram bot tizimi Centris Towers va Golden Lake loyihalari uchun zamonaviy, xavfsiz va samarali video tarqatish yechimini taqdim etadi. Tizim:

✅ **Avtomatik** - Minimal manual aralashuv
✅ **Xavfsiz** - Ko'p qatlamli himoya
✅ **Moslashuvchan** - Turli xil sozlamalar
✅ **Kengaytiriladigan** - Yangi funksiyalar qo'shish oson
✅ **Ishonchli** - 24/7 ishlash imkoniyati
✅ **Monitoring** - To'liq kuzatuv tizimi

Bu loyiha orqali minglab foydalanuvchi va yuzlab guruhlarga sifatli video kontent muntazam ravishda yetkazilmoqda.

---

**© 2025 Centris Towers & Golden Lake. Barcha huquqlar himoyalangan.**

*Bu hujjat 2025-01-19 sanasida yaratilgan va oxirgi marta yangilangan.*
