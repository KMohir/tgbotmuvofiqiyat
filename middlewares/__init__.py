from aiogram import Dispatcher

from .security import VideoSecurityMiddleware


def setup(dp: Dispatcher):
    dp.middleware.setup(VideoSecurityMiddleware())
