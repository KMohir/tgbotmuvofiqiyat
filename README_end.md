# 🤖 Centris Towers Telegram Bot

Centris Towers va Golden Lake loyihalari uchun video kontentni avtomatik yuboradigan Telegram bot.

## 🚀 Asosiy buyruqlar

| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/start` | Botni ishga tushirish va bosh menyu | Hamma |
| `/centris_towers` | Centris Towers haqida maʼlumot | Hamma |
| `/golden_lake` | Golden Lake haqida maʼlumot | Hamma |
| `/contact` | Aloqa maʼlumotlari | Hamma |
| `/about` | Loyihalar haqida | Hamma |
| `/set_time` | Video yuborish vaqtini sozlash | Foydalanuvchi |

## 👥 Guruhlar uchun buyruqlar

### 🎬 Video tarqatishni boshqarish
| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/set_group_video` | Guruh uchun video tarqatishni sozlash | Guruh adminlari |
| `/start_group_video` | Video tarqatishni boshlash | Guruh adminlari |
| `/stop_group_video` | Video tarqatishni toʻxtatish | Guruh adminlari |
| `/show_group_video_settings` | Guruh sozlamalarini ko‘rish | Guruh adminlari |
| `/help_group_video` | Video buyruqlari boʻyicha yordam | Guruh adminlari |

### 📊 Jarayon/Progress
| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/next_group_video` | Keyingi videoni yuborish | Guruh adminlari |
| `/skip_group_video` | Joriy videoni o‘tkazib yuborish | Guruh adminlari |
| `/status_group_video` | Video tarqatish holati | Guruh adminlari |
| `/list_group_videos` | Barcha videolar ro‘yxati | Guruh adminlari |
| `/all_groups_progress` | Barcha guruhlar progressi | Super-admin |

### 🔧 Sinov va diagnostika
| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/test_group_video` | Videoni test yuborish | Guruh adminlari |
| `/debug_group_video` | Guruh sozlamalarini diagnostika qilish | Guruh adminlari |
| `/diagnose_group` | Guruhni tahlil qilish | Guruh adminlari |
| `/force_group_video` | Majburiy yuborish | Guruh adminlari |
| `/force_send_now` | Hozir yuborish | Guruh adminlari |

## ⚙️ Administrativ buyruqlar

### 👤 Foydalanuvchilarni boshqarish
| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/add_admin` | Administrator qo‘shish | Super-admin |
| `/remove_admin` | Administratorni olib tashlash | Super-admin |
| `/list_admins` | Administratorlar ro‘yxati | Super-admin |
| `/get_all_users` | Barcha foydalanuvchilar ro‘yxati | Super-admin |

### 🏢 Guruhlarni boshqarish
| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/add_group_to_whitelist` | Guruhni whitelistga qo‘shish | Super-admin |
| `/remove_group_from_whitelist` | Guruhni whitelistdan olib tashlash | Super-admin |
| `/list_groups` | Barcha guruhlar ro‘yxati | Super-admin |
| `/unban_all_groups` | Barcha guruhlarni blokdan chiqarish | Super-admin |

### 📤 Kontent yuborish
| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/send_content` | Kontent yuborish | Super-admin |
| `/send_now` | Videoni hozir yuborish | Super-admin |

## 🎥 Video boshqaruvi

### ⏰ Vaqt sozlamalari
| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/set_centr_time` | Centris vaqti | Super-admin |
| `/set_golden_time` | Golden Lake vaqti | Super-admin |
| `/settime` | Foydalanuvchi vaqti | Foydalanuvchi |

### 🔄 Mavsumlar (Sezonlar)
| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/fix_season_project` | Mavsum loyihasini tuzatish | Super-admin |
| `/fix_group_seasons` | Guruh mavsumlarini tuzatish | Super-admin |
| `/fix_season_ids` | Mavsum IDlarini to‘g‘rilash | Super-admin |
| `/seasons_stats` | Mavsumlar statistikasi | Super-admin |

## 🔍 Diagnostika

### 📊 Statistika va monitoring
| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/stats_group_video` | Video statistikasi | Guruh adminlari |
| `/monitor_group_video` | Tizim monitoringi | Super-admin |
| `/version_group_video` | Versiya | Hamma |
| `/ping_group_video` | Aloqa tekshiruvi | Hamma |

### 🐛 Tuzatish va debugging
| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/fix_video_system` | Video tizimini tuzatish | Super-admin |
| `/fix_all_scheduler_problems` | Rejalashtiruvchi muammolarini tuzatish | Super-admin |
| `/emergency_fix_all` | Favqulodda tuzatish | Super-admin |
| `/simple_fix` | Oddiy tuzatish | Super-admin |

### 🧪 Testlar
| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/test_send_video` | Video yuborishni testlash | Super-admin |
| `/test_scheduler_now` | Rejalashtiruvchini testlash | Super-admin |
| `/test_auto_season_switch` | Avto-mavsum almashtirish testi | Super-admin |
| `/test_video_sequence` | Video ketma-ketligi testi | Super-admin |

## ⏰ Rejalashtiruvchi (Scheduler)

| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/schedule_group_video` | Vazifalarni qayta rejalashtirish | Guruh adminlari |
| `/scheduler_debug` | Rejalashtiruvchini diagnostika qilish | Super-admin |
| `/restart_scheduler` | Rejalashtiruvchini qayta ishga tushirish | Super-admin |
| `/cleanup_scheduler_jobs` | Rejalashtiruvchi vazifalarini tozalash | Super-admin |
| `/update_schedule` | Jadvalni yangilash | Super-admin |

## 🔐 Kirish huquqlari

| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/grant_access` | Guruhga ruxsat berish | Super-admin |
| `/revoke_access` | Guruhdan ruxsatni olib tashlash | Super-admin |
| `/check_access` | Guruh kirishini tekshirish | Guruh adminlari |
| `/auto_revoke` | Avtomatik ruxsat bekor qilish | Super-admin |
| `/access_stats` | Kirish statistikasi | Super-admin |
| `/access_help` | Kirish bo‘yicha yordam | Hamma |

## 🛠️ Tizim buyruqlari

### 💾 Zaxira nusxa
| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/backup_group_video` | Zaxira nusxa yaratish | Super-admin |
| `/restore_group_video` | Zaxiradan tiklash | Super-admin |

### 🧹 Tozalash va xizmat
| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/cleanup_group_video` | Tizimni tozalash | Super-admin |
| `/logs_group_video` | Loglarni ko‘rish | Super-admin |
| `/delete_bot_messages` | Bot xabarlarini o‘chirish | Guruh adminlari |

### 🔄 Qayta ishga tushirish va tiklash
| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/restart_scheduler` | Rejalashtiruvchini qayta ishga tushirish | Super-admin |
| `/reboot_group_video` | Video tizimini qayta ishga tushirish | Super-admin |
| `/emergency_group_video` | Favqulodda tiklash | Super-admin |

### 📋 Maʼlumot va qoʻllab-quvvatlash
| Buyruq | Tavsif | Kirish |
|--------|--------|--------|
| `/all_group_commands` | Guruhlar uchun barcha buyruqlar | Guruh adminlari |
| `/info_group_video` | Tizim haqida maʼlumot | Hamma |
| `/support_group_video` | Qo‘llab-quvvatlash | Hamma |
| `/about_group_video` | Video tizimi haqida | Hamma |

## 🚨 Favqulodda buyruqlar

| Buyruq | Tavsif | Qachon |
|--------|--------|--------|
| `/emergency_fix_all` | Barcha muammolarni tez tuzatish | Tizim ishlamay qolganda |
| `/emergency_group_video` | Video tizimini favqulodda tiklash | Video muammolarida |
| `/reboot_group_video` | Video tizimini qayta ishga tushirish | Tizim osilib qolsa |
| `/fix_all_scheduler_problems` | Rejalashtiruvchi muammolarini tuzatish | Rejalashtiruvchi nosoz bo‘lsa |

## 📝 Kirish darajalari

- **Hamma** — barcha foydalanuvchilar
- **Foydalanuvchi** — ro‘yxatdan o‘tgan foydalanuvchilar
- **Guruh adminlari** — guruh administratorlari
- **Super-admin** — faqat yuqori darajadagi administratorlar

## 📞 Qo‘llab-quvvatlash

Muammo bo‘lsa yoki savollar bo‘lsa:

1. Yordam uchun `/help_group_video` ni ishlating
2. Holatni `/status_group_video` orqali tekshiring
3. `/support_group_video` orqali super-admin bilan bog‘laning

---

*So‘nggi yangilanish: 2025-01-27*
