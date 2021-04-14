# Last.fm module by @TheRealPhoenix - https://github.com/rsktg

import MeguRobot.modules.sql.last_fm_sql as sql
import requests
from MeguRobot import LASTFM_API_KEY, dispatcher
from MeguRobot.modules.disable import DisableAbleCommandHandler
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, CommandHandler


def set_user(update: Update, context: CallbackContext):
    args = context.args
    msg = update.effective_message
    if args:
        user = update.effective_user.id
        username = " ".join(args)
        sql.set_user(user, username)
        msg.reply_text(
            f"Nombre de usuario de Last.FM establecido a *{username}*!",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        msg.reply_text(
            "Así no funciona...\nPon `/setuser` seguido de tu nombre de usuario de Last.FM!",
            parse_mode=ParseMode.MARKDOWN,
        )


def clear_user(update: Update, _):
    user = update.effective_user.id
    sql.set_user(user, "")
    update.effective_message.reply_text(
        "Nombre de usuario de Last.FM quitado de mi base de datos!"
    )


def last_fm(update: Update, _):
    msg = update.effective_message
    user = update.effective_user.first_name
    user_id = update.effective_user.id
    username = sql.get_user(user_id)
    if not username:
        msg.reply_text(
            "Aún no has configurado un usuario de Last.FM!\nPuedes hacerlo con `/setuser`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    base_url = "http://ws.audioscrobbler.com/2.0"
    res = requests.get(
        f"{base_url}?method=user.getrecenttracks&limit=3&extended=1&user={username}&api_key={LASTFM_API_KEY}&format=json"
    )
    if res.status_code != 200:
        msg.reply_text(
            "Hmm... algo salió mal.\nAsegúrese de haber configurado el usuario de Last.FM correcto!"
        )
        return

    try:
        first_track = res.json().get("recenttracks").get("track")[0]
    except IndexError:
        msg.reply_text("No parece que hayas escuchado alguna canción...")
        return
    if first_track.get("@attr"):
        # Ensures the track is now playing
        image = first_track.get("image")[3].get("#text")  # Grab URL of 300x300 image
        artist = first_track.get("artist").get("name")
        song = first_track.get("name")
        loved = int(first_track.get("loved"))
        rep = f"<b>{user}</b> está escuchando:\n\n"
        if not loved:
            rep += f"🎧  <b>{artist} - {song}</b>"
        else:
            rep += f"🎧  <b>{artist} - {song}</b> (❤ Favorita)"
        if image:
            rep += f"<a href='{image}'>\u200c</a>"
    else:
        tracks = res.json().get("recenttracks").get("track")
        track_dict = {
            tracks[i].get("artist").get("name"): tracks[i].get("name") for i in range(3)
        }
        rep = f"<b>{user}</b> estaba escuchando:\n\n"
        for artist, song in track_dict.items():
            rep += f"🎧  <b>{artist} - {song}</b>\n"
        last_user = (
            requests.get(
                f"{base_url}?method=user.getinfo&user={username}&api_key={LASTFM_API_KEY}&format=json"
            )
            .json()
            .get("user")
        )
        scrobbles = last_user.get("playcount")
        rep += f"\n(<b>{scrobbles}</b> scrobbles hasta ahora)"

    msg.reply_text(rep, parse_mode=ParseMode.HTML)


__help__ = """
*Comandos disponibles:*

 •`/setuser <nombre de usuario>`: Establece tu nombre de usuario de Last.FM.
 •`/clearuser`: Elimina tu nombre de usuario de Last.FM del bot.
 •`/lastfm`: Devuelve lo que estás buscando en Last.FM.
"""

__mod_name__ = "Last.FM"

SET_USER_HANDLER = CommandHandler("setuser", set_user, pass_args=True, run_async=True)
CLEAR_USER_HANDLER = CommandHandler("clearuser", clear_user, run_async=True)
LASTFM_HANDLER = DisableAbleCommandHandler("lastfm", last_fm, run_async=True)

dispatcher.add_handler(SET_USER_HANDLER)
dispatcher.add_handler(CLEAR_USER_HANDLER)
dispatcher.add_handler(LASTFM_HANDLER)

__command_list__ = ["setuser", "clearuser", "lastfm"]
