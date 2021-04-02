import html
import re
import os
import requests

from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsAdmins
from telethon import events

from telegram import MAX_MESSAGE_LENGTH, ParseMode, Update
from telegram.ext import CallbackContext, CommandHandler
from telegram.error import BadRequest
from telegram.utils.helpers import escape_markdown, mention_html

from MeguRobot import (
    DEV_USERS,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    FROG_USERS,
    WHITELIST_USERS,
    INFOPIC,
    dispatcher,
    sw,
)
from MeguRobot.modules.disable import DisableAbleCommandHandler
import MeguRobot.modules.sql.userinfo_sql as sql


def about_me(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user_id = extract_user(message, args)

    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_me_info(user.id)

    if info:
        update.effective_message.reply_text(
            f"*{user.first_name}*:\n{escape_markdown(info)}",
            parse_mode=ParseMode.MARKDOWN,
        )
    elif message.reply_to_message:
        username = message.reply_to_message.from_user.first_name
        update.effective_message.reply_text(
            f"*{username}* aún no ha puesto un mensaje sobre él!",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        update.effective_message.reply_text(
            "No tienes uno, usa `/setme` para configurar uno.",
            parse_mode=ParseMode.MARKDOWN,
        )


def set_about_me(update: Update, context: CallbackContext):
    message = update.effective_message
    user_id = message.from_user.id
    bot = context.bot
    if message.reply_to_message:
        repl_message = message.reply_to_message
        repl_user_id = repl_message.from_user.id
        if repl_user_id == bot.id and (user_id in SUDO_USERS or user_id in DEV_USERS):
            user_id = repl_user_id

    text = message.text
    info = text.split(None, 1)

    if len(info) == 2:
        if len(info[1]) < MAX_MESSAGE_LENGTH // 4:
            sql.set_user_me_info(user_id, info[1])
            if user_id == bot.id:
                message.reply_text(
                    "He actualizado tu información con la que proporcionaste!"
                )
            else:
                message.reply_text("Información actualizada!")
        else:
            message.reply_text(
                "¡La información debe tener menos de {} caracteres! Tienes {}.".format(
                    MAX_MESSAGE_LENGTH // 4, len(info[1])
                )
            )


def about_bio(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    user_id = extract_user(message, args)
    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_bio(user.id)

    if info:
        update.effective_message.reply_text(
            "*{}*:\n{}".format(user.first_name, escape_markdown(info)),
            parse_mode=ParseMode.MARKDOWN,
        )
    elif message.reply_to_message:
        username = user.first_name
        update.effective_message.reply_text(
            f"*{username}* aún no ha establecido un mensaje sobre sí mismo!\nEstablezca uno usando `/setbio`",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        update.effective_message.reply_text("Aún no tienes una biografía sobre ti!")


def set_about_bio(update: Update, context: CallbackContext):
    message = update.effective_message
    sender_id = update.effective_user.id
    bot = context.bot

    if message.reply_to_message:
        repl_message = message.reply_to_message
        user_id = repl_message.from_user.id

        if user_id == message.from_user.id:
            message.reply_text(
                "No puedes establecer tu propia biografía! Estás a merced de los demás aquí..."
            )
            return

        if (
            user_id == bot.id
            and sender_id not in SUDO_USERS
            and sender_id not in DEV_USERS
        ):
            message.reply_text(
                "Erm..., solo confío en los usuarios sudo y desarrolladores para configurar mi biografía."
            )
            return

        text = message.text
        bio = text.split(
            None, 1
        )  # use python's maxsplit to only remove the cmd, hence keeping newlines.

        if len(bio) == 2:
            if len(bio[1]) < MAX_MESSAGE_LENGTH // 4:
                sql.set_user_bio(user_id, bio[1])
                message.reply_text(
                    "Se actualizó la biografía de {}!".format(
                        repl_message.from_user.first_name
                    )
                )
            else:
                message.reply_text(
                    "La biografía debe tener menos de {} caracteres! Tienes {}.".format(
                        MAX_MESSAGE_LENGTH // 4, len(bio[1])
                    )
                )
    else:
        message.reply_text("Responde a alguien para establecer su biografía!")


def __user_info__(user_id):
    bio = html.escape(sql.get_user_bio(user_id) or "")
    me = html.escape(sql.get_user_me_info(user_id) or "")
    result = ""
    if me:
        result += f"<b>Informacion:</b> {me}\n"
    if bio:
        result += f"<b>Biografia:</b> {bio}\n"
    result = result.strip("\n")
    return result


__help__ = """
*ID:*
 •`/id`: Obtiene la identificación del grupo actual. Si se usa respondiendo a un mensaje, obtiene la ID de ese usuario.
 •`/gifid`: Responde a un gif para decirte su ID de archivo.

*Información auto agregada:*
 •`/setme <text>`: Establecerá su información
 •`/me`: Obtendrá su información o la de otro usuario.
Ejemplos:
  `/setme Hola soy Megumin.`
  `/me @nombredeusuario (por defecto es el tuyo si no hay un usuario especificado)`
*Información que otros agregan sobre tí:*
 •`/bio`: Obtendrás tu biografía o la de otro usuario. Esto no lo puede configurar tú mismo.
 •`/setbio <text>`: Mientras respondes, guardará la biografía de otro usuario.
Ejemplos:
   `/bio @username (por defecto es el tuyo si no hay usuario especificado).`
   `/setbio Este usuario es un lobo`(respondiendo al usuario)

*Información general sobre tí:*
 •`/info`: Obtén información sobre un usuario(respondiendo al usuario, escribiendo su ID o alías)
 •`/whois`: Obtén información sobre un usuario con información detallada.
"""

SET_BIO_HANDLER = DisableAbleCommandHandler("setbio", set_about_bio, run_async=True)
GET_BIO_HANDLER = DisableAbleCommandHandler("bio", about_bio, run_async=True)

SET_ABOUT_HANDLER = DisableAbleCommandHandler("setme", set_about_me, run_async=True)
GET_ABOUT_HANDLER = DisableAbleCommandHandler("me", about_me, run_async=True)

dispatcher.add_handler(SET_BIO_HANDLER)
dispatcher.add_handler(GET_BIO_HANDLER)
dispatcher.add_handler(SET_ABOUT_HANDLER)
dispatcher.add_handler(GET_ABOUT_HANDLER)

__mod_name__ = "Info"
__command_list__ = [
    "setbio",
    "bio",
    "setme",
    "me",
]
__handlers__ = [
    SET_BIO_HANDLER,
    GET_BIO_HANDLER,
    SET_ABOUT_HANDLER,
    GET_ABOUT_HANDLER,
]
