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

@dp.message_handler(lambda message: message.text and not message.text.startswith('/'), state=None)
async def bot_echo(message: types.Message):
    if not db.user_exists(message.from_user.id):
        await message.answer("Iltimos, /start buyrug'i bilan ro'yxatdan o'ting.")
        return

    await message.answer("Iltimos operator javobini kuting!")

@dp.message_handler(
    lambda message: not message.text.startswith('/'),
    state="*",
    content_types=types.ContentTypes.ANY
)
async def bot_echo_all(message: types.Message, state: FSMContext):
    if not db.user_exists(message.from_user.id):
        await message.answer("Iltimos, /start buyrug'i bilan ro'yxatdan o'ting.")
        return

    current_state = await state.get_state()
    print(f"echo.py: Текущее состояние пользователя {message.from_user.id}: {current_state}")
    print(f"echo.py: EXCLUDED_STATES: {EXCLUDED_STATES}")
    if current_state in EXCLUDED_STATES:
        print(f"echo.py: Сообщение от {message.from_user.id} пропущено, состояние: {current_state}")
        return

    await message.answer("Pastdagi tugmani bosing")