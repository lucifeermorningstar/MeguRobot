# Last.fm module by @TheRealPhoenix - https://github.com/rsktg converted to pyrogram by @CrimsonDemon - https://github.com/NachABR

import os

import MeguRobot.modules.sql.last_fm_sql as sql
import requests
from MeguRobot import LASTFM_API_KEY
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from youtubedown import asyncDown


async def set_user(client, message):
    args = message.text.split(" ", 1)[1]
    if args:
        user = message.from_user.id
        username = "".join(args)
        sql.set_user(user, username)
        await message.reply_text(
            f"Nombre de usuario de Last.FM establecido a **{username}**!",
            parse_mode="md",
        )
    else:
        await message.reply_text(
            "Así no funciona...\nPon `/setuser` seguido de tu nombre de usuario de Last.FM!",
            parse_mode="md",
        )


async def clear_user(client, message):
    user = message.from_user.id
    sql.set_user(user, "")
    await message.reply_text(
        "Nombre de usuario de Last.FM quitado de mi base de datos!"
    )


async def last_fm(client, message):
    msg = message
    user = message.from_user.first_name
    user_id = message.from_user.id
    username = sql.get_user(user_id)
    if not username:
        await msg.reply_text(
            "Aún no has configurado un usuario de Last.FM!\nPuedes hacerlo con `/setuser`",
            parse_mode="md",
        )
        return

    base_url = "http://ws.audioscrobbler.com/2.0"
    res = requests.get(
        f"{base_url}?method=user.getrecenttracks&limit=3&extended=1&user={username}&api_key={LASTFM_API_KEY}&format=json"
    )
    if res.status_code != 200:
        await msg.reply_text(
            "Hmm... algo salió mal.\nAsegúrese de haber configurado el usuario de Last.FM correcto!"
        )
        return

    try:
        first_track = res.json().get("recenttracks").get("track")[0]
    except IndexError:
        await msg.reply_text("No parece que hayas escuchado alguna canción...")
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
        music_busq = f"{artist}_{song}"
        buttons = [
            [
                InlineKeyboardButton(
                    "Descargar ⬇️", callback_data=f"get_music_{music_busq}"
                )
            ]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        await msg.reply_text(rep, parse_mode="html", reply_markup=keyboard)
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
        await msg.reply_text(rep, parse_mode="html")


async def get_yt(client, query):
    await query.message.edit_reply_markup(
        reply_markup=None
    )
    info = query.data.replace("get_music_", "")
    info = info.replace("_", " ")
    q_msg = query.message.message_id
    rep = await client.send_message(
        chat_id=query.message.chat.id,
        reply_to_message_id=q_msg,
        text="Buscando música...",
    )
    try:
        file_name, title = await d_download(info)
        await client.send_audio(
            chat_id=query.message.chat.id,
            reply_to_message_id=q_msg,
            audio=f"temp/{file_name}.mp3",
            title=title,
            file_name="{}.mp3".format(title),
        )
        await rep.delete()
        os.remove(f"temp/{file_name}.mp3")
    except:
        import traceback

        traceback.print_exc()
        await rep.edit("No se encontraron resultados.")


async def d_download(music):
    try:
        main = await asyncDown.lookup(title=music, path="temp/%(id)s")
        dowload = await main.download()
        file_name = dowload["video_url"].split("=")[1]
        title = dowload["title"]
        return (file_name, title)
    except:
        import traceback

        traceback.print_exc()


__help__ = """
*Comandos disponibles:*

 •`/setuser <nombre de usuario>`: Establece tu nombre de usuario de Last.FM.
 •`/clearuser`: Elimina tu nombre de usuario de Last.FM del bot.
 •`/lastfm`: Devuelve lo que estás buscando en Last.FM.
"""

__mod_name__ = "Last.FM"

__command_list__ = ["setuser", "clearuser", "lastfm"]
