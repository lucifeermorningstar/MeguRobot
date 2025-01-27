import html

from MeguRobot import SUDO_USERS, dispatcher
from MeguRobot.modules.disable import DisableAbleCommandHandler
from MeguRobot.modules.helper_funcs.alternate import send_message
from MeguRobot.modules.helper_funcs.chat_status import (
    ADMIN_CACHE,
    bot_admin,
    can_pin,
    can_promote,
    connection_status,
    user_admin,
)
from MeguRobot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from MeguRobot.modules.log_channel import loggable
from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters
from telegram.utils.helpers import mention_html, escape_markdown


@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def promote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = chat.get_member(user.id)

    if (
        not (promoter.can_promote_members or promoter.status == "creator")
        and not user.id in SUDO_USERS
    ):
        message.reply_text("No tienes los derechos necesarios para hacer eso!")
        return

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "No parece que se refiera a un usuario o el ID especificado es incorrecto."
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status == "administrator" or user_member.status == "creator":
        message.reply_text(
            "¿Cómo se supone que debo ascender a alguien que ya es administrador?"
        )
        return

    if user_id == bot.id:
        message.reply_text(
            "No puedo ascenderme! Necesito a un administrador para que lo haga por mí."
        )
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            # can_promote_members=bot_member.can_promote_members,
            can_manage_voice_chats=bot_member.can_manage_voice_chats,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text("No puedo ascender a alguien que no está en el grupo.")
        else:
            message.reply_text("Ocurrió un error al ascender.")
        return

    bot.sendMessage(
        chat.id,
        f"<b>{user_member.user.first_name or user_id}</b> ascendido exitosamente!",
        parse_mode=ParseMode.HTML,
    )

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#Ascendido\n"
        f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Usuario:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message


@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def demote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "No parece que se refiera a un usuario o el ID especificado es incorrecto."
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status == "creator":
        message.reply_text("Esta persona CREÓ el grupo ¿Cómo la rebajaría?")
        return

    if not user_member.status == "administrator":
        message.reply_text("No puedo rebajar a alguien que no se ascendió!")
        return

    if user_id == bot.id:
        message.reply_text(
            "No puedo rebajarme! Necesito a un administrador para que lo haga por mí."
        )
        return

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_manage_voice_chats=False,
            can_promote_members=False,
        )

        bot.sendMessage(
            chat.id,
            f"<b>{user_member.user.first_name or user_id}</b> rebajado exitosamente!",
            parse_mode=ParseMode.HTML,
        )

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#Rebajado\n"
            f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Usuario:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message
    except BadRequest:
        message.reply_text(
            "No puedo rebajar. Puede que no tenga administrador o que el estado de administrador fue designado por otro "
            "administrador, por lo que no puedo actuar!"
        )
        return


@user_admin
def refresh_admin(update, _):
    try:
        ADMIN_CACHE.pop(update.effective_chat.id)
    except KeyError:
        pass

    update.effective_message.reply_text("Lista de administradores actualizada!")


@connection_status
@bot_admin
@can_promote
@user_admin
def set_title(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message

    user_id, title = extract_user_and_text(message, args)
    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if not user_id:
        message.reply_text(
            "No parece que se esté refiriendo a un usuario o el ID especificado es incorrecto."
        )
        return

    if user_member.status == "creator":
        message.reply_text(
            "Esta persona CREÓ el chat, cómo puedo configurar un título personalizado para él?"
        )
        return

    if not user_member.status == "administrator":
        message.reply_text(
            "No se puede establecer un título a quienes no son administradores!\nAsciendalo primero para poder establecer un título personalizado!"
        )
        return

    if user_id == bot.id:
        message.reply_text(
            "No puedo establecer mi propio título! Haz que el que me hizo administrador lo haga por mí."
        )
        return

    if not title:
        message.reply_text("Establecer un título en blanco no cambiará nada!")
        return

    if len(title) > 16:
        message.reply_text(
            "La longitud del título es superior a 16 caracteres.\nRebajalo a 16 caracteres."
        )

    try:
        bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
    except BadRequest:
        message.reply_text(
            "No puedo establecer un título personalizado para administradores que no ascendí!"
        )
        return

    bot.sendMessage(
        chat.id,
        f"Se estableció correctamente el título de <code>{user_member.user.first_name or user_id}</code> "
        f"a <code>{html.escape(title[:16])}</code>!",
        parse_mode=ParseMode.HTML,
    )


@bot_admin
@user_admin
def chat_title(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    bot = context.bot
    title = " ".join(args)
    if not title:
        message.reply_text("Establecer un título en blanco no cambiará nada!")
        return
    if len(title) > 255:
        message.reply_text(
            "La longitud del título es superior a 255 caracteres.\nRebajalo a 255 caracteres."
        )
        return

    bot.set_chat_title(chat.id, title=title)
    bot.send_message(
        chat.id,
        f"Se estableció correctamente el titulo del grupo a:\n <code>{html.escape(title[:255])}</code>!",
        parse_mode=ParseMode.HTML,
    )


@bot_admin
@can_pin
@user_admin
@loggable
def pin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    user = update.effective_user
    chat = update.effective_chat

    is_group = chat.type != "private" and chat.type != "channel"
    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = not (
            args[0].lower() == "notify"
            or args[0].lower() == "loud"
            or args[0].lower() == "violent"
        )

    if prev_message and is_group:
        try:
            bot.pinChatMessage(
                chat.id, prev_message.message_id, disable_notification=is_silent
            )
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#Fijado\n"
            f"<b>Administrador:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )

        return log_message


@bot_admin
@can_pin
@user_admin
@loggable
def unpin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    pinned = msg.reply_to_message.message_id

    try:
        bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise
    except:
        bot.unpinChatMessage(chat.id, pinned)

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#Desfijado\n"
        f"<b>Administrador:</b> {mention_html(user.id, html.escape(user.first_name))}"
    )

    return log_message


@bot_admin
@can_pin
@user_admin
@loggable
def unpinall(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user

    try:
        bot.unpinAllChatMessages(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise
    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#DesfijadoTotal\n"
        f"<b>Administrador:</b> {mention_html(user.id, html.escape(user.first_name))}"
    )

    return log_message


@bot_admin
@user_admin
@connection_status
def invite(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat

    if chat.username:
        update.effective_message.reply_text(f"https://t.me/{chat.username}")
    elif chat.type == chat.SUPERGROUP or chat.type == chat.CHANNEL:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text(
                "No tengo acceso al enlace de invitación, intenta modificar mis permisos!"
            )
    else:
        update.effective_message.reply_text(
            "Solo puedo darte enlaces de invitación para supergrupos y canales, lo siento!"
        )


@connection_status
def adminlist(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    bot = context.bot

    if update.effective_message.chat.type == "private":
        send_message(update.effective_message, "Este comando sólo funciona en grupos.")
        return
    try:
        msg = update.effective_message.reply_text(
            "Obteniendo administradores del grupo...", parse_mode=ParseMode.HTML
        )
    except BadRequest:
        msg = update.effective_message.reply_text(
            "Obteniendo administradores del grupo...",
            quote=False,
            parse_mode=ParseMode.HTML,
        )

    administrators = bot.getChatAdministrators(chat.id)
    text = "Administradores en <b>{}</b>:\n".format(html.escape(chat.title))

    for admin in administrators:
        user = admin.user
        status = admin.status
        custom_title = admin.custom_title

        if user.first_name == "":
            name = "☠ <b>Cuenta Eliminada</b>"
        elif user.username:
            name = escape_markdown("@" + user.username)
        else:
            name = "{}".format(
                mention_html(
                    user.id, html.escape(user.first_name + " " + (user.last_name or ""))
                )
            )
        if user.is_bot:
            administrators.remove(admin)
            continue

        if status == "creator":
            text += "\n 👑 <b>Propietario:</b>"
            text += "\n<b> └ </b>{}".format(name)

            if custom_title:
                text += f" » <code>{html.escape(custom_title)}</code>\n"
            else:
                text += "\n"

    text += "\n🔱 <b>Administradores:</b>"

    custom_admin_list = {}
    normal_admin_list = []

    for admin in administrators:
        user = admin.user
        status = admin.status
        custom_title = admin.custom_title

        if user.first_name == "":
            name = "☠ Cuenta Eliminada"
        elif user.username:
            name = escape_markdown("@" + user.username)
        else:
            name = "{}".format(
                mention_html(
                    user.id, html.escape(user.first_name + " " + (user.last_name or ""))
                )
            )
        if status == "administrator":
            if custom_title:
                try:
                    custom_admin_list[custom_title].append(name)
                except KeyError:
                    custom_admin_list.update({custom_title: [name]})
            else:
                normal_admin_list.append(name)

    for admin in normal_admin_list:
        text += "\n<b> ├ </b>{}".format(admin)

    for admin_group in custom_admin_list.copy():
        if len(custom_admin_list[admin_group]) == 1:
            text += "\n<b> ├ </b>{} » <code>{}</code>".format(
                custom_admin_list[admin_group][0], html.escape(admin_group)
            )
            custom_admin_list.pop(admin_group)

    text += "\n"
    for admin_group in custom_admin_list:
        text += "\n🚨 <code>{}</code>".format(admin_group)
        for admin in custom_admin_list[admin_group]:
            text += "\n<b> ├ </b>{}".format(admin)
        text += "\n"
    try:
        text = text.replace("\_", "_")
        msg.edit_text(text, parse_mode=ParseMode.HTML)
    except BadRequest:  # if original message is deleted
        return


__help__ = """
 • `/admins`: Lista de administradores en el chat
 
*Solo administradores:*

 •`/pin`: Fija silenciosamente el mensaje al que respondió - agregue` 'loud'` o `' notify'` para dar notificaciones a los usuarios.
 •`/unpin`: Quita el mensaje anclado actualmente.
 •`/unpinall`: Quita las mensajes anclados actualmente.
 •`/link`: Obtén el link del grupo.
 •`/promote`: Promueve al usuario al que respondió.
 •`/demote`: Rebaja al usuario al que respondió.
 •`/title`: Establece un título personalizado para un administrador que promovió el bot.
 •`/setchattitle`: Cambia el titulo del chat.
 •`/admincache`: Actúaliza la lista de administradores.
"""

ADMINLIST_HANDLER = DisableAbleCommandHandler("admins", adminlist, run_async=True)

PIN_HANDLER = CommandHandler(
    "pin", pin, filters=Filters.chat_type.groups, run_async=True
)
UNPIN_HANDLER = CommandHandler(
    "unpin", unpin, filters=Filters.chat_type.groups, run_async=True
)
UNPINALL_HANDLER = CommandHandler(
    "unpinall", unpinall, filters=Filters.chat_type.groups, run_async=True
)

INVITE_HANDLER = DisableAbleCommandHandler("link", invite, run_async=True)
PROMOTE_HANDLER = DisableAbleCommandHandler("promote", promote, run_async=True)
DEMOTE_HANDLER = DisableAbleCommandHandler("demote", demote, run_async=True)
SET_TITLE_HANDLER = DisableAbleCommandHandler("title", set_title, run_async=True)
SET_CHAT_TITLE = DisableAbleCommandHandler("setchattitle", chat_title, run_async=True)
ADMIN_REFRESH_HANDLER = CommandHandler(
    "admincache", refresh_admin, filters=Filters.chat_type.groups, run_async=True
)

dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(UNPINALL_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(SET_TITLE_HANDLER)
dispatcher.add_handler(SET_CHAT_TITLE)
dispatcher.add_handler(ADMIN_REFRESH_HANDLER)

__mod_name__ = "Admin"
__command_list__ = [
    "adminlist",
    "admins",
    "invitelink",
    "promote",
    "demote",
    "admincache",
]
__handlers__ = [
    ADMINLIST_HANDLER,
    PIN_HANDLER,
    UNPIN_HANDLER,
    UNPINALL_HANDLER,
    INVITE_HANDLER,
    PROMOTE_HANDLER,
    DEMOTE_HANDLER,
    SET_TITLE_HANDLER,
    SET_CHAT_TITLE,
    ADMIN_REFRESH_HANDLER,
]
