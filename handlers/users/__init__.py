from .video_selector import dp
from .start import dp
from .user_commands import dp
from .user_registration import dp
from .video_scheduler import dp
from .help import dp
from .admin_image_sender import dp
# Явно импортируем обработчики команд для их регистрации
from .admin_image_sender import (
    set_group_video_command,
    set_group_video_private_command,
    process_project_selection,
    process_centr_season,
    process_golden_season,
    process_centr_video,
    process_golden_video
)
from .security import dp
from .admin_security import dp

__all__ = ["dp"]