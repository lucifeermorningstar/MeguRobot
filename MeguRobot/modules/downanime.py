import os
import re
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from MeguRobot import pyrogrm as app
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from zippyshare_downloader import Zippyshare

z = Zippyshare(verbose=True, progress_bar=True, replace=True)


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
    url = url[:3] + "ps" + url[4:]
    z.extract_info(f"{url}", download=True, folder=folder, custom_filename=filename)


async def download_episode(client, query):
    await query.message.edit("Descargando episodio.")
    link = query.data.replace("episode_", "")
    try:
        await download_anime(link)
    except:
        await query.message.edit("Error al descargar el episodio.")
        return
    await query.message.edit("Subiendo archivo.")
    msg = await client.send_video(query.message.chat.id, f"temp/{link}.mp4")
    await query.message.delete()
    await msg.reply("Episodio descargado.")
    os.system(f"rm temp/{link}.mp4")


async def search_episodes(client, query):
    title = query.data.replace("title_", "")
    await query.message.edit("Buscando episodios.")
    episodes = await get_episodes(title)
    buttons = []
    for episode in episodes:
        buttons.append(
            [
                InlineKeyboardButton(
                    episode, callback_data=f"episode_{episodes[episode]}"
                )
            ]
        )
    keyboard = InlineKeyboardMarkup(buttons)
    await client.edit_message_text(
        query.message.chat.id,
        query.message.message_id,
        "Episodios",
        reply_markup=keyboard,
    )


async def downanime(client, message):
    cmd = message.command
    name = "+".join(cmd[1:])
    if len(cmd) < 2:
        return
    titles = await get_animes(name)
    if not titles:
        return
    buttons = []
    for title in titles:
        buttons.append(
            [InlineKeyboardButton(title, callback_data=f"title_{titles[title]}")]
        )
    keyboard = InlineKeyboardMarkup(buttons)
    await client.send_message(message.chat.id, "Animes", reply_markup=keyboard)


__mod_name__ = "Anime Video"
