import html
import os
import re

from MeguRobot import ALLOW_EXCL, CustomCommandHandler, dispatcher
from MeguRobot.modules.disable import DisableAbleCommandHandler
from MeguRobot.modules.helper_funcs.chat_status import (
    bot_can_delete,
    connection_status,
    dev_plus,
    user_admin,
)
from MeguRobot.modules.sql import cleaner_sql as sql
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler

if ALLOW_EXCL:
    CMD_STARTERS = ("/", "!", ".")
else:
    CMD_STARTERS = "/"

BLUE_TEXT_CLEAN_GROUP = 15
CommandHandlerList = (CommandHandler, CustomCommandHandler, DisableAbleCommandHandler)
command_list = [
    "cleanblue",
    "ignoreblue",
    "unignoreblue",
    "listblue",
    "ungignoreblue",
    "gignoreblue" "start",
    "help",
    "settings",
    "donate",
    "stalk",
    "aka",
    "leaderboard",
]
VALID_PATTERN = "^[a-zA-Z0-9]+$"
ya_se_unieron = False
for handler_list in dispatcher.handlers:
    for handler in dispatcher.handlers[handler_list]:
        if any(isinstance(handler, cmd_handler) for cmd_handler in CommandHandlerList):
            command_list += handler.command


def clean_blue_text_must_click(update: Update, context: CallbackContext):
    global command_list
    global ya_se_unieron
    if not ya_se_unieron:
        try:
            comandos = open("temp/comandos.txt", "r")
            comandos_string = comandos.read()
            comandos_list = comandos_string.split()
            comandos.close()
            command_list.extend(comandos_list)
            ya_se_unieron = True
            os.remove("temp/comandos.txt")
        except Exception:
            pass

    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    if chat.get_member(bot.id).can_delete_messages:
        if sql.is_enabled(chat.id):
            fst_word = message.text.strip().split(None, 1)[0]

            if len(fst_word) > 1 and any(
                fst_word.startswith(start) for start in CMD_STARTERS
            ):

                command = fst_word[1:].split("@")

                ignored = sql.is_command_ignored(chat.id, command[0])
                if ignored:
                    return

                if command[0] not in command_list:
                    message.delete()


@connection_status
@bot_can_delete
@user_admin
def set_blue_text_must_click(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    bot, args = context.bot, context.args
    if len(args) >= 1:
        val = args[0].lower()
        if val in ("off", "no"):
            sql.set_cleanbt(chat.id, False)
            reply = "La limpieza de Bluetext se ha desactivado para <b>{}</b>".format(
                html.escape(chat.title)
            )
            message.reply_text(reply, parse_mode=ParseMode.HTML)

        elif val in ("yes", "on"):
            sql.set_cleanbt(chat.id, True)
            reply = "La limpieza de bluetext se ha habilitado para <b>{}</b>".format(
                html.escape(chat.title)
            )
            message.reply_text(reply, parse_mode=ParseMode.HTML)

        else:
            reply = "Argumento no válido. Los valores aceptados son 'yes', 'on', 'no', 'off'"
            message.reply_text(reply)
    else:
        clean_status = sql.is_enabled(chat.id)
        if clean_status:
            clean_status = "Activado"
        else:
            clean_status = "Desactivado"
        reply = "Limpieza de Bluetext para <b>{}</b> : <b>{}</b>".format(
            chat.title, clean_status
        )
        message.reply_text(reply, parse_mode=ParseMode.HTML)


@user_admin
def add_bluetext_ignore(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()

        valid = re.findall(VALID_PATTERN, val)
        if not valid:
            reply = "El comando contiene carácteres inválidos."
            message.reply_text(reply)
            return

        added = sql.chat_ignore_command(chat.id, val)
        if added:
            reply = "<b>{}</b> se ha agregado a la lista de ignorados del limpiador de bluetext.".format(
                args[0]
            )
        else:
            reply = "El comando ya esta ignorado."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "Ningún comando pasado para ser ignorado."
        message.reply_text(reply)


@user_admin
def remove_bluetext_ignore(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        removed = sql.chat_unignore_command(chat.id, val)
        if removed:
            reply = "<b>{}</b> se ha eliminado de la lista de ignorados del limpiador de bluetext.".format(
                args[0]
            )
        else:
            reply = "El comando no se ignora actualmente."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "No se pasó ningún comando para ser ignorado."
        message.reply_text(reply)


@user_admin
def add_bluetext_ignore_global(update: Update, context: CallbackContext):
    message = update.effective_message
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()

        valid = re.findall(VALID_PATTERN, val)
        if not valid:
            reply = "El comando contiene carácteres inválidos."
            message.reply_text(reply)
            return

        added = sql.global_ignore_command(val)
        if added:
            reply = "<b>{}</b> se ha agregado a la lista de ignorados del limpiador de bluetext global.".format(
                args[0]
            )
        else:
            reply = "El comando ya se ignora."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "Ningún comando pasado para ser ignorado."
        message.reply_text(reply)


@dev_plus
def remove_bluetext_ignore_global(update: Update, context: CallbackContext):
    message = update.effective_message
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        removed = sql.global_unignore_command(val)
        if removed:
            reply = "<b>{}</b> se ha eliminado de la lista de ignorados del limpiador de bluetext global.".format(
                args[0]
            )
        else:
            reply = "El comando no se ignora actualmente."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "No se pasó ningún comando para ser ignorado."
        message.reply_text(reply)


@dev_plus
def bluetext_ignore_list(update: Update, context: CallbackContext):

    message = update.effective_message
    chat = update.effective_chat

    global_ignored_list, local_ignore_list = sql.get_all_ignored(chat.id)
    text = ""

    if global_ignored_list:
        text = "Los siguientes comandos se ignoran actualmente globalmente desde la limpieza de bluetext:\n"

        for x in global_ignored_list:
            text += f" - <code>{x}</code>\n"

    if local_ignore_list:
        text += "\nLos siguientes comandos se ignoran actualmente localmente desde la limpieza de bluetext :\n"

        for x in local_ignore_list:
            text += f" - <code>{x}</code>\n"

    if text == "":
        text = "Actualmente no se ignoran los comandos de la limpieza de bluetext."
        message.reply_text(text)
        return

    message.reply_text(text, parse_mode=ParseMode.HTML)
    return


__help__ = """
El limpiador de bluetext elimina los comandos inventados que las personas envían en su chat.

 •`/cleanblue <on/off/yes/no>`: Limpiar comandos después de enviar
 •`/ignoreblue <palabra>`: Evita la limpieza automática del comando
 •`/unignoreblue <palabra>`: Quita evitar la limpieza automática del comando
 •`/listblue`: Lista los comandos actualmente incluidos en la lista blanca
"""

__command_list__ = [
    "cleanblue",
    "ignoreblue",
    "unignoreblue",
    "listblue",
    "gignoreblue",
    "ungignoreblue",
]

SET_CLEAN_BLUE_TEXT_HANDLER = CommandHandler(
    "cleanblue", set_blue_text_must_click, run_async=True
)
ADD_CLEAN_BLUE_TEXT_HANDLER = CommandHandler(
    "ignoreblue", add_bluetext_ignore, run_async=True
)
REMOVE_CLEAN_BLUE_TEXT_HANDLER = CommandHandler(
    "unignoreblue", remove_bluetext_ignore, run_async=True
)
ADD_CLEAN_BLUE_TEXT_GLOBAL_HANDLER = CommandHandler(
    "gignoreblue", add_bluetext_ignore_global, run_async=True
)
REMOVE_CLEAN_BLUE_TEXT_GLOBAL_HANDLER = CommandHandler(
    "ungignoreblue", remove_bluetext_ignore_global, run_async=True
)
LIST_CLEAN_BLUE_TEXT_HANDLER = CommandHandler(
    "listblue", bluetext_ignore_list, run_async=True
)
CLEAN_BLUE_TEXT_HANDLER = MessageHandler(
    Filters.command & Filters.chat_type.groups,  # regex(r"^[/.!]\w")
    clean_blue_text_must_click,
    run_async=True,
)

dispatcher.add_handler(SET_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(ADD_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(REMOVE_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(ADD_CLEAN_BLUE_TEXT_GLOBAL_HANDLER)
dispatcher.add_handler(REMOVE_CLEAN_BLUE_TEXT_GLOBAL_HANDLER)
dispatcher.add_handler(LIST_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(CLEAN_BLUE_TEXT_HANDLER, BLUE_TEXT_CLEAN_GROUP)

__mod_name__ = "Cleaner"
__handlers__ = [
    SET_CLEAN_BLUE_TEXT_HANDLER,
    ADD_CLEAN_BLUE_TEXT_HANDLER,
    REMOVE_CLEAN_BLUE_TEXT_HANDLER,
    ADD_CLEAN_BLUE_TEXT_GLOBAL_HANDLER,
    REMOVE_CLEAN_BLUE_TEXT_GLOBAL_HANDLER,
    LIST_CLEAN_BLUE_TEXT_HANDLER,
    (CLEAN_BLUE_TEXT_HANDLER, BLUE_TEXT_CLEAN_GROUP),
]
