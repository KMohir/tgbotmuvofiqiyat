from .help import dp
from .support import dp
from .support_call import dp
from .start import dp
from .user_registration import dp  # Новый файл
from .user_commands import dp      # Новый файл
from .media_handler import dp      # Новый файл
from .language_selection import dp # Новый файл
from .admin_image_sender import dp # Новый файл
from .video_scheduler import dp    # Новый файл
from .time import dp
from .video_selector import dp
from .subscription import dp

from .echo import dp
__all__ = ["dp"]