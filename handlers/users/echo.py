from datetime import datetime, timedelta

try:
    from aiogram import types
    from aiogram.dispatcher import FSMContext
    from db import db
    from loader import dp
    from states.state import TimeSelection, RegistrationStates, answer, questions, language, ImageCollection

    # Список состояний, которые нужно исключить из обработки
    EXCLUDED_STATES = [
        "TimeSelection:time",  # Указываем состояние напрямую как строку
        RegistrationStates.name.state,
        RegistrationStates.phone.state,
        RegistrationStates.end.state,
        RegistrationStates.number.state,
        RegistrationStates.help.state,
        RegistrationStates.contact.state,
        RegistrationStates.waiting_for_parameters.state,
        RegistrationStates.waiting_for_file.state,
        RegistrationStates.address.state,
        RegistrationStates.status.state,
        RegistrationStates.employees.state,
        RegistrationStates.custom_status.state,
        answer.A1.state,
        answer.A2.state,
        questions.answer.state,
        language.lang.state,
        ImageCollection.waiting_for_images.state,
    ]

    @dp.message_handler(lambda message: message.text and not message.text.startswith('/'), state=None, chat_type=types.ChatType.PRIVATE)
    async def bot_echo(message: types.Message):
        if not db.user_exists(message.from_user.id):
            await message.answer("Iltimos, /start buyrug'i bilan ro'yxatdan o'ting.")
            return

        await message.answer("Iltimos operator javobini kuting!")

    @dp.message_handler(
        lambda message: not message.text.startswith('/'),
        state="*",
        content_types=types.ContentTypes.ANY,
        chat_type=types.ChatType.PRIVATE
    )
    async def bot_echo_all(message: types.Message, state: FSMContext):
        if not db.user_exists(message.from_user.id):
            await message.answer("Iltimos, /start buyrug'i bilan ro'yxatdan o'ting.")
            return

        current_state = await state.get_state()

        if current_state in EXCLUDED_STATES:

            return

        await message.answer("Pastdagi tugmani bosing")

except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('echo ',  f"{time}formatted_date_time",f"error {exx}" )