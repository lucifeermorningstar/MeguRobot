import datetime
import html
import textwrap
import bs4
import jikanpy
import requests
import asyncio

from gpytranslate import Translator
from MeguRobot import dispatcher
from MeguRobot.modules.disable import DisableAbleCommandHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import CallbackContext

info_btn = "Más Información"
prequel_btn = "⬅️ Precuela"
sequel_btn = "Secuela ➡️"
close_btn = "Cerrar ❌"


def shorten(description, info="anilist.co"):
    msg = ""
    if len(description) > 700:
        description = description[0:500] + "...."
        msg += f"\n*Descripción*:\n_{description}_[Leer Más]({info})"
    else:
        msg += f"\n*Descripción*:\n_{description}_"
    return msg


# time formatter from uniborg
def t(milliseconds: int) -> str:
    """Inputs time in milliseconds, to get beautified time,
    as string"""
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + " Días, ") if days else "")
        + ((str(hours) + " Horas, ") if hours else "")
        + ((str(minutes) + " Minutos y ") if minutes else "")
        + ((str(seconds) + " Segundos, ") if seconds else "")
        + ((str(milliseconds) + " ms, ") if milliseconds else "")
    )
    return tmp[:-2]


airing_query = """
query ($id: Int,$search: String) { 
    Media (id: $id, type: ANIME,search: $search) {
        id
        episodes
        title {
            romaji
            english
            native
        }
        nextAiringEpisode {
            airingAt
            timeUntilAiring
            episode
        } 
    }
}
"""

fav_query = """
query ($id: Int) {
    Media (id: $id, type: ANIME) {
        id
        title {
            romaji
            english
            native
        }
    }
}
"""

anime_query = """
query ($id: Int,$search: String) {
    Media (id: $id, type: ANIME,search: $search) {
        id
        title {
            romaji
            english
            native
        }
        description (asHtml: false)
        startDate{
            year
        }
        episodes
        season
        type
        format
        status
        duration
        siteUrl
        studios{
            nodes{
                name
            }
        }
        trailer{
            id
            site
            thumbnail
        }
        averageScore
        genres
        bannerImage
    }
}
"""

character_query = """
query ($query: String) {
    Character (search: $query) {
        id
        name {
            first
            last
            full
        }
        siteUrl
        image {
            large
        }
        description
    }
}
"""

manga_query = """
query ($id: Int,$search: String) { 
    Media (id: $id, type: MANGA,search: $search) { 
        id
        title {
            romaji
            english
            native
        }
        description (asHtml: false)
        startDate{
            year
        }
        type
        format
        status
        siteUrl
        averageScore
        genres
        bannerImage
    }
}
"""

url = "https://graphql.anilist.co"


def airing(update: Update, context: CallbackContext):
    message = update.effective_message
    search_str = message.text.split(" ", 1)
    if len(search_str) == 1:
        update.effective_message.reply_text("Formato: `/airing <nombre del anime>`")
        return
    variables = {"search": search_str[1]}
    response = requests.post(
        url, json={"query": airing_query, "variables": variables}
    ).json()["data"]["Media"]
    msg = f"*Nombre*: *{response['title']['romaji']}*(`{response['title']['native']}`)\n*ID*: `{response['id']}`"
    if response["nextAiringEpisode"]:
        time = response["nextAiringEpisode"]["timeUntilAiring"] * 1000
        time = t(time)
        msg += f"\n*Episodio*: `{response['nextAiringEpisode']['episode']}`\n*Se transmitirá en*: `{time}`"
    else:
        msg += f"\n*Episodio*:{response['episodes']}\n*Estado*: `N/A`"
    update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


def anime(update: Update, context: CallbackContext):
    message = update.effective_message
    search = message.text.split(" ", 1)
    if len(search) == 1:
        update.effective_message.reply_text("Formato: `/anime <nombre de anime>`")
        return
    else:
        search = search[1]
    variables = {"search": search}
    json = requests.post(
        url, json={"query": anime_query, "variables": variables}
    ).json()
    if "errors" in json.keys():
        update.effective_message.reply_text("Error en la busqueda.")
        return
    if json:
        json = json["data"]["Media"]
        msg = f"*{json['title']['romaji']}*(`{json['title']['native']}`)\n*Tipo*: {json['format']}\n*Estado*: {json['status']}\n*Episodios*: {json.get('episodes', 'N/A')}\n*Duración*: {json.get('duration', 'N/A')} por episodio.\n*Calificación*: {json['averageScore']}\n*Generos*: `"
        for x in json["genres"]:
            x = asyncio.run(translate(x))
            msg += f"`{x}`, "
        msg = msg[:-2] + "`\n"
        msg += "*Estudios*: `"
        for x in json["studios"]["nodes"]:
            msg += f"{x['name']}, "
        msg = msg[:-2] + "`\n"
        info = json.get("siteUrl")
        trailer = json.get("trailer", None)
        anime_id = json["id"]
        if trailer:
            trailer_id = trailer.get("id", None)
            site = trailer.get("site", None)
            if site == "youtube":
                trailer = "https://youtu.be/" + trailer_id
        description = (
            json.get("description", "N/A")
            .replace("<i>", "")
            .replace("</i>", "")
            .replace("<br>", "")
        )
        description = asyncio.run(translate(description))
        msg += shorten(description, info)
        image = json.get("bannerImage", None)
        if trailer:
            buttons = [
                [
                    InlineKeyboardButton("Más Información", url=info),
                    InlineKeyboardButton("Trailer 🎬", url=trailer),
                ]
            ]
        else:
            buttons = [[InlineKeyboardButton("Más Información", url=info)]]
        if image:
            try:
                update.effective_message.reply_photo(
                    photo=image,
                    caption=msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
            except:
                msg += f" [〽️]({image})"
                update.effective_message.reply_text(
                    msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
        else:
            update.effective_message.reply_text(
                msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons),
            )


def character(update: Update, context: CallbackContext):
    message = update.effective_message
    search = message.text.split(" ", 1)
    if len(search) == 1:
        update.effective_message.reply_text(
            "Formato: `/character <nombre del personaje>`"
        )
        return
    search = search[1]
    variables = {"query": search}
    json = requests.post(
        url, json={"query": character_query, "variables": variables}
    ).json()
    if "errors" in json.keys():
        update.effective_message.reply_text("Error en la busqueda.")
        return
    if json:
        json = json["data"]["Character"]
        msg = f"*{json.get('name').get('full')}*(`{json.get('name').get('native')}`)\n"
        description = f"{json['description']}"
        description = asyncio.run(translate(description))
        site_url = json.get("siteUrl")
        msg += shorten(description, site_url)
        image = json.get("image", None)
        if image:
            image = image.get("large")
            update.effective_message.reply_photo(
                photo=image,
                caption=msg.replace("<b>", "</b>"),
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            update.effective_message.reply_text(
                msg.replace("<b>", "</b>"), parse_mode=ParseMode.MARKDOWN
            )


def manga(update: Update, context: CallbackContext):
    message = update.effective_message
    search = message.text.split(" ", 1)
    if len(search) == 1:
        update.effective_message.reply_text("Formato : `/manga <nombre de manga>`")
        return
    search = search[1]
    variables = {"search": search}
    json = requests.post(
        url, json={"query": manga_query, "variables": variables}
    ).json()
    msg = ""
    if "errors" in json.keys():
        update.effective_message.reply_text("Error en la busqueda.")
        return
    if json:
        json = json["data"]["Media"]
        title, title_native = json["title"].get("romaji", False), json["title"].get(
            "native", False
        )
        start_date, status, score = (
            json["startDate"].get("year", False),
            json.get("status", False),
            json.get("averageScore", False),
        )
        if title:
            msg += f"*{title}*"
            if title_native:
                msg += f"(`{title_native}`)"
        if start_date:
            msg += f"\n*Fecha de Inicio*: `{start_date}`"
        if status:
            msg += f"\n*Estado*: `{status}`"
        if score:
            msg += f"\n*Calificación*: `{score}`"
        msg += "\n*Generos*: "
        for x in json.get("genres", []):
            x = asyncio.run(translate(x))
            msg += f"`{x}`, "
        msg = msg[:-2]
        info = json.get("siteUrl")
        buttons = [[InlineKeyboardButton("Más Información", url=info)]]
        image = json.get("bannerImage", False)
        description = (
            json.get("description", "N/A")
            .replace("<i>", "")
            .replace("</i>", "")
            .replace("<br>", "")
        )
        description = asyncio.run(translate(description))
        site_url = json.get("siteUrl")
        msg += shorten(description, site_url)
        if image:
            try:
                update.effective_message.reply_photo(
                    photo=image,
                    caption=msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
            except:
                msg += f" [〽️]({image})"
                update.effective_message.reply_text(
                    msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
        else:
            update.effective_message.reply_text(
                msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons),
            )


def user(update: Update, context: CallbackContext):
    message = update.effective_message
    args = message.text.strip().split(" ", 1)

    try:
        search_query = args[1]
    except:
        if message.reply_to_message:
            search_query = message.reply_to_message.text
        else:
            update.effective_message.reply_text("Format : /user <username>")
            return

    jikan = jikanpy.jikan.Jikan()

    try:
        us = jikan.user(search_query)
    except jikanpy.APIException:
        update.effective_message.reply_text("Username not found.")
        return

    progress_message = update.effective_message.reply_text("Searching.... ")

    date_format = "%Y-%m-%d"
    if us["image_url"] is None:
        img = "https://cdn.myanimelist.net/images/questionmark_50.gif"
    else:
        img = us["image_url"]

    try:
        user_birthday = datetime.datetime.fromisoformat(us["birthday"])
        user_birthday_formatted = user_birthday.strftime(date_format)
    except:
        user_birthday_formatted = "Unknown"

    user_joined_date = datetime.datetime.fromisoformat(us["joined"])
    user_joined_date_formatted = user_joined_date.strftime(date_format)

    for entity in us:
        if us[entity] is None:
            us[entity] = "Unknown"

    about = us["about"].split(" ", 60)

    try:
        about.pop(60)
    except IndexError:
        pass

    about_string = " ".join(about)
    about_string = about_string.replace("<br>", "").strip().replace("\r\n", "\n")

    caption = ""

    caption += textwrap.dedent(
        f"""
    *Username*: [{us['username']}]({us['url']})
    *Gender*: `{us['gender']}`
    *Birthday*: `{user_birthday_formatted}`
    *Joined*: `{user_joined_date_formatted}`
    *Days wasted watching anime*: `{us['anime_stats']['days_watched']}`
    *Days wasted reading manga*: `{us['manga_stats']['days_read']}`
    """
    )

    caption += f"*About*: {about_string}"

    buttons = [[InlineKeyboardButton(info_btn, url=us["url"])],]

    update.effective_message.reply_photo(
        photo=img,
        caption=caption,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    progress_message.delete()


def upcoming(update: Update, context: CallbackContext):
    jikan = jikanpy.jikan.Jikan()
    upcomin = jikan.top("anime", page=1, subtype="upcoming")

    upcoming_list = [entry["title"] for entry in upcomin["top"]]
    upcoming_message = "Proximos animes:\n\n"

    for entry_num in range(len(upcoming_list)):
        if entry_num == 10:
            break
        upcoming_message += f"{entry_num + 1}. {upcoming_list[entry_num]}\n"

    update.effective_message.reply_text(upcoming_message)


async def translate(text):
    tr = Translator()
    teks = await tr(text, targetlang="es")
    return teks.text


__help__ = """
Obtén información sobre anime, manga o personajes de [AniList](anilist.co).
*Comandos disponibles:*
 •`/anime <anime>`*:* Devuelve información sobre el anime.
 •`/character <carácter>`*:* Devuelve información sobre el carácter.
 •`/manga <manga>`*:* Devuelve información sobre el manga.
 • `/user <user>`*:* Devuelve información sobre el usuario de MyAnimeList.
 •`/upcoming`*: * Devuelve una lista de nuevos animes en las próximas temporadas.
 •`/airing <anime>`*:* Devuelve información de emisión de anime.
 •`/whatanime`*:* Busca un anime respondiendo a un GIF, vídeo o imagen de una captura de un capítulo del Anime.
 """

AIRING_HANDLER = DisableAbleCommandHandler("airing", airing, run_async=True)
ANIME_HANDLER = DisableAbleCommandHandler("anime", anime, run_async=True)
CHARACTER_HANDLER = DisableAbleCommandHandler("character", character, run_async=True)
MANGA_HANDLER = DisableAbleCommandHandler("manga", manga, run_async=True)
USER_HANDLER = DisableAbleCommandHandler("user", user, run_async=True)
UPCOMING_HANDLER = DisableAbleCommandHandler("upcoming", upcoming, run_async=True)

dispatcher.add_handler(ANIME_HANDLER)
dispatcher.add_handler(CHARACTER_HANDLER)
dispatcher.add_handler(MANGA_HANDLER)
dispatcher.add_handler(AIRING_HANDLER)
dispatcher.add_handler(USER_HANDLER)
dispatcher.add_handler(UPCOMING_HANDLER)

__mod_name__ = "Anime"
__command_list__ = [
    "anime",
    "manga",
    "user",
    "character",
    "upcoming",
    "airing",
]
__handlers__ = [
    ANIME_HANDLER,
    CHARACTER_HANDLER,
    MANGA_HANDLER,
    USER_HANDLER,
    UPCOMING_HANDLER,
    AIRING_HANDLER,
]
