from random import randint

import requests as r
from MeguRobot import SUPPORT_CHAT, WALL_API_KEY, dispatcher
from MeguRobot.modules.disable import DisableAbleCommandHandler
from telegram import Update
from telegram.ext import CallbackContext

# Wallpapers module by @TheRealPhoenix using wall.alphacoders.com


def wall(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    args = context.args
    msg_id = update.effective_message.message_id
    bot = context.bot
    query = " ".join(args)
    if not query:
        msg.reply_text("Por favor ingrese su busqueda!")
        return
    else:
        caption = query
        term = query.replace(" ", "%20")
        json_rep = r.get(
            f"https://wall.alphacoders.com/api2.0/get.php?auth={WALL_API_KEY}&method=search&term={term}"
        ).json()
        if not json_rep.get("success"):
            msg.reply_text(f"¡Ocurrió un error! Informar esto en @{SUPPORT_CHAT}")
        else:
            wallpapers = json_rep.get("wallpapers")
            if not wallpapers:
                msg.reply_text("No se han encontrado resultados!")
                return
            else:
                index = randint(0, len(wallpapers) - 1)  # Choose random index
                wallpaper = wallpapers[index]
                wallpaper = wallpaper.get("url_image")
                wallpaper = wallpaper.replace("\\", "")
                bot.send_photo(
                    chat_id,
                    photo=wallpaper,
                    caption="Vista Previa",
                    reply_to_message_id=msg_id,
                    timeout=60,
                )
                bot.send_document(
                    chat_id,
                    document=wallpaper,
                    filename="wallpaper",
                    caption=caption,
                    reply_to_message_id=msg_id,
                    timeout=60,
                )


__mod_name__ = "Wallpapers"
WALLPAPER_HANDLER = DisableAbleCommandHandler("wall", wall, run_async=True)
dispatcher.add_handler(WALLPAPER_HANDLER)
__command_list__ = ["wall"]
