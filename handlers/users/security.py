"""
Обработчики безопасности для регистрации пользователей
"""

import logging
from datetime import datetime
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from loader import dp, bot
from db import db
from states import SecurityStates
from data.config import ADMINS, SUPER_ADMIN_ID
from keyboards.default.reply import main_menu_keyboard

logger = logging.getLogger(__name__)

async def notify_admins_about_registration(user_id: int, name: str, phone: str):
    """Уведомить админов о новой регистрации"""
    try:
        message_text = (
            "🔐 **Yangi ro'yxatdan o'tish so'rovi**\n\n"
            f"👤 **Foydalanuvchi**: {name}\n"
            f"🆔 **ID**: `{user_id}`\n"
            f"📱 **Telefon**: {phone}\n\n"
            "Harakatni tanlang:"
        )
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_user_{user_id}"),
            types.InlineKeyboardButton("❌ Rad etish", callback_data=f"deny_user_{user_id}")
        )
        
        admin_ids = [SUPER_ADMIN_ID]
        for admin in ADMINS:
            try:
                if isinstance(admin, str):
                    admin_ids.append(int(admin.strip()))
                elif isinstance(admin, int):
                    admin_ids.append(admin)
            except (ValueError, AttributeError):
                continue
        
        for admin_id in admin_ids:
            try:
                await bot.send_message(admin_id, message_text, reply_markup=keyboard, parse_mode='Markdown')
            except Exception as e:
                logger.warning(f"Adminga {admin_id} xabar yuborib bo'lmadi: {e}")
                
    except Exception as e:
        logger.error(f"Adminlarga ro'yxatdan o'tish haqida xabar yuborishda xatolik: {e}")

@dp.message_handler(Command("start"), chat_type=types.ChatType.PRIVATE, state="*")
async def security_start_registration(message: types.Message, state: FSMContext):
    """Обработка команды /start в приватном чате с проверкой регистрации"""
    user_id = message.from_user.id
    security_status = db.get_user_security_status(user_id)
    
    if security_status == 'approved':
        await message.answer("🎬 **Centris Towers & Golden Lake Botiga xush kelibsiz!**\n\nO'zingizga yoqqan loyihani tanlang:", reply_markup=main_menu_keyboard())
        await state.finish()
    elif security_status == 'pending':
        await message.answer("⏳ **Sizning arizangiz ko'rib chiqilmoqda**\n\nAdministrator hali sizning arizangizni ko'rib chiqmagan.\nIltimos, tasdiqlashni kuting.")
        await state.finish()
    elif security_status == 'denied':
        await message.answer("❌ **Kirish taqiqlangan**\n\nSizning arizangiz administrator tomonidan rad etildi.\nMa'lumot olish uchun qo'llab-quvvatlash xizmatiga murojaat qiling.")
        await state.finish()
    else:
        await message.answer("🔐 **Tizimda ro'yxatdan o'tish**\n\nBotga kirish uchun ro'yxatdan o'tish kerak.\n\n**1-qadam, 2 tadan**\n📝 Ismingizni kiriting:")
        await SecurityStates.waiting_name.set()

@dp.message_handler(state=SecurityStates.waiting_name, chat_type=types.ChatType.PRIVATE)
async def process_registration_name(message: types.Message, state: FSMContext):
    """Обработка ввода имени"""
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("❌ **Ism juda qisqa**\n\nIltimos, to'g'ri ism kiriting (kamida 2 ta belgi):")
        return
        
    if len(name) > 100:
        await message.answer("❌ **Ism juda uzun**\n\nIltimos, 100 belgidan kam bo'lgan ism kiriting:")
        return
    
    await state.update_data(name=name)
    await message.answer(f"✅ **Ism saqlandi**: {name}\n\n**2-qadam, 2 tadan**\n📱 Telefon raqamingizni kiriting:")
    await SecurityStates.waiting_phone.set()

@dp.message_handler(state=SecurityStates.waiting_phone, chat_type=types.ChatType.PRIVATE)
async def process_registration_phone(message: types.Message, state: FSMContext):
    """Обработка ввода телефона и завершение регистрации"""
    phone = message.text.strip()
    
    if len(phone) < 9:
        await message.answer("❌ **Telefon raqami noto'g'ri**\n\nIltimos, to'g'ri telefon raqamini kiriting:")
        return
        
    if len(phone) > 20:
        await message.answer("❌ **Telefon raqami juda uzun**\n\nIltimos, 20 belgidan kam raqam kiriting:")
        return
    
    data = await state.get_data()
    name = data.get('name')
    user_id = message.from_user.id
    
    db.add_user_registration(user_id, name, phone)
    
    await message.answer("✅ **Ro'yxatdan o'tish yakunlandi!**\n\n" + 
                        f"👤 **Ism**: {name}\n" +
                        f"📱 **Telefon**: {phone}\n\n" +
                        "⏳ **Sizning arizangiz ko'rib chiqilish uchun yuborildi**\n\n" +
                        "Administrator sizning arizangizni yaqin vaqtda ko'rib chiqadi.\n" +
                        "Qaror haqida xabar olasiz.")
    
    await notify_admins_about_registration(user_id, name, phone)
    await state.finish()
    logger.info(f"Foydalanuvchi {user_id} ro'yxatdan o'tishni yakunladi: {name}, {phone}")

@dp.callback_query_handler(lambda c: c.data.startswith('approve_user_'))
async def process_approve_user(callback_query: types.CallbackQuery):
    """Обработка одобрения пользователя админом"""
    admin_id = callback_query.from_user.id
    
    admin_ids = [SUPER_ADMIN_ID]
    for admin in ADMINS:
        try:
            if isinstance(admin, str):
                admin_ids.append(int(admin.strip()))
            elif isinstance(admin, int):
                admin_ids.append(admin)
        except (ValueError, AttributeError):
            continue
    
    if not (admin_id in admin_ids):
        await callback_query.answer("❌ Sizda administrator huquqi yo'q", show_alert=True)
        return
    
    try:
        user_id = int(callback_query.data.replace('approve_user_', ''))
        user_data = db.get_user_security_data(user_id)
        if not user_data:
            await callback_query.answer("❌ Foydalanuvchi ma'lumotlari topilmadi", show_alert=True)
            return
        
        success = db.approve_user(user_id, admin_id)
        if success:
            try:
                await bot.send_message(user_id, "✅ **Tabriklaymiz! Sizning arizangiz tasdiqlandi**\n\nEndi botga kirishingiz mumkin.\nIshlashni boshlash uchun /start buyrug'ini yuboring.")
            except Exception as e:
                logger.warning(f"Foydalanuvchiga {user_id} xabar yuborib bo'lmadi: {e}")
            
            await callback_query.message.edit_text(
                f"✅ **Foydalanuvchi tasdiqlandi**\n\n" +
                f"👤 **Ism**: {user_data['name']}\n" +
                f"🆔 **ID**: `{user_id}`\n" +
                f"📱 **Telefon**: {user_data['phone']}\n" +
                f"👨‍💼 **Tasdiqlagan**: {callback_query.from_user.full_name}\n" +
                f"📅 **Sana**: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                parse_mode='Markdown'
            )
            await callback_query.answer("✅ Foydalanuvchi muvaffaqiyatli tasdiqlandi")
        else:
            await callback_query.answer("❌ Foydalanuvchini tasdiqlashda xatolik", show_alert=True)
    except Exception as e:
        logger.error(f"Foydalanuvchini tasdiqlashda xatolik: {e}")
        await callback_query.answer("❌ Tizim xatoligi", show_alert=True)

@dp.callback_query_handler(lambda c: c.data.startswith('deny_user_'))
async def process_deny_user(callback_query: types.CallbackQuery):
    """Обработка отклонения пользователя админом"""
    admin_id = callback_query.from_user.id
    
    admin_ids = [SUPER_ADMIN_ID]
    for admin in ADMINS:
        try:
            if isinstance(admin, str):
                admin_ids.append(int(admin.strip()))
            elif isinstance(admin, int):
                admin_ids.append(admin)
        except (ValueError, AttributeError):
            continue
    
    if not (admin_id in admin_ids):
        await callback_query.answer("❌ Sizda administrator huquqi yo'q", show_alert=True)
        return
    
    try:
        user_id = int(callback_query.data.replace('deny_user_', ''))
        user_data = db.get_user_security_data(user_id)
        if not user_data:
            await callback_query.answer("❌ Foydalanuvchi ma'lumotlari topilmadi", show_alert=True)
            return
        
        success = db.deny_user(user_id, admin_id)
        if success:
            try:
                await bot.send_message(user_id, "❌ **Sizning arizangiz rad etildi**\n\nAdministrator sizning ro'yxatdan o'tish arizangizni rad etdi.\nQo'shimcha ma'lumot olish uchun qo'llab-quvvatlash xizmatiga murojaat qiling.")
            except Exception as e:
                logger.warning(f"Foydalanuvchiga {user_id} xabar yuborib bo'lmadi: {e}")
            
            await callback_query.message.edit_text(
                f"❌ **Foydalanuvchi rad etildi**\n\n" +
                f"👤 **Ism**: {user_data['name']}\n" +
                f"🆔 **ID**: `{user_id}`\n" +
                f"📱 **Telefon**: {user_data['phone']}\n" +
                f"👨‍💼 **Rad etgan**: {callback_query.from_user.full_name}\n" +
                f"📅 **Sana**: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                parse_mode='Markdown'
            )
            await callback_query.answer("✅ Foydalanuvchi rad etildi")
        else:
            await callback_query.answer("❌ Foydalanuvchini rad etishda xatolik", show_alert=True)
    except Exception as e:
        logger.error(f"Foydalanuvchini rad etishda xatolik: {e}")
        await callback_query.answer("❌ Tizim xatoligi", show_alert=True)
