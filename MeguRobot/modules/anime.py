import requests
import os
import re
from google_trans_new import google_translator
import asyncio
from bs4 import BeautifulSoup
from MeguRobot import BOT_USERNAME
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from zippyshare_downloader import Zippyshare

z = Zippyshare(verbose=False, progress_bar=False, replace=True)


async def info_episode(link):
    # transforma un link de tioanime a uno de animeonline
    name = link.split("/")[-1]
    ep_num = re.search(r"-\d+$", name).group()
    ep_name = name.replace(ep_num, "-cap") + ep_num
    new_link = "https://animeonline.ninja/episodio/" + ep_name

    # data scraping
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:71.0) Gecko/20100101 Firefox/71.0",
        }
        r = requests.post(new_link, headers=headers)
        html_soup = BeautifulSoup(r.text, "html.parser")
        info = html_soup.find("div", id="info")
        images = info.find("div", id="dt_galery")
        images = images.find_all("a", href=True)
    except:
        return (
            "",
            "",
            "",
            "",
        )

    ep_title = info.h1.text if info.h1 else ""
    ep_name = info.h3.text if info.h3 else ""
    ep_info = info.p.text if info.p else ""
    try:
        ep_img_link = images[0]["href"] if images[0] else ""
        ep_img_link = re.search(
            r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]+\.+\w{3})",
            ep_img_link,
        ).group()
    except IndexError:
        ep_img_link = ""
    return (ep_title, ep_name, ep_info, ep_img_link)


async def confirm_dowload(client, query):
    await query.message.edit("Buscando información y enlaces...")
    link = query.data.replace("episode_", "")
    full_link = "https://tioanime.com/ver/" + link
    ep_title, ep_name, ep_info, ep_img_link = await info_episode(full_link)
    caption = f"<b>{ep_title}</b>\n" f"<u>{ep_name}</u>\n\n" f"<i>{ep_info}</i>\n\n"
    while len(caption) > 4040:
        ep_info = ep_info[:-1]
        caption = f"<b>{ep_title}</b>\n" f"<u>{ep_name}</u>\n\n" f"<i>{ep_info}</i>\n\n"
    else:
        if not ep_info == "":
            ep_info += "..."
            caption = (
                f"<b>{ep_title}</b>\n" f"<u>{ep_name}</u>\n\n" f"<i>{ep_info}</i>\n\n"
            )
    caption += f"<a href={ep_img_link}>\u200C</a><b>Seguro que quieres descargar ese episodio?</b>"
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("SÍ", callback_data=f"download_si_{link}"),
                InlineKeyboardButton("NO", callback_data=f"download_no_{link}"),
            ]
        ]
    )
    if not ep_title == "":
        await query.message.edit(caption, parse_mode="html", reply_markup=keyboard)
    else:
        await query.message.edit(
            "**Seguro que quieres descargar ese episodio?**",
            reply_markup=keyboard,
        )


async def get_episodes(anime):
    link = "https://tioanime.com/ver/" + anime + "-"
    links = {}
    count = 0
    for i in range(50):
        test = link + str(i)
        r = requests.get(test)
        notfound = re.findall("Ups... Prueba de nuevo", r.text)
        if notfound:
            if count > 0:
                break
            count += 1
        else:
            links["Episodio " + str(i)] = test.replace("https://tioanime.com/ver/", "")
    return links


async def get_animes(name):
    r = requests.get("https://tioanime.com/directorio?q=" + name)
    pattern = r'<article class="anime".*</article>'
    anime_list = re.findall(pattern, r.text, re.DOTALL)
    animes = {}
    for anime in anime_list:
        pattern_title = r'<h3 class="title">.*</h3>'
        animes_raw = re.findall(pattern_title, anime)
        for title in animes_raw:
            anime_title = title.replace('<h3 class="title">', "").replace("</h3>", "")
            animes[anime_title] = ""

        count = 0
        for title in animes:
            pattern_link = r'href=".*"'
            anime_link = (
                re.findall(pattern_link, anime)[count]
                .replace('href="', "")
                .replace('"', "")
                .replace(r"/anime/", "")
            )
            animes[title] = anime_link
            count += 1

    return animes


async def download_anime(link):
    link_full = "https://tioanime.com/ver/" + link
    page = requests.get(link_full)
    sp = BeautifulSoup(page.text, "html.parser")
    nombre = sp.findAll(
        "a", {"class": "btn btn-success btn-download btn-sm rounded-pill"}
    )
    nombre = [x for x in nombre if "zippy" in x.get("href")]
    if len(nombre) == 0:
        return
    filename = f"{link}.mp4"
    folder = "temp"
    url = nombre[0].get("href")
    if url[4] != "s":
        url = url[:3] + "ps" + url[4:]
    print(url)
    z.extract_info(f"{url}", download=True, folder=folder, custom_filename=filename)


async def download_episode(client, query):
    if "download_si_" in query.data:
        await query.message.edit("Descargando episodio.")
        link = query.data.replace("download_si_", "")
        try:
            await download_anime(link)
        except:
            await query.message.edit("Error al descargar el episodio.")
            return
        try:
            await query.message.edit("Subiendo archivo.")
        except:
            pass
        hashtag_name = link.replace("-", "_")
        msg = await client.send_video(
            query.message.chat.id,
            f"temp/{link}.mp4",
            thumb="resources/megu_thum.jpg",
            caption=f"#{hashtag_name}",
        )
        await query.message.delete()
        os.remove(f"temp/{link}.mp4")
    else:
        await query.message.edit("Ok no descargaré ese episodio")


async def search_episodes(client, query):
    title = query.data.replace("title_", "")
    await query.message.edit("Buscando episodios...")
    episodes = await get_episodes(title)
    buttons = [
        InlineKeyboardButton(episode, callback_data=f"episode_{episodes[episode]}")
        for episode in episodes
    ]
    pairs = [buttons[i * 3 : (i + 1) * 3] for i in range((len(buttons) + 3 - 1) // 3)]
    round_num = len(buttons) / 3
    calc = len(buttons) - round(round_num)
    if calc == 1:
        pairs.append((buttons[-1],))
    elif calc == 2:
        pairs.append((buttons[-1],))

    keyboard = InlineKeyboardMarkup(pairs)
    await query.message.edit(text="**Episodios:** ", reply_markup=keyboard)


async def downanime(client, query):
    query_title = query.data.replace("downanime_", "")
    name = "+".join(query_title.split())
    titles = await get_animes(name)
    if not titles:
        await client.send_message(query.message.chat.id, f"No se pudo descargar el anime **{query_title}**.")
        return
    buttons = []
    for title in titles:
        buttons.append(
            [InlineKeyboardButton(title, callback_data=f"title_{titles[title]}")]
        )
    keyboard = InlineKeyboardMarkup(buttons)
    await client.send_message(query.message.chat.id, "**Animes:** ", reply_markup=keyboard)


def shorten(description, info="anilist.co"):
    ms_g = ""
    if len(description) > 600:
        description = description[0:600] + "..."
        ms_g += f"\n**Descripción**:\n{description}"
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
"""  # NOTE: Esto no está siendo usado

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
        msg = f"**{json['title']['romaji']}**(`{json['title']['native']}`)\n**Tipo**: `"
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
        msg += "`\n**Estado**: `"
        if json["status"] == "RELEASING":
            msg += "En emisíon"
        elif json["status"] == "FINISHED":
            msg += "Finalizado"
        elif json["status"] == "NOT_YET_RELEASED":
            msg += "No emitido"
        elif json["status"] == "CANCELLED":
            msg += "Cancelado"
        msg += f"`\n**Episodios**: `{json.get('episodes', 'N/A')}`\n**Duración**: `{json.get('duration', 'N/A')} mins aprox. por ep.`\n**Calificación**: `{json['averageScore']:1.0f}`\n**Géneros**: `"
        for x in json["genres"]:
            x = await translate(x)
            msg += f"{x}, "
            msg = msg.replace(" , ", ", ")
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
            .replace(" ... ", "... ")
            .replace(".  ", ".\n\n")
        )
        description = await translate(description)
        msg += shorten(description, info)
        image = info.replace("anilist.co/anime/", "img.anili.st/media/")
        if trailer:
            buttons = [
                [
                    InlineKeyboardButton("Más Información", url=info),
                    InlineKeyboardButton("Trailer 🎬", url=trailer),
                ],
                [InlineKeyboardButton("Descargar ⬇️", callback_data=f"downanime_{json['title']['romaji']}")]
            ]
        else:
            buttons = [
                [InlineKeyboardButton("Más Información", url=info)],
                [InlineKeyboardButton("Descargar ⬇️", callback_data=f"downanime_{json['title']['romaji']}")]
            ]
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
            .replace("] (", "](")
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
                message.chat.id,
                text=ms_g,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True,
            )


async def translate(text):
    tr = google_translator()
    loop = asyncio.get_event_loop()
    try:
        teks = await loop.run_in_executor(None, tr.translate, text, "es")
    except Exception:
        return text
    return teks


__help__ = f"""
Obtén información sobre anime, manga o personajes de [AniList](anilist.co).

*Comandos disponibles:*

 •`/anime <anime>`*:* Devuelve información sobre el anime.
 •`/character <carácter>`*:* Devuelve información sobre el personaje.
 •`/manga <manga>`*:* Devuelve información sobre el manga.
 •`/upcoming`*:* Devuelve una lista de nuevos animes en las próximas temporadas.
 •`/airing <anime>`*:* Devuelve información de emisión del anime.
 •`/whatanime`*:* Busca un anime respondiendo a un GIF, vídeo o imagen de una captura de un capítulo del Anime.
 •`/downanime <anime>`*:* Descarga un episodio de un anime

*Modo Inline:*

Usa @{BOT_USERNAME} en cualquier parte cuando escribas, esto mostrará el modo inline el cual puedes usar cuando el bot no está en el chat.

 • `@{BOT_USERNAME} anime`: Devuelve información sobre el anime.
 • `@{BOT_USERNAME} airing`: Devuelve información de emisión del anime.
 • `@{BOT_USERNAME} manga`: Devuelve información sobre el manga.
 • `@{BOT_USERNAME} character`: Devuelve información sobre el personaje.
 
 """

__mod_name__ = "Anime"
