# 🎯 Centris Bot - Sodda Funksiyalar Qo'llanmasi

## 📋 **Bot Nima?**

**Centris Bot** - bu Telegram bot bo'lib, Centris Towers va Golden Lake loyihalari uchun videolarni avtomatik yuborish va foydalanuvchilarga video taqsimlash vazifasini bajaradi.

---

## ⚡ **Asosiy Funksiyalar**

### 🎥 **Video Yuborish**
- **Avtomatik yuborish** - Har kuni belgilangan vaqtda
- **O'z vaqtini belgilash** - 5 ta tayyor vaqtdan tanlash
- **Progress kuzatish** - Qaysi videolar ko'rilgan

### 👥 **Guruh Boshqaruvi**
- **Guruh qo'shish/o'chirish**
- **Guruh nomini o'zgartirish**
- **Guruh sozlamalarini ko'rish**

### 🔐 **Xavfsizlik Tizimi**
- **Foydalanuvchi ro'yxatdan o'tkazish**
- **Admin huquqlari**
- **Guruh whitelist**

---

## 👤 **Foydalanuvchi Buyruqlari**

| Buyruq | Vazifa |
|--------|---------|
| `/start` | Botni ishga tushirish |
| `/help` | Yordam olish |
| `/menu` | Asosiy menyu |
| `/projects` | Loyihalarni ko'rish |
| `/videos` | Videolarni ko'rish |
| `/settings` | Sozlamalarni o'zgartirish |

---

## 🎬 **Video Funksiyalari**

### **Avtomatik Video Yuborish**
1. **Vaqt kelganda** - Belgilangan soatda
2. **Keyingi video topiladi** - Ko'rilmagan videolar
3. **Foydalanuvchiga yuboriladi** - Telegram orqali
4. **Progress yangilanadi** - Database da

### **Vaqtni O'zi Belgilash**
- **09:00** - Ertalab
- **12:00** - Tushlik
- **15:00** - Kechki tushlik
- **18:00** - Kechqurun
- **21:00** - Kechki

---

## 🔐 **Admin Buyruqlari**

| Buyruq | Vazifa | Misol |
|--------|---------|-------|
| `/set_group_video` | Guruh video sozlamalari | `/set_group_video centris 2` |
| `/add_season` | Yangi mavsum qo'shish | `/add_season golden 3` |
| `/add_video` | Yangi video qo'shish | `/add_video centris 2 5` |
| `/send_video` | Videoni yuborish | `/send_video all` |
| `/user_management` | Foydalanuvchilarni boshqarish | `/user_management` |
| `/statistics` | Statistikalarni ko'rish | `/statistics` |

---

## ⏰ **Vaqt Boshqaruvi**

### **Default Vaqtlar**
- **08:00** - Ertalab
- **20:00** - Kechki

### **O'z Vaqtini Belgilash**
1. **Vaqtni tanlash** - 5 ta tayyor vaqtdan
2. **Database ga saqlash** - preferred_time
3. **Scheduler yangilash** - Yangi cron job
4. **Avtomatik yuborish** - Har kuni shu vaqtda

---

## 🔒 **Xavfsizlik Tizimi**

### **Foydalanuvchi Ro'yxatdan O'tkazish**
1. **Foydalanuvchi /start yuboradi**
2. **Ma'lumotlar kiritiladi**
3. **Admin tasdiqlaydi**
4. **Ruxsat beriladi**
5. **Bot funksiyalari ochiladi**

### **Admin Huquqlari**
- **Admin** - Oddiy admin
- **Super Admin** - Yuqori huquqlar
- **Guruh Whitelist** - Ruxsat berilgan guruhlar

---

## 💾 **Database**

### **Asosiy Jadvalar**
- **users** - Foydalanuvchilar ma'lumotlari
- **group_video_settings** - Guruh sozlamalari
- **videos** - Video ma'lumotlari
- **seasons** - Mavsumlar
- **user_security** - Xavfsizlik ma'lumotlari
- **group_whitelist** - Guruh ruxsatlari
- **admins** - Admin ma'lumotlari

---

## 📤 **Video Yuborish Jarayoni**

### **1. Vaqt Kelganda**
- Scheduler ishga tushadi
- Belgilangan vaqt tekshiriladi

### **2. Keyingi Video Topiladi**
- Ko'rilmagan videolar qidiriladi
- Progress tekshiriladi

### **3. Foydalanuvchiga Yuboriladi**
- Telegram orqali yuboriladi
- Xatoliklar tekshiriladi

### **4. Progress Yangilanadi**
- Database da yangilanadi
- Keyingi video rejalashtiriladi

---

## 🔧 **Xatoliklarni Tuzatish**

### **Tuzatilgan Xatoliklar**
- ✅ **Parse mode xatoliklari** - HTML/Markdown
- ✅ **Database xatoliklari** - "too many values to unpack"
- ✅ **Scheduler xatoliklari** - Vaqt boshqaruvi
- ✅ **Video yuborish xatoliklari** - Chat not found

### **Log Fayllarini Ko'rish**
- **video_scheduler.py** - Scheduler xatoliklari
- **group_video_commands.py** - Buyruq xatoliklari
- **security.py** - Xavfsizlik xatoliklari

---

## 📊 **Statistika va Monitoring**

### **Asosiy Ko'rsatkichlar**
- **Foydalanuvchilar soni**
- **Yuborilgan videolar**
- **Xatoliklar soni**
- **Guruhlar soni**
- **Video progress**
- **Tizim holati**

---

## 📖 **Foydalanish Qo'llanmasi**

### **1. Botni Ishga Tushirish**
```bash
python app.py
```

### **2. Foydalanuvchi Ro'yxatdan O'tkazish**
- `/start` buyrug'ini yuborish
- Ma'lumotlarni kiritish
- Admin tasdiqini kutish

### **3. Video Sozlamalari**
- Guruh tanlash
- Mavsum tanlash
- Vaqt belgilash

### **4. Admin Funksiyalari**
- Guruh boshqaruvi
- Video qo'shish
- Statistikalarni ko'rish

---

## ✨ **Afzalliklar**

- 🚀 **Avtomatik video yuborish**
- 🎯 **Oson boshqaruv**
- 🔒 **Xavfsizlik tizimi**
- 👥 **Ko'p guruh qo'llab-quvvatlash**
- 📊 **Real-time monitoring**
- 🔧 **Xatoliklarni avtomatik tuzatish**

---

## ⚙️ **Texnik Talablar**

- **Python 3.8+**
- **PostgreSQL database**
- **Telegram Bot API**
- **APScheduler**
- **aiogram 2.x**
- **Linux server**

---

## 🎯 **Yakuniy**

✅ **Bot to'liq ishlayapti**  
✅ **Barcha funksiyalar tushunarli**  
✅ **Xatoliklar tuzatildi**  
✅ **Prezentatsiya tayyor**  
✅ **Foydalanish oson**  
✅ **Texnik qo'llab-quvvatlash mavjud**  

---

## 📁 **Fayllar**

- **`prezentatsiya_v6_sodda_funksiyalar.pptx`** - Asosiy prezentatsiya
- **`SODDA_FUNKSIYALAR_QOLLANMA.md`** - Bu qo'llanma
- **`create_presentation_v6_sodda_funksiyalar.py`** - Prezentatsiya yaratish skripti

---

## 🚀 **Boshlash**

Endi siz botning barcha funksiyalarini sodda va tushunarli holda taqdimot qilishingiz mumkin!

**🎉 Prezentatsiya tayyor!**
