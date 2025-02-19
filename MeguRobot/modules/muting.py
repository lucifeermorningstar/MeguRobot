import html
from typing import Optional

from MeguRobot import FROG_USERS, LOGGER, dispatcher
from MeguRobot.modules.helper_funcs.chat_status import (
    bot_admin,
    can_restrict,
    connection_status,
    is_user_admin,
    user_admin,
)
from MeguRobot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from MeguRobot.modules.helper_funcs.string_handling import extract_time
from MeguRobot.modules.log_channel import loggable
from telegram import Bot, Chat, ChatPermissions, ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler
from telegram.utils.helpers import mention_html


def check_user(user_id: int, bot: Bot, chat: Chat) -> Optional[str]:
    if not user_id:
        reply = (
            "No parece que se refiera a un usuario o el ID especificado es incorrecto.."
        )
        return reply

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            reply = "Parece que no puedo encontrar a este usuario"
            return reply
        else:
            raise

    if user_id == bot.id:
        reply = "No me voy a callar, que tan alto estás?"
        return reply

    if is_user_admin(chat, user_id, member) or user_id in FROG_USERS:
        reply = """Realmente desearía poder mutear a los administradores... Quizás un "explosion"?"""
        return reply

    return None


@connection_status
@bot_admin
@user_admin
@loggable
def mute(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = extract_user_and_text(message, args)
    reply = check_user(user_id, bot, chat)

    if reply:
        message.reply_text(reply)
        return ""

    member = chat.get_member(user_id)

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#Muteado\n"
        f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Usuario:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    if reason:
        log += f"\n<b>Razón:</b> {reason}"

    if member.can_send_messages is None or member.can_send_messages:
        chat_permissions = ChatPermissions(can_send_messages=False)
        bot.restrict_chat_member(chat.id, user_id, chat_permissions)
        bot.sendMessage(
            chat.id,
            f"Silenciado <b>{html.escape(member.user.first_name)}</b> sin tiempo de desmuteado!",
            parse_mode=ParseMode.HTML,
        )
        return log

    else:
        message.reply_text("Este usuario ya está muteado!")

    return ""


@connection_status
@bot_admin
@user_admin
@loggable
def unmute(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "Debes darme un nombre de usuario o responder a alguien para desmutearlo."
        )
        return ""

    member = chat.get_member(int(user_id))

    if member.status != "kicked" and member.status != "left":
        if (
            member.can_send_messages
            and member.can_send_media_messages
            and member.can_send_other_messages
            and member.can_add_web_page_previews
        ):
            message.reply_text("Este usuario ya está desmuteado.")
        else:
            chat_permissions = ChatPermissions(
                can_send_messages=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_send_polls=True,
                can_change_info=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
            bot.restrict_chat_member(chat.id, int(user_id), chat_permissions)
            bot.sendMessage(
                chat.id,
                f"<b>{html.escape(member.user.first_name)}</b> desmuteado",
                parse_mode=ParseMode.HTML,
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#Desmuteado\n"
                f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>Usuario:</b> {mention_html(member.user.id, member.user.first_name)}"
            )
    else:
        message.reply_text(
            "Este usuario ni siquiera está en el chat, mutearlo no hará efecto."
        )

    return ""


@connection_status
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_mute(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = extract_user_and_text(message, args)
    reply = check_user(user_id, bot, chat)

    if reply:
        message.reply_text(reply)
        return ""

    member = chat.get_member(user_id)

    if not reason:
        message.reply_text("No has especificado un tiempo para mutear a este usuario.!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = extract_time(message, time_val)

    if not mutetime:
        return ""

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#SilenciadoTemporal\n"
        f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Usuario:</b> {mention_html(member.user.id, member.user.first_name)}\n"
        f"<b>Tiemppo:</b> {time_val}"
    )
    if reason:
        log += f"\n<b>Razón:</b> {reason}"

    try:
        if member.can_send_messages is None or member.can_send_messages:
            chat_permissions = ChatPermissions(can_send_messages=False)
            bot.restrict_chat_member(
                chat.id, user_id, chat_permissions, until_date=mutetime
            )
            bot.sendMessage(
                chat.id,
                f"<b>{html.escape(member.user.first_name)}</b> muteado por {time_val}!",
                parse_mode=ParseMode.HTML,
            )
            return log
        else:
            message.reply_text("Este usuario ya está muteado.")

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(f"Silenciado por {time_val}!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR muting user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Bueno maldita sea, no puedo mutear a ese usuario.")

    return ""


__help__ = """
*Solo administradores:*

 •`/mute <usuario>`: Silencia (mutea) a un usuario. Se puede utilizar con ID, alias o respondiendo al usuario.
 •`/tmute <usuario> x(m/h/d)`: Mutea a un usuario por x tiempo. (a través del identificador o respuesta). `m`=`minutos`, `h`=`horas`, `d`=`días`.
 •`/unmute <userhandle>`: Desmutea a un usuario. Se puede utilizar con ID, alias o respondiendo al usuario.
"""

MUTE_HANDLER = CommandHandler("mute", mute, run_async=True)
UNMUTE_HANDLER = CommandHandler("unmute", unmute, run_async=True)
TEMPMUTE_HANDLER = CommandHandler(["tmute", "tempmute"], temp_mute, run_async=True)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
dispatcher.add_handler(TEMPMUTE_HANDLER)

__mod_name__ = "Muteo"
__handlers__ = [MUTE_HANDLER, UNMUTE_HANDLER, TEMPMUTE_HANDLER]
__command_list__ = ["mute", "tmute", "unmute", "tempmute"]
