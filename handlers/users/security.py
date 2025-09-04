"""
Система безопасности для Telegram бота
"""

import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.utils.exceptions import InvalidQueryID
from loader import dp, bot
from db import db
from data.config import ADMINS
from datetime import datetime
from states.security_states import SecurityStates

logger = logging.getLogger(__name__)

# Список супер-администраторов
SUPER_ADMIN_IDS = [5657091547, 7983512278, 5310261745]

async def send_updated_approval_message(admin_id: int, user_id: int, user_data: dict, action_type: str = "pending"):
    """Отправить обновленное сообщение для одобрения/отклонения пользователя"""
    try:
        if action_type == "pending":
            message_text = (
                f"🆕 **Yangi ro'yxatdan o'tish arizasi** (Yangilandi)\n\n"
                f"👤 **Ism**: {user_data['name']}\n"
                f"🆔 **ID**: `{user_id}`\n"
                f"📱 **Telefon**: {user_data['phone']}\n"
                f"📅 **Sana**: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                f"⚠️ **Eslatma**: Oldingi tugmalar eskirgan. Yangi tugmalardan foydalaning:\n\n"
                f"Tasdiqlash yoki rad etish uchun quyidagi tugmalardan birini bosing:"
            )
            
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_user_{user_id}"),
                types.InlineKeyboardButton("❌ Rad etish", callback_data=f"deny_user_{user_id}")
            )
            
            await bot.send_message(admin_id, message_text, reply_markup=keyboard, parse_mode='Markdown')
            return True
    except Exception as e:
        logger.error(f"Yangilangan tasdiqlash xabarini yuborishda xatolik: {e}")
        return False

async def notify_admins_about_registration(user_id: int, name: str, phone: str):
    """Уведомить админов о новой регистрации"""
    try:
        message_text = (
            f"🆕 **Yangi ro'yxatdan o'tish arizasi**\n\n"
            f"👤 **Ism**: {name}\n"
            f"🆔 **ID**: `{user_id}`\n"
            f"📱 **Telefon**: {phone}\n"
            f"📅 **Sana**: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Tasdiqlash yoki rad etish uchun quyidagi tugmalardan birini bosing:"
        )
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_user_{user_id}"),
            types.InlineKeyboardButton("❌ Rad etish", callback_data=f"deny_user_{user_id}")
        )
        
        admin_ids = SUPER_ADMIN_IDS
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
        await message.answer("🎬 **Centris Towers & Golden Lake Botiga xush kelibsiz!**\n\nO'zingizga yoqqan loyihani tanlang:", reply_markup=main_menu_keyboard(), parse_mode="Markdown")
        await state.finish()
    elif security_status == 'pending':
        await message.answer("⏳ **Sizning arizangiz ko'rib chiqilmoqda**\n\nAdministrator hali sizning arizangizni ko'rib chiqmagan.\nIltimos, tasdiqlashni kuting.", parse_mode="Markdown")
        await state.finish()
    elif security_status == 'denied':
        await message.answer("❌ **Kirish taqiqlangan**\n\nSizning arizangiz administrator tomonidan rad etildi.\nMa'lumot olish uchun qo'llab-quvvatlash xizmatiga murojaat qiling.", parse_mode="Markdown")
        await state.finish()
    else:
        await message.answer("🔐 **Tizimda ro'yxatdan o'tish**\n\nBotga kirish uchun ro'yxatdan o'tish kerak.\n\n**1-qadam, 2 tadan**\n📝 Ismingizni kiriting:", parse_mode="Markdown")
        await SecurityStates.waiting_name.set()

@dp.message_handler(state=SecurityStates.waiting_name, chat_type=types.ChatType.PRIVATE)
async def process_registration_name(message: types.Message, state: FSMContext):
    """Обработка ввода имени"""
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("❌ **Ism juda qisqa**\n\nIltimos, to'g'ri ism kiriting (kamida 2 ta belgi):", parse_mode="Markdown")
        return
        
    if len(name) > 100:
        await message.answer("❌ **Ism juda uzun**\n\nIltimos, 100 belgidan kam bo'lgan ism kiriting:", parse_mode="Markdown")
        return
    
    await state.update_data(name=name)
    await message.answer(f"✅ **Ism saqlandi**: {name}\n\n**2-qadam, 2 tadan**\n📱 Telefon raqamingizni kiriting:", parse_mode="Markdown")
    await SecurityStates.waiting_phone.set()

@dp.message_handler(state=SecurityStates.waiting_phone, chat_type=types.ChatType.PRIVATE)
async def process_registration_phone(message: types.Message, state: FSMContext):
    """Обработка ввода телефона и завершение регистрации"""
    phone = message.text.strip()
    
    if len(phone) < 9:
        await message.answer("❌ **Telefon raqami noto'g'ri**\n\nIltimos, to'g'ri telefon raqamini kiriting:", parse_mode="Markdown")
        return
        
    if len(phone) > 20:
        await message.answer("❌ **Telefon raqami juda uzun**\n\nIltimos, 20 belgidan kam raqam kiriting:", parse_mode="Markdown")
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
                        "Qaror haqida xabar olasiz.", parse_mode="Markdown")
    
    await notify_admins_about_registration(user_id, name, phone)
    await state.finish()
    logger.info(f"Foydalanuvchi {user_id} ro'yxatdan o'tishni yakunladi: {name}, {phone}")

@dp.callback_query_handler(lambda c: c.data.startswith('approve_user_'))
async def process_approve_user(callback_query: types.CallbackQuery):
    """Обработка одобрения пользователя админом"""
    admin_id = callback_query.from_user.id
    
    admin_ids = SUPER_ADMIN_IDS.copy()
    for admin in ADMINS:
        try:
            if isinstance(admin, str):
                admin_ids.append(int(admin.strip()))
            elif isinstance(admin, int):
                admin_ids.append(admin)
        except (ValueError, AttributeError):
            continue
    
    if not (admin_id in admin_ids):
        try:
            await callback_query.answer("❌ Sizda administrator huquqi yo'q", show_alert=True)
        except InvalidQueryID:
            logger.warning(f"Callback query {callback_query.id} is too old, admin rights check failed for {admin_id}")
            # Отправляем сообщение о недостатке прав
            try:
                await bot.send_message(admin_id, f"❌ **Ruxsat rad etildi**\n\n⚠️ **Eslatma**: Tugma eskirgan. Sizda administrator huquqi yo'q.", parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Adminga {admin_id} ma'lumot xabarini yuborib bo'lmadi: {e}")
        return
    
    try:
        user_id = int(callback_query.data.replace('approve_user_', ''))
        user_data = db.get_user_security_data(user_id)
        if not user_data:
            try:
                await callback_query.answer("❌ Foydalanuvchi ma'lumotlari topilmadi", show_alert=True)
            except InvalidQueryID:
                logger.warning(f"Callback query {callback_query.id} is too old, user {user_id} not found")
                # Отправляем сообщение о том, что пользователь не найден
                try:
                    await bot.send_message(admin_id, f"❌ **Foydalanuvchi topilmadi**\n\n🆔 **ID**: `{user_id}`\n\n⚠️ **Eslatma**: Tugma eskirgan va foydalanuvchi ma'lumotlari topilmadi.", parse_mode='Markdown')
                except Exception as e:
                    logger.error(f"Adminga {admin_id} ma'lumot xabarini yuborib bo'lmadi: {e}")
            return
        
        success = db.approve_user(user_id, admin_id)
        if success:
            try:
                await bot.send_message(user_id, "✅ **Tabriklaymiz! Sizning arizangiz tasdiqlandi**\n\nEndi botga kirishingiz mumkin.\nIshlashni boshlash uchun /start buyrug'ini yuboring.")
            except Exception as e:
                logger.warning(f"Foydalanuvchiga {user_id} xabar yuborib bo'lmadi: {e}")
            
            try:
                await callback_query.message.edit_text(
                    f"✅ **Foydalanuvchi tasdiqlandi**\n\n" +
                    f"👤 **Ism**: {user_data['name']}\n" +
                    f"🆔 **ID**: `{user_id}`\n" +
                    f"📱 **Telefon**: {user_data['phone']}\n" +
                    f"👨‍💼 **Tasdiqlagan**: {callback_query.from_user.full_name}\n" +
                    f"📅 **Sana**: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                    parse_mode='Markdown'
                )
            except Exception as edit_error:
                logger.warning(f"Не удалось отредактировать сообщение: {edit_error}")
                # Если не удалось отредактировать, просто отвечаем на callback
                pass
            try:
                await callback_query.answer("✅ Foydalanuvchi muvaffaqiyatli tasdiqlandi")
            except InvalidQueryID:
                logger.warning(f"Callback query {callback_query.id} is too old, but user {user_id} was approved successfully")
                # Отправляем администратору информационное сообщение
                try:
                    await bot.send_message(admin_id, f"✅ **Foydalanuvchi tasdiqlandi**\n\n👤 **Ism**: {user_data['name']}\n🆔 **ID**: `{user_id}`\n\n⚠️ **Eslatma**: Tugma eskirgan edi, lekin amal bajarildi.", parse_mode='Markdown')
                except Exception as e:
                    logger.error(f"Adminga {admin_id} ma'lumot xabarini yuborib bo'lmadi: {e}")
        else:
            try:
                await callback_query.answer("❌ Foydalanuvchini tasdiqlashda xatolik", show_alert=True)
            except InvalidQueryID:
                logger.warning(f"Callback query {callback_query.id} is too old, approval failed for user {user_id}")
                # Отправляем новое сообщение для повторной попытки
                await send_updated_approval_message(admin_id, user_id, user_data)
    except Exception as e:
        logger.error(f"Foydalanuvchini tasdiqlashda xatolik: {e}")
        try:
            await callback_query.answer("❌ Tizim xatoligi", show_alert=True)
        except InvalidQueryID:
            logger.warning(f"Callback query {callback_query.id} is too old, system error during approval")
            # Отправляем новое сообщение для повторной попытки
            user_data = db.get_user_security_data(user_id) if 'user_id' in locals() else None
            if user_data:
                await send_updated_approval_message(admin_id, user_id, user_data)

@dp.callback_query_handler(lambda c: c.data.startswith('deny_user_'))
async def process_deny_user(callback_query: types.CallbackQuery):
    """Обработка отклонения пользователя админом"""
    admin_id = callback_query.from_user.id
    
    admin_ids = SUPER_ADMIN_IDS.copy()
    for admin in ADMINS:
        try:
            if isinstance(admin, str):
                admin_ids.append(int(admin.strip()))
            elif isinstance(admin, int):
                admin_ids.append(admin)
        except (ValueError, AttributeError):
            continue
    
    if not (admin_id in admin_ids):
        try:
            await callback_query.answer("❌ Sizda administrator huquqi yo'q", show_alert=True)
        except InvalidQueryID:
            logger.warning(f"Callback query {callback_query.id} is too old, admin rights check failed for {admin_id}")
            # Отправляем сообщение о недостатке прав
            try:
                await bot.send_message(admin_id, f"❌ **Ruxsat rad etildi**\n\n⚠️ **Eslatma**: Tugma eskirgan. Sizda administrator huquqi yo'q.", parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Adminga {admin_id} ma'lumot xabarini yuborib bo'lmadi: {e}")
        return
    
    try:
        user_id = int(callback_query.data.replace('deny_user_', ''))
        user_data = db.get_user_security_data(user_id)
        if not user_data:
            try:
                await callback_query.answer("❌ Foydalanuvchi ma'lumotlari topilmadi", show_alert=True)
            except InvalidQueryID:
                logger.warning(f"Callback query {callback_query.id} is too old, user {user_id} not found for denial")
            return
        
        success = db.deny_user(user_id, admin_id)
        if success:
            try:
                await bot.send_message(user_id, "❌ **Sizning arizangiz rad etildi**\n\nAdministrator sizning ro'yxatdan o'tish arizangizni rad etdi.\nQo'shimcha ma'lumot olish uchun qo'llab-quvvatlash xizmatiga murojaat qiling.")
            except Exception as e:
                logger.warning(f"Foydalanuvchiga {user_id} xabar yuborib bo'lmadi: {e}")
            
            try:
                await callback_query.message.edit_text(
                    f"❌ **Foydalanuvchi rad etildi**\n\n" +
                    f"👤 **Ism**: {user_data['name']}\n" +
                    f"🆔 **ID**: `{user_id}`\n" +
                    f"📱 **Telefon**: {user_data['phone']}\n" +
                    f"👨‍💼 **Rad etgan**: {callback_query.from_user.full_name}\n" +
                    f"📅 **Sana**: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                    parse_mode='Markdown'
                )
            except Exception as edit_error:
                logger.warning(f"Не удалось отредактировать сообщение: {edit_error}")
                # Если не удалось отредактировать, просто отвечаем на callback
                pass
            try:
                await callback_query.answer("✅ Foydalanuvchi rad etildi")
            except InvalidQueryID:
                logger.warning(f"Callback query {callback_query.id} is too old, but user {user_id} was denied successfully")
                # Отправляем администратору информационное сообщение
                try:
                    await bot.send_message(admin_id, f"❌ **Foydalanuvchi rad etildi**\n\n👤 **Ism**: {user_data['name']}\n🆔 **ID**: `{user_id}`\n\n⚠️ **Eslatma**: Tugma eskirgan edi, lekin amal bajarildi.", parse_mode='Markdown')
                except Exception as e:
                    logger.error(f"Adminga {admin_id} ma'lumot xabarini yuborib bo'lmadi: {e}")
        else:
            try:
                await callback_query.answer("❌ Foydalanuvchini rad etishda xatolik", show_alert=True)
            except InvalidQueryID:
                logger.warning(f"Callback query {callback_query.id} is too old, denial failed for user {user_id}")
                # Отправляем новое сообщение для повторной попытки
                await send_updated_approval_message(admin_id, user_id, user_data)
    except Exception as e:
        logger.error(f"Foydalanuvchini rad etishda xatolik: {e}")
        try:
            await callback_query.answer("❌ Tizim xatoligi", show_alert=True)
        except InvalidQueryID:
            logger.warning(f"Callback query {callback_query.id} is too old, system error during denial")
            # Отправляем новое сообщение для повторной попытки
            user_data = db.get_user_security_data(user_id) if 'user_id' in locals() else None
            if user_data:
                await send_updated_approval_message(admin_id, user_id, user_data)

def main_menu_keyboard():
    """Клавиатура главного меню"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🏢 Centris Towers", callback_data="project_centris"),
        types.InlineKeyboardButton("🌊 Golden Lake", callback_data="project_golden")
    )
    return keyboard
