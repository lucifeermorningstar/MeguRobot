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


async def info_episode(link):
    # transforma un link de tioanime a uno de animeonline
    name = link.split("/")[-1]
    ep_num = re.search("-\d+$", name).group()
    ep_name = name.replace(ep_num, "-cap") + ep_num
    new_link = "https://animeonline.ninja/episodio/" + ep_name
    
    # data scraping
    try:
        headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:71.0) Gecko/20100101 Firefox/71.0",
        }
        r = requests.post(new_link, headers=headers)
        html_soup = BeautifulSoup(r.text, 'html.parser')
        info = html_soup.find("div", id="info")
        images = info.find_all("a", href=True)
    except:
        return ("", "", "", "",)
    
    ep_title = info.h1.text if info.h1 else ""
    ep_name = info.h3.text if info.h3 else ""
    ep_info = info.p.text if info.p else ""
    ep_img_link = images[0]["href"] if images[0] else ""
    ep_img_link = re.search(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]+\.+\w{3})", ep_img_link).group()
    
    return (ep_title, ep_name, ep_info, ep_img_link)


async def confirm_dowload(client, query):
    link = query.data.replace("episode_", "")
    full_link = "https://tioanime.com/ver/" + link
    ep_title, ep_name, ep_info, ep_img_link = await info_episode(full_link)
    caption=(
            f"<b>{ep_title}</b>\n"
            f"<u>{ep_name}</u>\n\n"
            f"<i>{ep_info}</i>\n\n"
        )
    while len(caption) > 1020:
        ep_info = ep_info[:-1]
        caption=(
            f"<b>{ep_title}</b>\n"
            f"<u>{ep_name}</u>\n\n"
            f"<i>{ep_info}</i>\n\n"
        )
    else:
        if not ep_info == "":
            ep_info += "..."
            caption=(
                f"<b>{ep_title}</b>\n"
                f"<u>{ep_name}</u>\n\n"
                f"<i>{ep_info}</i>\n\n"
            )
    keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "SÍ", 
                        callback_data=f"download_si_{link}"
                    ),
                    InlineKeyboardButton(
                        "NO",
                        callback_data=f"download_no_{link}"
                    )]
                ])
    if not ep_title == "":
        episode_data = await client.send_photo(
            query.message.chat.id,
            photo=ep_img_link,
            caption=caption,
            parse_mode="html"
        )
    await client.send_message(query.message.chat.id, "Seguro que quieres descargar ese episodio?", reply_markup=keyboard)
    await query.message.delete()

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
    if "download_si_" in query.data:
        await query.message.edit("Descargando episodio.")
        link = query.data.replace("download_si_", "")
        try:
            await download_anime(link)
        except:
            await query.message.edit("Error al descargar el episodio.")
            return
        await query.message.edit("Subiendo archivo.")
        hashtag_name = link.replace("-","_")
        msg = await client.send_video(query.message.chat.id, f"temp/{link}.mp4", caption=f"#{hashtag_name}")
        await query.message.delete()
        os.remove(f"temp/{link}.mp4")
    else:
        await query.message.edit("Ok no descargaré ese episodio")



async def search_episodes(client, query):
    title = query.data.replace("title_", "")
    await query.message.edit("Buscando episodios.")
    episodes = await get_episodes(title)
    buttons = [
                InlineKeyboardButton(
                    episode, callback_data=f"episode_{episodes[episode]}"
                ) for episode in episodes
            ]
    pairs = [buttons[i * 3 : (i + 1) * 3] for i in range((len(buttons) + 3 - 1) // 3)]
    round_num = len(buttons) / 3
    calc = len(buttons) - round(round_num)
    if calc == 1:
        pairs.append((buttons[-1],))
    elif calc == 2:
        pairs.append((modules[-1],))
        
    keyboard = InlineKeyboardMarkup(pairs)
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
