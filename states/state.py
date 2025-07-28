from aiogram.dispatcher.filters.state import StatesGroup, State


class answer(StatesGroup):
    A1 = State()
    A2 = State()


class language(StatesGroup):
    lang = State()


class questions(StatesGroup):
    answer = State()


class RegistrationStates(StatesGroup):
    lang = State()
    name = State()
    phone = State()
    end = State()
    number = State()
    help = State()
    contact = State()
    waiting_for_parameters = State()  # Ожидание ввода параметров A, B, C, X, Y, Z
    waiting_for_file = State()        # Ожидание загрузки Excel-файла
    address = State()
    status = State()
    employees = State()
    custom_status = State()


class TimeSelection(StatesGroup):
    time = State()


class ImageCollection(StatesGroup):
    waiting_for_images = State()

# === СОСТОЯНИЯ БЕЗОПАСНОСТИ ===

class SecurityStates(StatesGroup):
    waiting_name = State()
    waiting_phone = State()

class GroupManagement(StatesGroup):
    waiting_group_id = State()
    waiting_group_title = State()

class AdminSecurityStates(StatesGroup):
    waiting_user_id_approve = State()
    waiting_user_id_deny = State()
    waiting_group_id_add = State()
    waiting_group_id_remove = State()