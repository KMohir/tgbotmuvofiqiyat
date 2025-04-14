from aiogram import types


async def set_default_commands(dp):

    await dp.bot.set_my_commands([
        types.BotCommand("start", "Botni ishga tushurish"),
        types.BotCommand("time", "Yangiliklarni soat nechida olishni hohlaysiz?"),
        types.BotCommand("/videos", "FAQ ?"),
        types.BotCommand("contact",'Bino sotip olish'),
        types.BotCommand("about",'Bino sotip olish'),
    ])
