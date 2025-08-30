# Импортируем все обработчики для их регистрации
from . import video_selector
from . import start  
from . import user_commands
from . import user_registration
from . import video_scheduler
from . import help
from . import admin_image_sender
from . import group_video_commands
from . import security
from . import admin_security

# Импортируем dp из одного модуля
from tgbotmuvofiqiyat.loader import dp

__all__ = ["dp"]