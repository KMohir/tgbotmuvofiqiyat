from aiogram.dispatcher.filters.state import State, StatesGroup


class GroupVideoStates(StatesGroup):
    waiting_for_project = State()
    waiting_for_centr_season = State()
    waiting_for_centr_video = State()
    waiting_for_golden_video = State()
    waiting_for_golden_season = State()
    waiting_for_group_selection = State()
    waiting_for_send_times = State()  # Новое состояние для выбора времени отправки


class AddSeasonStates(StatesGroup):
    waiting_for_project = State()
    waiting_for_season_name = State()
    waiting_for_video_links = State()
    waiting_for_video_titles = State()


class EditSeasonStates(StatesGroup):
    waiting_for_season_id = State()
    waiting_for_new_name = State()
    waiting_for_action = State()  # edit_name, edit_video, delete_video, delete_season


class EditVideoStates(StatesGroup):
    waiting_for_video_id = State()
    waiting_for_new_url = State()
    waiting_for_new_title = State()
    waiting_for_new_position = State()


class SendContentStates(StatesGroup):
    waiting_for_message_id = State()


class DeleteBotMessagesStates(StatesGroup):
    waiting_for_group_selection = State()
    waiting_for_message_count = State()


