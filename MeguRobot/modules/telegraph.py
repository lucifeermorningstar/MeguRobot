import os
from datetime import datetime

from MeguRobot import pyrogrm
from MeguRobot.utils.capture_errors import capture_err
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from telegraph import upload_file


@capture_err
async def telegraph(client, message):
    replied = message.reply_to_message
    start_t = datetime.now()
    if not replied:
        await message.reply_text("Responde a un archivo multimedia compatible")
        return
    if not (
        (replied.photo and replied.photo.file_size <= 5242880)
        or (replied.animation and replied.animation.file_size <= 5242880)
        or (
            replied.video
            and replied.video.file_name.endswith(".mp4")
            and replied.video.file_size <= 5242880
        )
        or (
            replied.document
            and replied.document.file_name.endswith(
                (".jpg", ".jpeg", ".png", ".gif", ".mp4")
            )
            and replied.document.file_size <= 5242880
        )
    ):
        await message.reply_text("No soportado!")
        return
    download_location = await client.download_media(
        message=message.reply_to_message, file_name="temp/"
    )
    try:
        response = upload_file(download_location)
    except Exception as document:
        await message.reply(document)
    else:
        try:
            button = [
                [
                    InlineKeyboardButton(
                        "Telegra.ph", url=f"https://telegra.ph{response[0]}"
                    )
                ]
            ]
            await message.reply_text(
                f"**Archivo subido a: [Telegra.ph](https://telegra.ph{response[0]})**",
                reply_markup=InlineKeyboardMarkup(button),
            )
        except:
            await message.reply_text(
                f"**Archivo subido a: [Telegra.ph](https://telegra.ph{response[0]})**"
            )
    finally:
        os.remove(download_location)
