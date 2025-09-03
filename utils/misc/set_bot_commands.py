from aiogram import types


async def set_default_commands(dp):

    await dp.bot.set_my_commands([
        types.BotCommand("start", "Botni ishga tushurish"),
        types.BotCommand("centris_towers", "Centris Towers videolar ni korish"),
        types.BotCommand("golden_lake","Golden lake videolarini korish"),
        types.BotCommand("about",'Bino bilan tanishish'),
        types.BotCommand("set_group_video", "Guruh uchun video tarqatish sozlamalari"),
        types.BotCommand("show_group_video_settings", "Guruh video sozlamalarini ko'rish"),
        types.BotCommand("update_video_progress", "Video progress yangilash (admin)"),
        types.BotCommand("auto_update_progress", "Avtomatik progress yangilash (admin)"),
        types.BotCommand("update_group_names", "Guruh nomlarini yangilash (admin)"),
        types.BotCommand("test_send_video_all_groups", "Test video yuborish (admin)"),
        types.BotCommand("send_all_planned_videos", "Barcha rejalashtirilgan videolar (admin)"),
        types.BotCommand("send_specific_video", "Maxsus video yuborish (admin)"),
    ])
