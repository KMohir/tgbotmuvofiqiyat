from aiogram import Dispatcher

from .throttling import ThrottlingMiddleware
from .security import VideoSecurityMiddleware


def setup(dp: Dispatcher):
    dp.middleware.setup(ThrottlingMiddleware())
    dp.middleware.setup(VideoSecurityMiddleware())
