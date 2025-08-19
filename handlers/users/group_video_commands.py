from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from handlers import groups
from db import db
from loader import dp
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

# Импортируем необходимые переменные
from data.config import ADMINS, SUPER_ADMIN_ID

logger.info(f"🔄 Регистрируем команды групп в group_video_commands.py, dp ID: {id(dp)}")

# Команда для настройки видео рассылки в группе
@dp.message_handler(commands=['set_group_video'])
async def set_group_video_command(message: types.Message, state: FSMContext):
    """
    Команда для настройки видео рассылки в группе
    """
    logger.info(f"🚀 set_group_video вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    logger.info(f"📝 Текст сообщения: {message.text}")
    
    # Проверяем права пользователя
    user_id = message.from_user.id
    if user_id not in ADMINS + [SUPER_ADMIN_ID] and not db.is_admin(user_id):
        logger.warning(f"❌ Пользователь {user_id} не имеет прав")
        await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.")
        return
    
    logger.info(f"✅ Пользователь {user_id} имеет права")
    
    # Определяем тип чата
    chat_type = message.chat.type
    chat_id = message.chat.id
    
    logger.info(f"Тип чата: {chat_type}, ID чата: {chat_id}")
    
    # Сбрасываем предыдущее состояние
    await state.finish()
    
    if chat_type in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
        logger.info("✅ Это группа, отправляем меню")
        # Команда в группе
        await message.answer(
            "📹 **GURUH UCHUN VIDEO TARQATISH SOZLAMALARI**\n\n"
            "🏢 **Loyihani tanlang:**",
            reply_markup=get_project_keyboard(),
            parse_mode="Markdown"
        )
    else:
        logger.info("⚠️ Это не группа, отправляем личное меню")
        # Команда в личных сообщениях
        await message.answer(
            "📹 **VIDEO TARQATISH SOZLAMALARI**\n\n"
            "🏢 **Loyihani tanlang:**",
            reply_markup=get_project_keyboard(),
            parse_mode="Markdown"
        )
    
    # Импортируем состояния
    from handlers.users.group_video_states import GroupVideoStates
    await state.set_state(GroupVideoStates.waiting_for_project.state)
    await state.update_data(chat_id=chat_id)
    logger.info(f"✅ Состояние установлено, chat_id: {chat_id}")

# Команда для просмотра настроек видео рассылки группы
@dp.message_handler(commands=['show_group_video_settings'])
async def show_group_video_settings(message: types.Message):
    """
    Команда для просмотра текущих настроек видео рассылки в группе
    """
    logger.info(f"🚀 show_group_video_settings вызвана в чате {message.chat.id} ({message.chat.type})")
    logger.info(f"👤 Пользователь: {message.from_user.id} ({message.from_user.username})")
    
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем права пользователя
        if user_id not in ADMINS + [SUPER_ADMIN_ID] and not db.is_admin(user_id):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав")
            await message.answer("❌ **Sizda bu buyruqni bajarish uchun ruxsat yo'q!**\n\nFaqat adminlar foydalana oladi.")
            return
        
        logger.info(f"✅ Пользователь {user_id} имеет права")
        
        # Проверяем, что команда используется в группе
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            logger.warning("⚠️ Команда вызвана не в группе")
            await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi.")
            return
        
        logger.info("✅ Команда вызвана в группе, продолжаем обработку")
        
        # Получаем настройки группы
        settings = db.get_group_video_settings(chat_id)
        if not settings:
            await message.answer(
                "📹 **GURUH VIDEO SOZLAMALARI**\n\n"
                "❌ **Hech qanday sozlamalar topilmadi!**\n\n"
                "Video tarqatishni yoqish uchun /set_group_video buyrug'ini ishlating."
            )
            return
        
        # Получаем стартовые позиции
        centris_start = db.get_group_video_start(chat_id, 'centris')
        golden_start = db.get_group_video_start(chat_id, 'golden')
        
        # Получаем информацию о сезонах
        centris_season_name = "N/A"
        golden_season_name = "N/A"
        
        if settings[1]:  # centris_season
            centris_season_info = db.get_season_by_id(settings[1])
            if centris_season_info:
                centris_season_name = centris_season_info[1]  # season_name
        
        if settings[5]:  # golden_season
            golden_season_info = db.get_season_by_id(settings[5])
            if golden_season_info:
                golden_season_name = golden_season_info[1]  # season_name
        
        # Формируем ответ
        response = "📹 **GURUH VIDEO SOZLAMALARI**\n\n"
        
        # Centris Towers
        response += "🏢 **Centris Towers:**\n"
        if settings[0]:  # centris_enabled
            response += f"   ✅ Yoqilgan\n"
            response += f"   📺 Seson: {centris_season_name}\n"
            response += f"   🎬 Boshlash videosi: {centris_start[1] if centris_start[0] else 0}\n"
        else:
            response += "   ❌ O'chirilgan\n"
        
        response += "\n"
        
        # Golden Lake
        response += "🏘️ **Golden Lake:**\n"
        if settings[4]:  # golden_enabled
            response += f"   ✅ Yoqilgan\n"
            response += f"   📺 Seson: {golden_season_name}\n"
            response += f"   🎬 Boshlash videosi: {golden_start[1] if golden_start[0] else 0}\n"
        else:
            response += "   ❌ O'chirilgan\n"
        
        response += "\n"
        
        # Статус подписки
        is_subscribed = db.get_subscription_status(chat_id)
        response += f"📡 **Obuna holati:** {'✅ Faol' if is_subscribed else '❌ Faol emas'}\n"
        
        # Whitelist статус
        is_whitelisted = db.is_group_whitelisted(chat_id)
        response += f"🔒 **Whitelist:** {'✅ Ruxsat berilgan' if is_whitelisted else '❌ Ruxsat berilmagan'}\n"
        
        # Кнопки управления
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_settings"),
            InlineKeyboardButton("⚙️ O'zgartirish", callback_data="edit_settings")
        )
        
        await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при показе настроек группы: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

logger.info("✅ Команды групп зарегистрированы успешно!")

# Функция для получения клавиатуры выбора проекта
def get_project_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🏢 Centris Towers", callback_data="project_centris"),
        InlineKeyboardButton("🏘️ Golden Lake", callback_data="project_golden"),
        InlineKeyboardButton("🎯 Ikkalasi ham", callback_data="project_both")
    )
    return keyboard

# Обработчики callback-запросов для set_group_video
@dp.callback_query_handler(lambda c: c.data.startswith("project_"), state="*")
async def process_project_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора проекта"""
    try:
        project = callback_query.data.replace("project_", "")
        await state.update_data(project=project)
        
        if project == "centris":
            await callback_query.message.edit_text(
                "🏢 **Centris Towers**\n\n"
                "📺 **Sesonni tanlang:**",
                reply_markup=get_season_keyboard("centris"),
                parse_mode="Markdown"
            )
            from handlers.users.group_video_states import GroupVideoStates
            await state.set_state(GroupVideoStates.waiting_for_centr_season.state)
            
        elif project == "golden":
            seasons = db.get_seasons_by_project("golden")
            if not seasons:
                await callback_query.message.edit_text(
                    "❌ **Golden Lake uchun hech qanday seson topilmadi!**\n\n"
                    "Iltimos, avval seson qo'shing."
                )
                await state.finish()
                return
                
            await callback_query.message.edit_text(
                "🏢 **Golden Lake**\n\n"
                "📺 **Sesonni tanlang:**",
                reply_markup=get_season_keyboard("golden"),
                parse_mode="Markdown"
            )
            from handlers.users.group_video_states import GroupVideoStates
            await state.set_state(GroupVideoStates.waiting_for_golden_season.state)
            
        elif project == "both":
            await callback_query.message.edit_text(
                "🏢 **Centris + Golden**\n\n"
                "📺 **Centris Towers uchun sesonni tanlang:**",
                reply_markup=get_season_keyboard("centris"),
                parse_mode="Markdown"
            )
            from handlers.users.group_video_states import GroupVideoStates
            await state.set_state(GroupVideoStates.waiting_for_centr_season.state)
            await state.update_data(both_selected=True)
            
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при выборе проекта: {e}")
        await callback_query.answer("❌ Xatolik yuz berdi!")

@dp.callback_query_handler(lambda c: c.data.startswith("season_"), state="*")
async def process_season_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора сезона"""
    try:
        if callback_query.data == "no_seasons":
            await callback_query.message.edit_text(
                "❌ **Hech qanday seson topilmadi!**\n\n"
                "Iltimos, avval seson qo'shing."
            )
            await state.finish()
            return
            
        season_id = int(callback_query.data.replace("season_", ""))
        data = await state.get_data()
        project = data.get("project")
        
        if project == "centris" or (project == "both" and data.get("both_selected")):
            await state.update_data(centris_season_id=season_id)
            await callback_query.message.edit_text(
                "🏢 **Centris Towers**\n"
                f"📺 **Seson:** {db.get_season_name(season_id)}\n\n"
                "🎬 **Boshlash uchun videoni tanlang:**",
                reply_markup=get_video_keyboard_from_db(db.get_videos_by_season(season_id), []),
                parse_mode="Markdown"
            )
            from handlers.users.group_video_states import GroupVideoStates
            await state.set_state(GroupVideoStates.waiting_for_centr_video.state)
            
        elif project == "golden":
            await state.update_data(golden_season_id=season_id)
            await callback_query.message.edit_text(
                "🏢 **Golden Lake**\n"
                f"📺 **Seson:** {db.get_season_name(season_id)}\n\n"
                "🎬 **Boshlash uchun videoni tanlang:**",
                reply_markup=get_video_keyboard_from_db(db.get_videos_by_season(season_id), []),
                parse_mode="Markdown"
            )
            from handlers.users.group_video_states import GroupVideoStates
            await state.set_state(GroupVideoStates.waiting_for_golden_video.state)
            
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при выборе сезона: {e}")
        await callback_query.answer("❌ Xatolik yuz berdi!")

@dp.callback_query_handler(lambda c: c.data.startswith("video_"), state="*")
async def process_video_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора видео"""
    try:
        if callback_query.data == "all_videos_sent":
            await callback_query.message.edit_text(
                "❌ **Barcha video allaqachon yuborilgan!**\n\n"
                "Boshqa seson tanlang yoki yangi video qo'shing."
            )
            await state.finish()
            return
            
        video_idx = int(callback_query.data.replace("video_", ""))
        data = await state.get_data()
        project = data.get("project")
        
        if project == "centris" or (project == "both" and data.get("both_selected")):
            await state.update_data(centris_start_video=video_idx)
            
            if data.get("both_selected"):
                # Если выбран оба проекта, переходим к Golden
                await callback_query.message.edit_text(
                    "🏢 **Centris Towers sozlandi!**\n\n"
                    "📺 **Golden Lake uchun sesonni tanlang:**",
                    reply_markup=get_season_keyboard("golden"),
                    parse_mode="Markdown"
                )
                from handlers.users.group_video_states import GroupVideoStates
                await state.set_state(GroupVideoStates.waiting_for_golden_season.state)
            else:
                # Только Centris - сохраняем настройки
                await save_group_settings(data)
                await callback_query.message.edit_text(
                    "✅ **Centris Towers sozlamalari saqlandi!**\n\n"
                    "🎬 Video tarqatish faollashtirildi."
                )
                await state.finish()
                
        elif project == "golden":
            await state.update_data(golden_start_video=video_idx)
            
            if data.get("both_selected"):
                # Оба проекта - сохраняем настройки
                await save_group_settings(data)
                await callback_query.message.edit_text(
                    "✅ **Barcha sozlamalar saqlandi!**\n\n"
                    "🎬 Video tarqatish faollashtirildi."
                )
                await state.finish()
            else:
                # Только Golden - сохраняем настройки
                await save_group_settings(data)
                await callback_query.message.edit_text(
                    "✅ **Golden Lake sozlamalari saqlandi!**\n\n"
                    "🎬 Video tarqatish faollashtirildi."
                )
                await state.finish()
                
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при выборе видео: {e}")
        await callback_query.answer("❌ Xatolik yuz berdi!")

# Вспомогательные функции
def get_season_keyboard(project):
    """Клавиатура для выбора сезона"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    kb = InlineKeyboardMarkup(row_width=2)
    seasons = db.get_seasons_by_project(project)
    if not seasons:
        kb.add(InlineKeyboardButton("❌ Нет сезонов", callback_data="no_seasons"))
        return kb
    
    for season_id, season_name in seasons:
        kb.add(InlineKeyboardButton(f"📺 {season_name}", callback_data=f"season_{season_id}"))
    return kb

def get_video_keyboard_from_db(videos, viewed):
    """Клавиатура для выбора видео"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    kb = InlineKeyboardMarkup(row_width=3)
    has_unwatched = False
    
    for url, title, position in videos:
        if position not in viewed:
            kb.add(InlineKeyboardButton(f"{position+1}. {title}", callback_data=f"video_{position}"))
            has_unwatched = True
    
    if not has_unwatched:
        kb.add(InlineKeyboardButton("❌ Все видео уже отправлены", callback_data="all_videos_sent"))
        return None
    
    return kb

async def save_group_settings(data):
    """Сохранение настроек группы"""
    try:
        chat_id = data.get("chat_id")
        project = data.get("project")
        
        # Определяем какие проекты включены
        centris_enabled = project in ["centris", "both"]
        golden_enabled = project in ["golden", "both"]
        
        # Получаем данные
        centris_season_id = data.get("centris_season_id") if centris_enabled else None
        centris_start_video = data.get("centris_start_video", 0)
        golden_season_id = data.get("golden_season_id") if golden_enabled else None
        golden_start_video = data.get("golden_start_video", 0)
        
        # Сохраняем в базу
        db.set_group_video_settings(
            chat_id,
            int(centris_enabled),
            centris_season_id,
            centris_start_video,
            int(golden_enabled),
            golden_start_video
        )
        
        # Сохраняем стартовые позиции
        if centris_enabled and centris_season_id is not None:
            db.set_group_video_start(chat_id, 'centris', centris_season_id, centris_start_video)
            db.reset_group_viewed_videos(chat_id)
            
        if golden_enabled and golden_season_id is not None:
            db.set_group_video_start(chat_id, 'golden', golden_season_id, golden_start_video)
            db.reset_group_viewed_videos(chat_id)
        
        # Планируем задачи
        from handlers.users.video_scheduler import schedule_group_jobs
        schedule_group_jobs()
        
        logger.info(f"Группа {chat_id}: настройки сохранены - Centris: {centris_enabled}, Golden: {golden_enabled}")
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении настроек группы: {e}")
        raise
