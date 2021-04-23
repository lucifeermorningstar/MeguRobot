import os
import subprocess
import sys
from time import sleep

from MeguRobot import dispatcher
from MeguRobot.modules.helper_funcs.chat_status import dev_plus
from telegram import TelegramError, Update
from telegram.ext import CallbackContext, CommandHandler


@dev_plus
def leave(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if args:
        chat_id = str(args[0])
        try:
            bot.leave_chat(int(chat_id))
            update.effective_message.reply_text("Beep boop, dejé ese grupo!.")
        except TelegramError:
            update.effective_message.reply_text(
                "Parece que no estoy en ese grupo..."
            )
    else:
        update.effective_message.reply_text("Envíame un ID de chat válido")


@dev_plus
def gitpull(update: Update, context: CallbackContext):
    sent_msg = update.effective_message.reply_text(
        "Extrayendo todos los cambios e intentando reiniciar."
    )
    subprocess.Popen("git pull", stdout=subprocess.PIPE, shell=True)

    sent_msg_text = (
        sent_msg.text + "\n\nCambios Realizados... Eso creo.. Reiniciando en "
    )

    for i in reversed(range(5)):
        sent_msg.edit_text(sent_msg_text + str(i + 1))
        sleep(1)

    sent_msg.edit_text("Reiniciado.")

    os.system("restart.bat")
    os.execv("start.bat", sys.argv)


@dev_plus
def restart(update: Update, context: CallbackContext):
    update.effective_message.reply_text("Iniciando una nueva instancia y cerrando esta")

    os.system("restart.bat")
    os.execv("start.bat", sys.argv)


LEAVE_HANDLER = CommandHandler("leave", leave, run_async=True)
GITPULL_HANDLER = CommandHandler("gitpull", gitpull, run_async=True)
RESTART_HANDLER = CommandHandler("restart", restart, run_async=True)

dispatcher.add_handler(LEAVE_HANDLER)
dispatcher.add_handler(GITPULL_HANDLER)
dispatcher.add_handler(RESTART_HANDLER)

__mod_name__ = "Dev"
__handlers__ = [LEAVE_HANDLER, GITPULL_HANDLER, RESTART_HANDLER]
__command_list__ = ["leave", "gitpull", "restart"]
