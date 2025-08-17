from aiogram import types


async def set_default_commands(dp):

    await dp.bot.set_my_commands([
        types.BotCommand("start", "Botni ishga tushurish"),
        types.BotCommand("centris_towers", "Centris Towers videolar ni korish"),
        types.BotCommand("golden_lake","Golden lake videolarini korish"),
        types.BotCommand("about",'Bino bilan tanishish'),
        types.BotCommand("set_group_video", "Guruh uchun video tarqatish sozlamalari"),
    ])
