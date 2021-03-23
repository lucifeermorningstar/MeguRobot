import math
import time
import requests
import json
import asyncio

from gpytranslate import Translator
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def shorten(description, info='anilist.co'):
    ms_g = ""
    if len(description) > 700:
        description = description[0:500] + '....'
        ms_g += f"\n**Descripción**:\n\n__{description}__ [Leer Más]({info})"
    else:
        ms_g += f"\n**Descripción**:\n\n__{description}__"
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
    tmp = ((str(days) + " Días, ") if days else "") + \
        ((str(hours) + " Horas, ") if hours else "") + \
        ((str(minutes) + " Minutos y ") if minutes else "") + \
        ((str(seconds) + " Segundos, ") if seconds else "") + \
        ((str(milliseconds) + " ms, ") if milliseconds else "")
    return tmp[:-2]


airing_query = '''
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
    '''

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

anime_query = '''
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
'''
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


url = 'https://graphql.anilist.co'


async def anime_airing(client, message):
    search_str = message.text.split(' ', 1)
    if len(search_str) == 1:
        await message.reply_text(message.chat.id, "Formato: `/airing <nombre del anime>`")
        return
    variables = {'search': search_str[1]}
    response = requests.post(
        url, json={'query': airing_query, 'variables': variables}).json()['data']['Media']
    ms_g = f"**Nombre**: **{response['title']['romaji']}**(`{response['title']['native']}`)\n**ID**: `{response['id']}`"
    if response['nextAiringEpisode']:
        airing_time = response['nextAiringEpisode']['timeUntilAiring'] * 1000
        airing_time_final = t(airing_time)
        ms_g += f"\n**Episodio**: `{response['nextAiringEpisode']['episode']}`\n**Transmitiéndose en**: `{airing_time_final}`"
    else:
        ms_g += f"\n**Episodio**:{response['episodes']}\n**Estado**: `N/A`"
    await client.send_message(message.chat.id, ms_g)


async def anime_search(client, message):
    search = message.text.split(' ', 1)
    if len(search) == 1:
        await message.delete()
        return
    else:
        search = search[1]
    variables = {'search': search}
    json = requests.post(url, json={'query': anime_query, 'variables': variables}).json()[
        'data'].get('Media', None)
    if json:
        msg = f"**{json['title']['romaji']}**(`{json['title']['native']}`)\n**Tipo**: {json['format']}\n**Estado**: {json['status']}\n**Episodios**: {json.get('episodes', 'N/A')}\n**Duración**: {json.get('duration', 'N/A')} minutos por episodio.\n**Calificación**: {json['averageScore']}\n**Géneros**: `"
        for x in json['genres']:
            msg += f"{x}, "
        msg = msg[:-2] + '`\n'
        msg += "**Estudios**: `"
        for x in json['studios']['nodes']:
            msg += f"{x['name']}, "
        msg = msg[:-2] + '`\n'
        info = json.get('siteUrl')
        trailer = json.get('trailer', None)
        if trailer:
            trailer_id = trailer.get('id', None)
            site = trailer.get('site', None)
            if site == "youtube":
                trailer = 'https://youtu.be/' + trailer_id
        description = (
            json.get("description", "N/A")
            .replace("<i>", "")
            .replace("</i>", "")
            .replace("<br>", "")
        )
        description = await translate(description)
        msg += shorten(description, info)
        image = info.replace('anilist.co/anime/', 'img.anili.st/media/')
        if trailer:
            buttons = [
                    [InlineKeyboardButton("Más Información", url=info),
                    InlineKeyboardButton("Trailer 🎬", url=trailer)]
                    ]
        else:
            buttons = [
                    [InlineKeyboardButton("Más Información", url=info)]
                    ]
        if image:
            try:
                await message.send_photo(image, caption=msg, reply_markup=InlineKeyboardMarkup(buttons))
            except:
                msg += f" [〽️]({image})"
                await message.edit(msg)
        else:
            await message.edit(msg)


async def character_search(client, message):
    search = message.text.split(' ', 1)
    if len(search) == 1:
        await message.reply_text("Formato: `/character <nombre del personaje>`")
        return
    search = search[1]
    variables = {'query': search}
    json = requests.post(url, json={'query': character_query, 'variables': variables}).json()[
        'data'].get('Character', None)
    if json:
        ms_g = f"**{json.get('name').get('full')}**(`{json.get('name').get('native')}`)\n"
        description = (
            json.get("description")
            .replace("<i>", "")
            .replace("</i>", "")
            .replace("<br>", "")
        )
        description = await translate(description)
        site_url = json.get('siteUrl')
        ms_g += shorten(description, site_url)
        image = json.get('image', None)
        if image:
            image = image.get('large')
            await message.send_photo(message.chat.id, image, caption=ms_g)
            
        else:
            await message.reply_text(ms_g)


async def manga_search(client, message):
    search = message.text.split(' ', 1)
    if len(search) == 1:
        await client.send_message("Formato: `/manga <nombre del manga>")
        return
    search = search[1]
    variables = {'search': search}
    json = requests.post(url, json={'query': manga_query, 'variables': variables}).json()[
        'data'].get('Media', None)
    ms_g = ''
    if json:
        title, title_native = json['title'].get(
            'romaji', False), json['title'].get('native', False)
        start_date, status, score = json['startDate'].get('year', False), json.get(
            'status', False), json.get('averageScore', False)
        if title:
            ms_g += f"**{title}**"
            if title_native:
                ms_g += f"(`{title_native}`)"
        if start_date:
            ms_g += f"\n**Inicio**: `{start_date}`"
        if status:
            ms_g += f"\n**Estado**: `{status}`"
        if score:
            ms_g += f"\n**Calificación**: `{score}`"
        ms_g += '\n**Géneros** - '
        for x in json.get('genres', []):
            ms_g += f"{x}, "
        ms_g = ms_g[:-2]

        image = json.get("bannerImage", False)
        description = (
            json.get("description", "N/A")
            .replace("<i>", "")
            .replace("</i>", "")
            .replace("<br>", "")
        )
        description = await translate(description)
        ms_g += f"_{description}_"
        if image:
            try:
                await client.send_photo(message.chat.id, image, caption=ms_g)
            except:
                ms_g += f" [〽️]({image})"
                await message.reply_text(ms_g)
        else:
            await message.reply(ms_g)


async def translate(text):
    tr = Translator()
    teks = await tr(text, targetlang="es")
    return teks.text