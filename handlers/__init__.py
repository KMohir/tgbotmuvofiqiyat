from .users import dp
from . import users
from . import groups

# Импортируем обработчики групп для их регистрации
from .groups import group_handler

__all__ = ["dp"]
