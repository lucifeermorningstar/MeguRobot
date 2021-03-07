import requests
import re
import time
import os
import sys
from urllib.parse import unquote
from bs4 import BeautifulSoup

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from MeguRobot import pyrogrm as app


def get_episodes(anime):
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


def get_animes(name):
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
            anime_link = re.findall(pattern_link, anime)[count].replace('href="', "").replace('"', "").replace(r"/anime/", "")
            animes[title] = anime_link
            count += 1

    return animes


def download_anime(link):
    link_full = "https://tioanime.com/ver/" + link
    page = requests.get(link_full)
    sp = BeautifulSoup(page.text,'html.parser')
    nombre = sp.findAll('a',{'class':'btn btn-success btn-download btn-sm rounded-pill'})
    nombre = [x for x in nombre if 'zippy' in x.get('href')]
    if len(nombre)==0:
        sys.exit()
    nombre = nombre[0].get('href')
    no2 = requests.get(unquote(nombre))
    bp = BeautifulSoup(no2.text,'html.parser')
    sec = bp.findAll('script')[9]
    nombre = sec.next
    cooki = no2.cookies
    cooki = cooki.list_domains()[1]
    nombre = re.sub('document.getElementById(.*)\.href = ','',nombre)
    nombre = nombre.replace('\n','')
    nombre = re.sub('if(.*)','',nombre)
    suma = nombre.replace(' ','').replace(';','')
    otro = re.split('\((.*)\)',suma)
    try:
        a = otro[0]
        suv = "str("+otro[1]+")"
        b = otro[2]
        suma = eval(a+suv+b)
    except Exception as e:
        exit()

    nombre = suma
    filename = link + ".mp4"
    url = "https://" + cooki + nombre
    dw = os.system(f"wget -q -O {filename} {url}")
    return dw


@app.on_callback_query(filters.regex("^episode_.*"))
async def download(client, query):
    await query.message.edit("Descargando episodio.")
    link = query.data.replace("episode_", "")
    status = download_anime(link)
    if status != 0:
        return
    await query.message.edit("Subiendo archivo.")
    msg = await client.send_video(query.message.chat.id, f"{link}.mp4")
    await query.message.delete()
    await msg.reply("Episodio descargado.")


@app.on_callback_query(filters.regex("^title_.*"))
async def episodes(client, query):
    title = query.data.replace("title_", "")
    await query.message.edit("Buscando episodios.")
    episodes = get_episodes(title)
    buttons = []
    for episode in episodes:
        buttons.append([InlineKeyboardButton(episode, callback_data=f"episode_{episodes[episode]}")])
    keyboard = InlineKeyboardMarkup(buttons)
    await client.edit_message_text(query.message.chat.id, query.message.message_id, "Episodios", reply_markup=keyboard)


@app.on_message(filters.command("downanime"))
async def downanime(client, message):
    cmd = message.command
    if len(cmd) < 2:
        return
    titles = get_animes("".join(cmd[1:]))
    if not titles:
        return
    buttons = []
    for title in titles:
        buttons.append([InlineKeyboardButton(title, callback_data=f"title_{titles[title]}")])
    keyboard = InlineKeyboardMarkup(buttons)
    await client.send_message(message.chat.id, "Animes", reply_markup=keyboard)
