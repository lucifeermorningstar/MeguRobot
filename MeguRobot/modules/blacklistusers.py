# Module to blacklist users and prevent them from using commands by @TheRealPhoenix
import os
import MeguRobot.modules.sql.blacklistusers_sql as sql
from MeguRobot import (
    DEV_USERS,
    FROG_USERS,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    WHITELIST_USERS,
    dispatcher,
)
from MeguRobot.modules.helper_funcs.chat_status import dev_plus
from MeguRobot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from MeguRobot.modules.log_channel import gloggable
from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler
from telegram.utils.helpers import mention_html

BLACKLISTWHITELIST = (
    [OWNER_ID] + DEV_USERS + SUDO_USERS + WHITELIST_USERS + SUPPORT_USERS
)
BLABLEUSERS = [OWNER_ID] + DEV_USERS


@dev_plus
@gloggable
def bl_user(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Dudo que sea un usuario.")
        return ""

    if user_id == bot.id:
        message.reply_text(
            "Cómo se supone que debo hacer mi trabajo si me ignoro a mí misma?"
        )
        return ""

    if user_id in BLACKLISTWHITELIST:
        message.reply_text("No!\nSaber quienes son mis administradores es mi trabajo.")
        return ""

    try:
        target_user = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Parece que no puedo encontrar a este usuario.")
            return ""
        else:
            raise

    sql.blacklist_user(user_id, reason)
    message.reply_text("Ignoraré a este usuario!")
    log_message = (
        f"#ListaNegra\n"
        f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Usuario:</b> {mention_html(target_user.id, target_user.first_name)}"
    )
    if reason:
        log_message += f"\n<b>Razón:</b> {reason}"

    return log_message


@dev_plus
@gloggable
def unbl_user(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text("Dudo que sea un usuario.")
        return ""

    if user_id == bot.id:
        message.reply_text("Siempre me doy cuenta de mi misma.")
        return ""

    try:
        target_user = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Parece que no puedo encontrar a este usuario.")
            return ""
        else:
            raise

    if sql.is_user_blacklisted(user_id):

        sql.unblacklist_user(user_id)
        message.reply_text("Usuario quitado de la lista negra")
        log_message = (
            f"#QuitaListaNegra\n"
            f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Usuario:</b> {mention_html(target_user.id, target_user.first_name)}"
        )

        return log_message

    else:
        message.reply_text("Sin embargo, no lo estoy ignorando en absoluto!")
        return ""


@dev_plus
def bl_users(update: Update, context: CallbackContext):
    users = []
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    for each_user in sql.BLACKLIST_USERS:
        user = bot.get_chat(each_user)
        reason = sql.get_reason(each_user)

        if reason:
            users.append(f"• {user.id}, {user.first_name} :- {reason}")
        else:
            users.append(f"• {user.id}, {user.first_name}")

    message = "<b>Usuarios incluidos en la Lista Negra:</b>\n"
    if not users:
        message += "\nNadie está siendo ignorado por el momento."
        msg.reply_text(message, parse_mode=ParseMode.HTML)
    else:
        try:
            blusers = message + "\n".join(users)
            msg.reply_text(blusers, parse_mode=ParseMode.HTML)
        except:
            blusers = message + "\n".join(users)
            with open("BLUsers.txt", "w") as f:
                f.write(blusers)
            with open("BLUsers.txt", "rb") as output:
                bot.send_document(
                    chat.id,
                    document=output,
                    filename="BLUsers.txt",
                    caption=message,
                    parse_mode=ParseMode.HTML,
                )
            os.remove("BLUsers.txt")


def __user_info__(user_id):
    is_blacklisted = sql.is_user_blacklisted(user_id)

    text = "<b>Lista Negra:</b> <code>{}</code>"
    if user_id in [777000, 1087968824]:
        return ""
    if user_id == dispatcher.bot.id:
        return ""
    if int(user_id) in SUDO_USERS + FROG_USERS + WHITELIST_USERS:
        return ""
    if is_blacklisted:
        text = text.format("Si")
        reason = sql.get_reason(user_id)
        if reason:
            text += f"\nRazón: <code>{reason}</code>"
    else:
        text = text.format("No")

    return text


BL_HANDLER = CommandHandler("ignore", bl_user, run_async=True)
UNBL_HANDLER = CommandHandler("notice", unbl_user, run_async=True)
BLUSERS_HANDLER = CommandHandler("ignoredlist", bl_users, run_async=True)

dispatcher.add_handler(BL_HANDLER)
dispatcher.add_handler(UNBL_HANDLER)
dispatcher.add_handler(BLUSERS_HANDLER)

__mod_name__ = "BlackList de Usuarios"
__handlers__ = [BL_HANDLER, UNBL_HANDLER, BLUSERS_HANDLER]
__command_list__ = ["ignore", "notice", "ignoredlist"]
