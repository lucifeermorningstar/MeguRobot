import os
from datetime import datetime

from MeguRobot import LOGGER, pyrogrm
from MeguRobot.utils.capture_errors import capture_err
from pyrogram import Client, filters
from pyrogram.errors import PeerIdInvalid
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, User


def ReplyCheck(message: Message):
    reply_id = None

    if message.reply_to_message:
        reply_id = message.reply_to_message.message_id

    elif not message.from_user.is_self:
        reply_id = message.message_id

    return reply_id


WHOIS = (
    "**Información:**\n\n"
    "**ID:** `{user_id}`\n"
    "**Nombre:** [{full_name}](tg://user?id={userid})\n"
    "**Alias:** `{username}`\n"
    "**Última vez:** `{last_online}`\n"
)

WHOIS_PIC = (
    "**Información:**\n\n"
    "**ID:** `{user_id}`\n"
    "**Nombre:** [{full_name}](tg://user?id={userid})\n"
    "**Alías:** `{username}`\n"
    "**Última vez:** `{last_online}`\n"
    "**PFPs:** `{profile_pics}`\n"
)


def LastOnline(user: User):
    if user.is_bot:
        return ""
    elif user.status == "recently":
        return "Recientemente"
    elif user.status == "within_week":
        return "Hace unas semanas"
    elif user.status == "within_month":
        return "Hace un mes"
    elif user.status == "long_time_ago":
        return "Hace mucho tiempo"
    elif user.status == "online":
        return "En línea"
    elif user.status == "offline":
        return datetime.fromtimestamp(user.status.date).strftime(
            "%a, %d %b %Y, %H:%M:%S"
        )


def FullName(user: User):
    return user.first_name + " " + user.last_name if user.last_name else user.first_name


def ProfilePicUpdate(user_pic):
    return datetime.fromtimestamp(user_pic[0].date).strftime("%d.%m.%Y, %H:%M:%S")


@capture_err
async def whois(client, message):
    buscando = await message.reply_text(text="Buscando...")
    cmd = message.command
    if not message.reply_to_message and len(cmd) == 1:
        get_user = message.from_user.id
    elif len(cmd) == 1:
        get_user = message.reply_to_message.from_user.id
    elif len(cmd) > 1:
        get_user = cmd[1]
        try:
            get_user = int(cmd[1])
        except ValueError:
            pass
    try:
        user = await client.get_users(get_user)
    except PeerIdInvalid:
        await buscando.edit("No conozco a este usuario.")
        return
    desc = await client.get_chat(get_user)
    desc = desc.description
    user_pic = await client.get_profile_photos(user.id)
    pic_count = await client.get_profile_photos_count(user.id)
    if not user.photo:
        await message.reply(
            WHOIS.format(
                user_id=user.id,
                full_name=FullName(user),
                userid=user.id,
                username=user.username if user.username else "`Sin alias`",
                last_online=LastOnline(user),
            ),
            disable_web_page_preview=True,
        )
    else:
        await client.download_media(user_pic[0], file_name=f"./{user.id}.png")
        await message.reply_document(
            document=open(f"{user.id}.png", "rb"),
            caption=WHOIS_PIC.format(
                user_id=user.id,
                full_name=FullName(user),
                userid=user.id,
                username=user.username if user.username else "`Sin alias`",
                last_online=LastOnline(user),
                profile_pics=pic_count,
                reply_to_message_id=ReplyCheck(message),
            ),
        )
        try:
            os.remove(f"./{user.id}.png")
        except:
            LOGGER.exception("Error al remover foto de perfil")
    try:
        await buscando.delete()
    except:
        LOGGER.exception("Error al eliminar mensaje Buscando")
