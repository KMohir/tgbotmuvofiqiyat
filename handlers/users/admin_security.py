"""
Административные команды для управления системой безопасности
"""

import logging
from aiogram import types
from aiogram.dispatcher.filters import Command
from loader import dp
from db import db
from data.config import ADMINS, SUPER_ADMIN_ID
from datetime import datetime

logger = logging.getLogger(__name__)

def is_super_admin(user_id: int) -> bool:
    """Проверить является ли пользователь супер-админом"""
    SUPER_ADMIN_IDS = [5657091547, 8053364577, 5310261745]  # Список супер-администраторов
    admin_ids = SUPER_ADMIN_IDS.copy()
    for admin in ADMINS:
        try:
            if isinstance(admin, str):
                admin_ids.append(int(admin.strip()))
            elif isinstance(admin, int):
                admin_ids.append(admin)
        except (ValueError, AttributeError):
            continue
    return user_id in admin_ids

@dp.message_handler(Command("pending_users"), chat_type=[types.ChatType.PRIVATE, types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def show_pending_users(message: types.Message):
    """Показать список пользователей ожидающих одобрения"""
    user_id = message.from_user.id
    
    if not is_super_admin(user_id):
        await message.reply("❌ Bu buyruqni bajarish uchun sizda ruxsat yo'q.")
        return
    
    pending_users = db.get_pending_users()
    
    if not pending_users:
        await message.reply("📋 **Kutayotgan foydalanuvchilar yo'q**\n\nBarcha arizalar ko'rib chiqildi.")
        return
    
    text = "⏳ **Tasdiqlashni kutayotgan foydalanuvchilar:**\n\n"
    
    for user_id_pending, name, phone, reg_date in pending_users:
        formatted_date = reg_date.strftime("%d.%m.%Y %H:%M")
        text += f"👤 **{name}**\n"
        text += f"🆔 ID: `{user_id_pending}`\n"
        text += f"📱 Telefon: {phone}\n"
        text += f"📅 Sana: {formatted_date}\n"
        text += f"Buyruqlar: `/approve_user {user_id_pending}` | `/deny_user {user_id_pending}`\n\n"
    
    await message.reply(text, parse_mode='Markdown')

@dp.message_handler(Command("users_list"), chat_type=[types.ChatType.PRIVATE, types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def show_all_users(message: types.Message):
    """Показать список всех пользователей в системе безопасности"""
    user_id = message.from_user.id
    
    if not is_super_admin(user_id):
        await message.reply("❌ Bu buyruqni bajarish uchun sizda ruxsat yo'q.")
        return
    
    all_users = db.get_all_security_users()
    
    if not all_users:
        await message.reply("📋 **Tizimda foydalanuvchilar yo'q**\n\nHech kim ro'yxatdan o'tmagan.")
        return
    
    text = "👥 **Barcha foydalanuvchilar:**\n\n"
    
    approved_count = 0
    pending_count = 0
    denied_count = 0
    
    for user_data in all_users:
        user_id_listed = user_data['user_id']
        name = user_data['name']
        phone = user_data['phone'] 
        status = user_data['status']
        reg_date = user_data['reg_date']
        
        if status == 'approved':
            status_emoji = "✅"
            approved_count += 1
        elif status == 'pending':
            status_emoji = "⏳"
            pending_count += 1
        elif status == 'denied':
            status_emoji = "❌"
            denied_count += 1
        else:
            status_emoji = "❓"
            
        formatted_date = reg_date.strftime("%d.%m.%Y") if reg_date else "Noma'lum"
        text += f"{status_emoji} **{name}**\n"
        text += f"🆔 ID: `{user_id_listed}`\n"
        text += f"📱 Telefon: {phone}\n"
        text += f"📅 Sana: {formatted_date}\n"
        text += f"📊 Status: {status}\n\n"
    
    summary = f"📊 **Xulosa:**\n"
    summary += f"✅ Tasdiqlangan: {approved_count}\n"
    summary += f"⏳ Kutayotgan: {pending_count}\n" 
    summary += f"❌ Rad etilgan: {denied_count}\n"
    summary += f"📈 Jami: {len(all_users)}\n\n"
    
    await message.reply(summary + text, parse_mode="Markdown")

@dp.message_handler(Command("approve_user"), chat_type=[types.ChatType.PRIVATE, types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def approve_user_command(message: types.Message):
    """Одобрить пользователя по ID"""
    admin_id = message.from_user.id
    
    if not is_super_admin(admin_id):
        await message.reply("❌ Bu buyruqni bajarish uchun sizda ruxsat yo'q.")
        return
    
    args = message.get_args()
    if not args:
        await message.reply("📝 **Buyruqdan foydalanish:**\n\n`/approve_user <user_id>`\n\nMisol: `/approve_user 123456789`")
        return
    
    try:
        user_id = int(args.strip())
        status = db.get_user_security_status(user_id)
        if status != 'pending':
            await message.reply(f"❌ Foydalanuvchi {user_id} tasdiqlashni kutayotganlar orasida topilmadi.")
            return
        
        user_data = db.get_user_security_data(user_id)
        if not user_data:
            await message.reply(f"❌ Foydalanuvchi ma'lumotlari topilmadi.")
            return
        
        success = db.approve_user(user_id, admin_id)
        if success:
            await message.reply(f"✅ **Foydalanuvchi tasdiqlandi**\n\n👤 **Ism**: {user_data['name']}\n🆔 **ID**: `{user_id}`\n📱 **Telefon**: {user_data['phone']}\n📅 **Sana**: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        else:
            await message.reply(f"❌ Foydalanuvchini tasdiqlashda xatolik yuz berdi.")
            
    except ValueError:
        await message.reply("❌ Noto'g'ri foydalanuvchi ID. Raqam kiriting.")
    except Exception as e:
        logger.error(f"Foydalanuvchini tasdiqlashda xatolik: {e}")
        await message.reply("❌ Tizim xatoligi yuz berdi.")

@dp.message_handler(Command("deny_user"), chat_type=[types.ChatType.PRIVATE, types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def deny_user_command(message: types.Message):
    """Отклонить пользователя по ID"""
    admin_id = message.from_user.id
    
    if not is_super_admin(admin_id):
        await message.reply("❌ Bu buyruqni bajarish uchun sizda ruxsat yo'q.")
        return
    
    args = message.get_args()
    if not args:
        await message.reply("📝 **Buyruqdan foydalanish:**\n\n`/deny_user <user_id>`\n\nMisol: `/deny_user 123456789`")
        return
    
    try:
        user_id = int(args.strip())
        status = db.get_user_security_status(user_id)
        if status != 'pending':
            await message.reply(f"❌ Foydalanuvchi {user_id} tasdiqlashni kutayotganlar orasida topilmadi.")
            return
        
        user_data = db.get_user_security_data(user_id)
        if not user_data:
            await message.reply(f"❌ Foydalanuvchi ma'lumotlari topilmadi.")
            return
        
        success = db.deny_user(user_id, admin_id)
        if success:
            await message.reply(f"❌ **Foydalanuvchi rad etildi**\n\n👤 **Ism**: {user_data['name']}\n🆔 **ID**: `{user_id}`\n📱 **Telefon**: {user_data['phone']}\n📅 **Sana**: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        else:
            await message.reply(f"❌ Foydalanuvchini rad etishda xatolik yuz berdi.")
            
    except ValueError:
        await message.reply("❌ Noto'g'ri foydalanuvchi ID. Raqam kiriting.")
    except Exception as e:
        logger.error(f"Foydalanuvchini rad etishda xatolik: {e}")
        await message.reply("❌ Tizim xatoligi yuz berdi.")

@dp.message_handler(Command("add_group"), chat_type=[types.ChatType.PRIVATE, types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def add_group_command(message: types.Message):
    """Добавить группу в whitelist"""
    user_id = message.from_user.id
    
    if not is_super_admin(user_id):
        await message.reply("❌ Bu buyruqni bajarish uchun sizda ruxsat yo'q.")
        return
    
    args = message.get_args()
    if not args:
        await message.reply("📝 **Buyruqdan foydalanish:**\n\n`/add_group <chat_id>`\n\nMisol: `/add_group -1001234567890`")
        return
    
    try:
        chat_id = int(args.strip())
        
        if db.is_group_whitelisted(chat_id):
            await message.reply(f"❌ Guruh {chat_id} allaqachon ruxsat etilganlar ro'yxatida.")
            return
        
        success = db.add_group_to_whitelist(chat_id, "Qo'shilgan guruh", user_id)
        if success:
            await message.reply(f"✅ **Guruh ruxsat etilganlar ro'yxatiga qo'shildi**\n\n🆔 **ID**: `{chat_id}`\n👨‍💼 **Qo'shgan**: {message.from_user.full_name}\n📅 **Sana**: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        else:
            await message.reply(f"❌ Guruhni qo'shishda xatolik yuz berdi.")
            
    except ValueError:
        await message.reply("❌ Noto'g'ri chat ID. Manfiy raqam kiriting (masalan: -1001234567890)")
    except Exception as e:
        logger.error(f"Guruhni qo'shishda xatolik: {e}")
        await message.reply("❌ Tizim xatoligi yuz berdi.")

@dp.message_handler(Command("remove_group"), chat_type=[types.ChatType.PRIVATE, types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def remove_group_command(message: types.Message):
    """Удалить группу из whitelist"""
    user_id = message.from_user.id
    
    if not is_super_admin(user_id):
        await message.reply("❌ Bu buyruqni bajarish uchun sizda ruxsat yo'q.")
        return
    
    args = message.get_args()
    if not args:
        await message.reply("📝 **Buyruqdan foydalanish:**\n\n`/remove_group <chat_id>`\n\nMisol: `/remove_group -1001234567890`")
        return
    
    try:
        chat_id = int(args.strip())
        
        if not db.is_group_whitelisted(chat_id):
            await message.reply(f"❌ Guruh {chat_id} ruxsat etilganlar ro'yxatida emas.")
            return
        
        success = db.remove_group_from_whitelist(chat_id)
        if success:
            await message.reply(f"✅ **Guruh ruxsat etilganlar ro'yxatidan o'chirildi**\n\n🆔 **ID**: `{chat_id}`\n👨‍💼 **O'chirgan**: {message.from_user.full_name}\n📅 **Sana**: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        else:
            await message.reply(f"❌ Guruhni o'chirishda xatolik yuz berdi.")
            
    except ValueError:
        await message.reply("❌ Noto'g'ri chat ID. Manfiy raqam kiriting (masalan: -1001234567890)")
    except Exception as e:
        logger.error(f"Guruhni o'chirishda xatolik: {e}")
        await message.reply("❌ Tizim xatoligi yuz berdi.")

@dp.message_handler(Command("groups_list"), chat_type=[types.ChatType.PRIVATE, types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def show_whitelisted_groups(message: types.Message):
    """Показать список групп в whitelist"""
    user_id = message.from_user.id
    
    if not is_super_admin(user_id):
        await message.reply("❌ Bu buyruqni bajarish uchun sizda ruxsat yo'q.")
        return
    
    groups = db.get_whitelisted_groups()
    
    if not groups:
        await message.reply("📋 **Ruxsat etilgan guruhlar yo'q**\n\nHech qanday guruh whitelist da emas.")
        return
    
    text = f"📋 **Ruxsat etilgan guruhlar ({len(groups)}):**\n\n"
    
    for group_data in groups:
        chat_id = group_data['chat_id']
        title = group_data['title'] or 'Noma''lum guruh'
        added_date = group_data['added_date'].strftime("%d.%m.%Y %H:%M")
        
        text += f"🏷 **{title}**\n"
        text += f"🆔 ID: `{chat_id}`\n"
        text += f"📅 Qo'shilgan: {added_date}\n"
        text += f"Buyruq: `/remove_group {chat_id}`\n\n"
    
    await message.reply(text, parse_mode='Markdown')
