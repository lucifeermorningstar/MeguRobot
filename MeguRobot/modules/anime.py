import requests
from gpytranslate import Translator
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def shorten(description, info="anilist.co"):
    ms_g = ""
    if len(description) > 700:
        description = description[0:600] + "..."
        ms_g += f"\n**Descripción**:\n{description}\n[Leer Más]({info})"
    else:
        ms_g += f"\n**Descripción**:\n{description}"
    return (
        ms_g.replace("<br>", "")
        .replace("</br>", "")
        .replace("<i>", "")
        .replace("</i>", "")
    )


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
        siteUrl
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
        idMal
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
                     native
               }
               siteUrl
               favourites
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


async def anime_airing(client, message):
    search_str = message.text.split(" ", 1)
    if len(search_str) == 1:
        await client.send_message(
            message.chat.id, "Formato: `/airing <nombre del anime>`", parse_mode="md"
        )
        return
    variables = {"search": search_str[1]}
    response = requests.post(
        url, json={"query": airing_query, "variables": variables}
    ).json()["data"]["Media"]
    ms_g = f"**Nombre**: **{response['title']['romaji']}**(`{response['title']['native']}`)\n**ID**: `{response['id']}`"
    if response["nextAiringEpisode"]:
        airing_time = response["nextAiringEpisode"]["timeUntilAiring"] * 1000
        airing_time_final = t(airing_time)
        ms_g += f"\n**Episodio**: `{response['nextAiringEpisode']['episode']}`\n**Transmitiéndose en**: `{airing_time_final}`"
    else:
        ms_g += f"\n**Episodio**:{response['episodes']}\n**Estado**: `N/A`"
    await client.send_message(message.chat.id, text=ms_g)


async def anime_search(client, message):
    search = message.text.split(" ", 1)
    if len(search) == 1:
        await client.send_message(
            message.chat.id, "Formato: `/anime <nombre del anime>`", parse_mode="md"
        )
        return
    else:
        search = search[1]
    variables = {"search": search}
    json = (
        requests.post(url, json={"query": anime_query, "variables": variables})
        .json()["data"]
        .get("Media", None)
    )
    if json:
        msg = f"**{json['title']['romaji']}**(`{json['title']['native']}`)\n**Tipo**: "
        if json["format"] == "MOVIE":
            msg += "Película"
        elif json["format"] == "TV_SHORT":
            msg += "Corto"
        elif json["format"] == "TV":
            msg += "TV"
        elif json["format"] == "SPECIAL":
            msg += "Especial"
        elif json["format"] == "MUSIC":
            msg += "Música"
        elif json["format"] == "OVA":
            msg += "OVA"
        elif json["format"] == "ONA":
            msg += "ONA"
        msg += "\n**Estado**: "
        if json["status"] == "RELEASING":
            msg += "En emisíon"
        elif json["status"] == "FINISHED":
            msg += "Finalizado"
        elif json["status"] == "NOT_YET_RELEASED":
            msg += "No emitido"
        elif json["status"] == "CANCELLED":
            msg += "Cancelado"
        msg += f"\n**Episodios**: `{json.get('episodes', 'N/A')}`\n**Duración**: `{json.get('duration', 'N/A')} mins aprox. por ep.`\n**Calificación**: `{json['averageScore']:1.0f}`\n**Géneros**: `"
        for x in json["genres"]:
            x = await translate(x)
            msg += f"{x}, "
        msg = msg[:-2] + "`\n"
        msg += "**Estudios**: `"
        for x in json["studios"]["nodes"]:
            msg += f"{x['name']}, "
        msg = msg[:-2] + "`\n"
        info = json.get("siteUrl")
        trailer = json.get("trailer", None)
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
        description = await translate(description)
        msg += shorten(description, info)
        image = info.replace("anilist.co/anime/", "img.anili.st/media/")
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
                await client.send_photo(
                    message.chat.id,
                    photo=image,
                    caption=msg,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
            except:
                msg += f" [〽️]({image})"
                await client.send_message(
                    message.chat.id,
                    text=msg,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
        else:
            await client.send_message(
                message.chat.id, text=msg, reply_markup=InlineKeyboardMarkup(buttons)
            )


async def character_search(client, message):
    search = message.text.split(" ", 1)
    if len(search) == 1:
        await message.reply_text(
            "Formato: `/character <nombre del personaje>`", parse_mode="md"
        )
        return
    search = search[1]
    variables = {"query": search}
    json = requests.post(
        url, json={"query": character_query, "variables": variables}
    ).json()
    if "errors" in json.keys():
        await message.reply_text("Error en la busqueda.")
        return
    if json:
        json = json["data"]["Character"]
        msg = f"**{json.get('name').get('full')}**"
        if json.get("name").get("native") is None:
            msg += "\n\n"
        else:
            msg += f"(`{json.get('name').get('native')}`)\n\n"
        site_url = json.get("siteUrl")
        description = json.get("description")
        description = await translate(description)
        description = (
            description.replace("<i>", "")
            .replace("</i>", "")
            .replace("<br>", "")
            .replace("__", "**")
            .replace("~", "~~")
            .replace(" ~", "~")
            .replace("! ", "!")
            .replace("\n ", " \n")
        )
        # print(repr(description))
        if len(description) > 700:
            description = description[0:600] + "..."
            msg += f"{description}[Leer Más]({site_url})"
        else:
            msg += description
        image = json.get("image", None)
        if image:
            image = image.get("large")
            await client.send_photo(
                message.chat.id, photo=image, caption=msg, parse_mode="md"
            )
        else:
            await client.reply_text(msg, parse_mode="md")


async def manga_search(client, message):
    search = message.text.split(" ", 1)
    if len(search) == 1:
        await message.reply_text(
            "Formato: `/manga <nombre del manga>`", parse_mode="md"
        )
        return
    search = search[1]
    variables = {"search": search}
    json = (
        requests.post(url, json={"query": manga_query, "variables": variables})
        .json()["data"]
        .get("Media", None)
    )
    ms_g = ""
    if json:
        title, title_native = json["title"].get("romaji", False), json["title"].get(
            "native", False
        )
        start_date, status, score = (
            json["startDate"].get("year", False),
            json.get("status", False),
            json.get("averageScore", False),
        )
        if title:
            ms_g += f"**{title}**"
            if title_native:
                ms_g += f"(`{title_native}`)"
        if start_date:
            ms_g += f"\n**Inicio**: `{start_date}`"
        if status:
            ms_g += f"\n**Estado**: `"
        if json["status"] == "RELEASING":
            ms_g += "En emisíon"
        elif json["status"] == "FINISHED":
            ms_g += "Finalizado"
        elif json["status"] == "HIATUS":
            ms_g += "Interrumpido"
        elif json["status"] == "NOT_YET_RELEASED":
            ms_g += "No emitido"
        elif json["status"] == "CANCELLED":
            ms_g += "Cancelado"
        ms_g += "`"
        if score:
            ms_g += f"\n**Calificación**: `{score}`"
        ms_g += "\n**Géneros**: `"
        for x in json.get("genres", []):
            x = await translate(x)
            ms_g += f"{x}, "
        ms_g = ms_g[:-2] + "`\n"

        image = json.get("bannerImage", False)
        description = "N/A"
        if json.get("description"):
            description = (
                json.get("description", "N/A")
                .replace("<i>", "")
                .replace("</i>", "")
                .replace("<br>", "")
            )
            description = await translate(description)
        site_url = json.get("siteUrl")
        ms_g += shorten(description, site_url)
        buttons = [[InlineKeyboardButton("Más Información", url=site_url)]]
        if image:
            try:
                await client.send_photo(
                    message.chat.id,
                    photo=image,
                    caption=ms_g,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
            except:
                ms_g += f" [〽️]({image})"
                await client.send_message(
                    message.chat.id,
                    text=ms_g,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
        else:
            await client.send_message(
                message.chat.id, text=ms_g, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True
            )


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
 •`/upcoming`*: * Devuelve una lista de nuevos animes en las próximas temporadas.
 •`/airing <anime>`*:* Devuelve información de emisión de anime.
 •`/whatanime`*:* Busca un anime respondiendo a un GIF, vídeo o imagen de una captura de un capítulo del Anime.
 """

__mod_name__ = "Anime"
