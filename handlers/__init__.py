from .users import dp

from . import errors
from . import users
from . import groups
from . import channels

# Импортируем обработчики групп для их регистрации
from .groups import group_handler, group_auto_leave

__all__ = ["dp"]
