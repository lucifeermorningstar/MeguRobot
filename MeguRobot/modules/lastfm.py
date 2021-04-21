# Last.fm module by @TheRealPhoenix - https://github.com/rsktg converted to pyrogram by @CrimsonDemon - https://github.com/NachABR

import os, random

import MeguRobot.modules.sql.last_fm_sql as sql
import requests
from MeguRobot import LASTFM_API_KEY
from pydeezer import Deezer
from pydeezer.constants import track_formats
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


arl = "b5adae63e9ec47cc332df3a9c83a088816888ee4e947b0491b1aa0ada6c1d011010be7a8d025a4aadb920b3de28193ca1eb59063f0bdb8f44f46087adc077a3fd533645e972c650527d9a383385da68ad264dc2fdcd3900cf6f461a443276c32"
deezer = Deezer(arl=arl)


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
        deezer_busq = f"{artist}_{song}"
        buttons = [[InlineKeyboardButton("Descargar ⬇️", callback_data=f"get_music_{deezer_busq}")]]
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


async def get_deezer(client, query):
    if "get_music_" in query.data:
        info = query.data.replace("get_music_", "")
        info = info.replace("_", " ")
        await query.edit_message_text("Buscando música...")
        try:
            track_search_results = deezer.search_tracks(info, limit=1)
            track_id = track_search_results[0]["id"]
            track = deezer.get_track(track_id)
            download_dir = "temp/"
            file_name = random.randint(0, 9999999999)
            track["download"](
                download_dir,
                filename=f"{file_name}",
                quality=track_formats.MP3_256,
                with_lyrics=False,
            )
            await client.send_audio(
                query.message.chat.id,
                audio=f"temp/{file_name}.mp3",
                title=track["tags"]["title"],
                file_name="{}.mp3".format(track["tags"]["title"])
            )
            await query.message.delete()
            os.remove(f"temp/{file_name}.mp3")
        except:
            await query.edit_message_text("No se encontraron resultados")


__help__ = """
*Comandos disponibles:*

 •`/setuser <nombre de usuario>`: Establece tu nombre de usuario de Last.FM.
 •`/clearuser`: Elimina tu nombre de usuario de Last.FM del bot.
 •`/lastfm`: Devuelve lo que estás buscando en Last.FM.
"""

__mod_name__ = "Last.FM"

__command_list__ = ["setuser", "clearuser", "lastfm"]
