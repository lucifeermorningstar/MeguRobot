import aiohttp
import requests

from MeguRobot import BOT_USERNAME, pyrogrm
from MeguRobot.utils.aiohttp import AioHttp
from MeguRobot.modules.anime import (
    airing_query,
    anime_query,
    character_query,
    manga_query,
    shorten,
    t,
    url,
    translate,
)
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InputTextMessageContent,
)


@pyrogrm.on_inline_query()
async def inline_query_handler(client, query):
    string = query.query.lower()
    if string == "":
        await client.answer_inline_query(
            query.id,
            results=[
                InlineQueryResultPhoto(
                    caption="¡Oye! Tengo un modo inline, haz clic en los botones de abajo para comenzar con tu busqueda!",
                    photo_url="https://telegra.ph/file/21af7939895c314dddb23.jpg",
                    parse_mode="html",
                    title="Necesitas ayuda?",
                    description="Haz click aquí...",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "Anime", switch_inline_query_current_chat="anime "
                                ),
                                InlineKeyboardButton(
                                    "Manga", switch_inline_query_current_chat="manga "
                                ),
                            ],
                            [
                                InlineKeyboardButton(
                                    "Airing", switch_inline_query_current_chat="airing "
                                ),
                                InlineKeyboardButton(
                                    "Personaje",
                                    switch_inline_query_current_chat="character ",
                                ),
                            ],
                            [
                                InlineKeyboardButton(
                                    text="Ayuda",
                                    url=f"https://t.me/{BOT_USERNAME}?start=ghelp_anime",
                                )
                            ],
                        ]
                    ),
                ),
            ],
            switch_pm_text="Click aquí para ir al privado",
            switch_pm_parameter="start",
            cache_time=300,
        )

    answers = []
    txt = string.split()
    if len(txt) != 0 and txt[0] == "anime":
        if len(txt) == 1:
            await client.answer_inline_query(
                query.id,
                results=answers,
                switch_pm_text="Buscar un Anime",
                switch_pm_parameter="start",
            )
            return
        search = string.split(None, 1)[1]
        variables = {"search": search}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json={"query": anime_query, "variables": variables}
            ) as resp:
                r = await resp.json()
                json = r["data"].get("Media", None)
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
                    msg += f"\n**Episodios:** `{json.get('episodes', 'N/A')}`\n**Duración:** `{json.get('duration', 'N/A')} mins aprox. por ep.` \n**Calificación:** `{json['averageScore']}`\n**Géneros**: `"
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
                            [InlineKeyboardButton("Más Información", url=info)],
                            [InlineKeyboardButton("Trailer 🎬", url=trailer)],
                        ]
                    else:
                        buttons = [[InlineKeyboardButton("Más Información", url=info)]]
                    if image:
                        answers.append(
                            InlineQueryResultPhoto(
                                caption=msg,
                                photo_url=image,
                                parse_mode="markdown",
                                title=f"{json['title']['romaji']}",
                                description=f"{json['format']} | {json.get('episodes', 'N/A')} Episodio{'s' if len(str(json.get('episodes'))) > 1 else ''}",
                                reply_markup=InlineKeyboardMarkup(buttons),
                            )
                        )
                    else:
                        answers.append(
                            InlineQueryResultArticle(
                                title=f"{json['title']['romaji']}",
                                description=f"{json['format']} | {json.get('episodes', 'N/A')} Episodio{'s' if len(str(json.get('episodes'))) > 1 else ''}",
                                input_message_content=InputTextMessageContent(
                                    msg, parse_mode="md", disable_web_page_preview=True
                                ),
                                reply_markup=InlineKeyboardMarkup(buttons),
                            )
                        )
        await client.answer_inline_query(
            query.id, results=answers, cache_time=0, is_gallery=False
        )
    elif len(txt) != 0 and txt[0] == "manga":
        if len(txt) == 1:
            await client.answer_inline_query(
                query.id,
                results=answers,
                switch_pm_text="Buscar un Manga",
                switch_pm_parameter="start",
            )
            return
        search = string.split(None, 1)[1]
        variables = {"search": search}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json={"query": manga_query, "variables": variables}
            ) as resp:
                r = await resp.json()
                json = r["data"].get("Media", None)
                if json:
                    title, title_native = (
                        json["title"].get("romaji", False),
                        json["title"].get("native", False),
                    )
                    start_date, status, score = (
                        json["startDate"].get("year", False),
                        json.get("status", False),
                        json.get("averageScore", False),
                    )
                    if title:
                        ms_g = f"**{title}**"
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
                    if site_url:
                        buttons = InlineKeyboardMarkup(
                            [[InlineKeyboardButton("Más Información", url=site_url)]]
                        )
                    else:
                        buttons = None
                    ms_g += shorten(description, site_url)
                    banner_url = json.get("bannerImage")
                    if banner_url:
                        answers.append(
                            InlineQueryResultPhoto(
                                caption=ms_g,
                                photo_url=banner_url,
                                parse_mode="markdown",
                                title=f"{json['title']['romaji']}",
                                description=f"{json['startDate']['year']}",
                                reply_markup=buttons,
                            )
                        )
                    else:
                        answers.append(
                            InlineQueryResultArticle(
                                title=f"{json['title']['native']}",
                                description=f"{json['averageScore']}",
                                input_message_content=InputTextMessageContent(
                                    ms_g,
                                    parse_mode="markdown",
                                    disable_web_page_preview=True,
                                ),
                                reply_markup=buttons,
                            )
                        )
        await client.answer_inline_query(
            query.id, results=answers, cache_time=0, is_gallery=False
        )
    elif len(txt) != 0 and txt[0] == "airing":
        if len(txt) == 1:
            await client.answer_inline_query(
                query.id,
                results=answers,
                switch_pm_text="Obtener el estado de transmisión",
                switch_pm_parameter="start",
            )
            return
        search = string.split(None, 1)[1]
        variables = {"search": search}
        response = requests.post(
            url, json={"query": airing_query, "variables": variables}
        ).json()["data"]["Media"]
        info = response["siteUrl"]
        if info:
            buttons = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Más Información", url=info)]]
            )
        else:
            buttons = None
        image = info.replace("anilist.co/anime/", "img.anili.st/media/")
        if image:
            thumb = image
        else:
            thumb = None
        ms_g = f"**Nombre**: **{response['title']['romaji']}**(`{response['title']['native']}`)\n**ID**: `{response['id']}`"
        if response["nextAiringEpisode"]:
            airing_time = response["nextAiringEpisode"]["timeUntilAiring"] * 1000
            airing_time_final = t(airing_time)
            in_des = f"El episodio {response['nextAiringEpisode']['episode']} se transmitirá en {airing_time_final}"
            ms_g += f"\n**Episodio**: `{response['nextAiringEpisode']['episode']}`\n**Transmitiéndose en**: `{airing_time_final}`"
        else:
            ms_g += f"\n**Episodio**:{response['episodes']}\n**Estado**: `N/A`"
        answers.append(
            InlineQueryResultArticle(
                title=f"{response['title']['romaji']}",
                description=f"{in_des}",
                input_message_content=InputTextMessageContent(
                    f"{ms_g}[⁠ ⁠]({image})",
                    parse_mode="markdown",
                    disable_web_page_preview=False,
                ),
                reply_markup=buttons,
                thumb_url=thumb,
            )
        )
        await client.answer_inline_query(
            query.id, results=answers, cache_time=0, is_gallery=False
        )
    elif len(txt) != 0 and txt[0] == "character":
        if len(txt) == 1:
            await client.answer_inline_query(
                query.id,
                results=answers,
                switch_pm_text="Obtener información de un personaje",
                switch_pm_parameter="start",
            )
            return
        search = string.split(None, 1)[1]
        variables = {"query": search}
        json = requests.post(
            url, json={"query": character_query, "variables": variables}
        ).json()["data"]["Character"]
        if json:
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
            if len(description) > 700:
                description = description[0:600] + "..."
                msg += f"{description}[Leer Más]({site_url})"
            else:
                msg += description
            image = json.get("image", None)
            if image:
                image = image.get("large")
                answers.append(
                    InlineQueryResultPhoto(
                        caption=msg,
                        photo_url=image,
                        parse_mode="markdown",
                        title=f"{json.get('name').get('full')}",
                        description=f"❤️ {json['favourites']}",
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton("Más Información", url=site_url)]]
                        ),
                    )
                )
            else:
                answers.append(
                    InlineQueryResultArticle(
                        title=f"{json.get('name').get('full')}",
                        description=f"{json['favourites']}",
                        input_message_content=InputTextMessageContent(
                            msg, parse_mode="markdown", disable_web_page_preview=True
                        ),
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton("Más Información", url=site_url)]]
                        ),
                    )
                )
            await client.answer_inline_query(
                query.id, results=answers, cache_time=0, is_gallery=False
            )
