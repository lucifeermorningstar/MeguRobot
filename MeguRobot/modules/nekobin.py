import asyncio
import os

from MeguRobot import pyrogrm
from MeguRobot.utils.aiohttp import AioHttp
from MeguRobot.utils.capture_errors import capture_err
from pyrogram import filters

from nekobin import NekoBin


@capture_err
async def paste(client, message):
    nekobin = NekoBin()
    try:
        if (
            message.reply_to_message.document
            and message.reply_to_message.document.file_size < 2 ** 20 * 10
        ):
            var = os.path.splitext(message.reply_to_message.document.file_name)[1]
            print(var)
            path = await message.reply_to_message.download("temp/")
            with open(path) as doc:
                text = doc.read()
            os.remove(path)
        if message.reply_to_message:
            text = message.reply_to_message.text
        try:
            response = await nekobin.nekofy(text)
        except Exception:
            await message.reply_text("Ocurrió un error al copiar...")
    except:
        await message.reply_text("Dame algo para copiar!")
    try:
        text = "Copiado a **Nekobin**:\n"
        text += f" • [Link]({response.url})"
        text += f" | [Raw]({response.raw})"
        await message.reply_text(text, disable_web_page_preview=True, parse_mode="md")
    except:
        pass


@capture_err
async def get_paste_(client, message):
    """fetches the content of a dogbin or nekobin URL."""
    if message.reply_to_message:
        link = message.reply_to_message.text
    rep = await client.send_message(
        message.chat.id, text="Obteniendo el contenido copiado..."
    )
    format_view = "https://del.dog/v/"
    if link.startswith(format_view):
        link = link[len(format_view) :]
        raw_link = f"https://del.dog/raw/{link}"
    elif link.startswith("https://del.dog/"):
        link = link[len("https://del.dog/") :]
        raw_link = f"https://del.dog/raw/{link}"
    elif link.startswith("del.dog/"):
        link = link[len("del.dog/") :]
        raw_link = f"https://del.dog/raw/{link}"
    elif link.startswith("https://nekobin.com/"):
        link = link[len("https://nekobin.com/") :]
        raw_link = f"https://nekobin.com/raw/{link}"
    elif link.startswith("nekobin.com/"):
        link = link[len("nekobin.com/") :]
        raw_link = f"https://nekobin.com/raw/{link}"
    else:
        await rep.edit_text(text="Responde a un link de **NekoBin** o **DogBin**!")
        return
    resp = await AioHttp().get_text(raw_link)
    await client.send_message(message.chat.id, text=f"**Contenido:**\n`{resp}`")
