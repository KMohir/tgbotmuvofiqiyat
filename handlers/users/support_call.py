from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.types import ReplyKeyboardRemove

from data.config import support_ids
from db import db
from keyboards.default.reply import get_lang_for_button
from keyboards.inline.support import support_keyboard, support_callback, langMenu, cancel_support_callback
from loader import dp, bot
from states.state import RegistrationStates
from translation import _


@dp.message_handler(Text(equals=["/takliflar", "Отправка предложений", "Takliflarni yuborish"]))
async def ask_support(message: types.Message, state: FSMContext):
    if not db.user_exists(message.from_user.id):
        await bot.send_message(
            message.from_user.id,
            'Assalomu aleykum, Centris Towers yordamchi botiga hush kelibsiz!\nЗдравствуйте, добро пожаловать в бот поддержки Centris Towers!'
        )
        await bot.send_message(
            message.from_user.id,
            'Tilni tanlang:\nВыберите язык:',
            reply_markup=langMenu
        )
        await RegistrationStates.lang.set()
        return

    lang = db.get_lang(message.from_user.id)
    user_id = 5657091547  # ID оператора поддержки

    # Создаем клавиатуру с кнопкой "Назад"
    back_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    back_button = types.KeyboardButton(_("Orqaga", lang))
    back_keyboard.add(back_button)

    await message.answer(
        _("Savolingizni yoki murojatingizni 1 ta habar orqali yuboring.", lang),
        reply_markup=back_keyboard
    )
    await state.set_state("wait_for_support_message")
    await state.update_data(second_id=user_id)


@dp.callback_query_handler(support_callback.filter(messages="one"))
async def send_to_support(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    user_id = int(callback_data.get("user_id"))

    lang = db.get_lang(call.from_user.id)
    await call.message.answer(
        _("Savolingizni yoki murojatingizni 1 ta habar orqali yuboring.", lang),
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state("wait_for_support_message")
    await state.update_data(second_id=user_id)


@dp.message_handler(state="wait_for_support_message", content_types=types.ContentTypes.ANY)
async def get_support_message(message: types.Message, state: FSMContext):
    if not db.user_exists(message.from_user.id):
        await message.answer("Пожалуйста, зарегистрируйтесь с помощью команды /start.")
        await state.reset_state()
        return

    data = await state.get_data()
    second_id = data.get("second_id")
    lang = db.get_lang(message.from_user.id)

    # Проверяем, нажал ли пользователь "Назад"
    if message.text in [_("Orqaga", lang), _("Назад", lang)]:
        await message.answer(
            _("Operatsiya bekor qilindi", lang),
            reply_markup=get_lang_for_button(message)
        )
        await state.reset_state()
        return

    # Уведомляем пользователя, что сообщение отправлено
    await message.answer(
        _('Savolingiz / Murojatingiz bizning operatorlarga yuborildi, yaqin orada sizga javob beramiz!', lang),
        reply_markup=ReplyKeyboardRemove()
    )

    # Получаем данные пользователя
    name = db.get_name(message.from_user.id)
    phone = db.get_phone(message.from_user.id)

    # Отправляем сообщение оператору и в группу
    for support_id in support_ids:
        if str(second_id) == support_id:
            try:
                keyboard = await support_keyboard(message, messages="one", user_id=message.from_user.id)
                db.add_questions(message.from_user.id, message.message_id)
                a = db.get_id()

                if message.text is None:  # Если это не текст (например, фото или видео)
                    await message.copy_to(
                        second_id,
                        caption=f"Raqami: {a}\nI.SH.: {name}\nUsername: @{message.from_user.username}\nNomer: <code>{phone}</code>\nHabar: {message.caption or 'Без текста'}",
                        reply_markup=keyboard
                    )
                    await message.copy_to(
                        -1002601209038,  # ID группы
                        caption=f"Raqami: {a}\nI.SH.: {name}\nUsername: @{message.from_user.username}\nNomer: <code>{phone}</code>\nHabar: {message.caption or 'Без текста'}",
                        reply_markup=keyboard
                    )
                else:  # Если это текстовое сообщение
                    await bot.send_message(
                        second_id,
                        f"Raqami: {a}\nI.SH.: {name}\nUsername: @{message.from_user.username}\nNomer: <code>{phone}</code>\nHabar: {message.text}",
                        reply_markup=keyboard
                    )
                    await bot.send_message(
                        -1002601209038,
                        f"Raqami: {a}\nI.SH.: {name}\nUsername: @{message.from_user.username}\nNomer: <code>{phone}</code>\nHabar: {message.text}"
                    )
            except Exception as e:
                print(f"Error sending to support: {e}")
                continue
        else:
            # Логика для ответа на предыдущее сообщение
            db.add_questions(message.from_user.id, message.message_id)
            reply = db.get_question(second_id)
            keyboard = await support_keyboard(message, messages="one", user_id=message.from_user.id)
            try:
                if message.text is None:
                    await message.copy_to(
                        second_id,
                        reply_to_message_id=reply,
                        caption=message.caption or "Без текста"
                    )
                else:
                    await bot.send_message(
                        second_id,
                        message.text,
                        reply_to_message_id=reply
                    )
            except Exception as e:
                print(f"Error replying to support: {e}")

            lang = db.get_lang(second_id)
            await bot.send_message(
                second_id,
                _("Yana savolingiz yoki murojatingiz bo'lsa, /taklif orqali berishingiz mumkin.", lang),
                reply_markup=get_lang_for_button(message)
            )

    await state.reset_state()


@dp.callback_query_handler(cancel_support_callback.filter(), state=["in_support", "wait_in_support", None])
async def exit_support(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    user_id = int(callback_data.get("user_id"))
    second_state = dp.current_state(user=user_id, chat=user_id)

    if await second_state.get_state() is not None:
        data_second = await second_state.get_data()
        second_id = data_second.get("second_id")
        if int(second_id) == call.from_user.id:
            await second_state.reset_state()
            await bot.send_message(user_id, "Пользователь завершил сеанс техподдержки")

    await call.message.answer("Centris Towers bu sizni bilimingzini sinash uchun qilingan platforma")
    await state.reset_state()


@dp.message_handler(Text(equals=["/about", "Centris Towers haqida bilish", "Узнать про Centris Towers"]))
async def bot_help(message: types.Message):
    if not db.user_exists(message.from_user.id):
        await message.answer("Пожалуйста, зарегистрируйтесь с помощью команды /start.")
        return

    video_path = 'Centris.mp4'
    lang = db.get_lang(message.from_user.id)
    caption = _(
        "Centris Tower - innovatsiya va zamonaviy uslub gullab-yashnaydigan yangi avlod biznes markazi\n\nMuvaffaqiyatli biznesingizning kaliti bo'ladigan hashamatli ish joyingizni kashf eting.",
        lang
    )

    with open(video_path, 'rb') as video:
        await bot.send_video(
            chat_id=message.chat.id,
            video=video,
            caption=caption,  # Исправлено: caption теперь передаётся
            supports_streaming=True,
            reply_markup=get_lang_for_button(message)
        )