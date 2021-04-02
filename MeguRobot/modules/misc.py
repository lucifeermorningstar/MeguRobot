import html
import re
import os
import requests
import datetime
import platform

from platform import python_version
from telegram import MAX_MESSAGE_LENGTH, ParseMode, Update, __version__
from telegram.ext import CallbackContext, CommandHandler
from telegram.error import BadRequest
from telegram.utils.helpers import escape_markdown, mention_html

from MeguRobot.__main__ import STATS, TOKEN, USER_INFO
from MeguRobot.modules.disable import DisableAbleCommandHandler
import MeguRobot.modules.sql.userinfo_sql as sql
from MeguRobot.modules.sql.global_bans_sql import is_user_gbanned
from MeguRobot.modules.sql.afk_sql import is_afk, check_afk_status
from MeguRobot.modules.sql.users_sql import get_user_num_chats
from MeguRobot.modules.sql.feds_sql import get_user_fbanlist
from MeguRobot.modules.helper_funcs.extraction import extract_user
from psutil import cpu_percent, virtual_memory, disk_usage, boot_time


def no_by_per(totalhp, percentage):
    """
    rtype: num of `percentage` from total
    eg: 1000, 10 -> 10% of 1000 (100)
    """
    return totalhp * percentage / 100


def get_percentage(totalhp, earnedhp):
    """
    rtype: percentage of `totalhp` num
    eg: (1000, 100) will return 10%
    """

    matched_less = totalhp - earnedhp
    per_of_totalhp = 100 - matched_less * 100.0 / totalhp
    per_of_totalhp = str(int(per_of_totalhp))
    return per_of_totalhp


def hpmanager(user):
    total_hp = (get_user_num_chats(user.id) + 10) * 10

    if not is_user_gbanned(user.id):

        # Assign new var `new_hp` since we need `total_hp` in
        # end to calculate percentage.
        new_hp = total_hp

        # if no username decrease 25% of hp.
        if not user.username:
            new_hp -= no_by_per(total_hp, 25)
        try:
            dispatcher.bot.get_user_profile_photos(user.id).photos[0][-1]
        except IndexError:
            # no profile photo ==> -25% of hp
            new_hp -= no_by_per(total_hp, 25)
        # if no /setme exist ==> -20% of hp
        if not sql.get_user_me_info(user.id):
            new_hp -= no_by_per(total_hp, 20)
        # if no bio exsit ==> -10% of hp
        if not sql.get_user_bio(user.id):
            new_hp -= no_by_per(total_hp, 10)

        if is_afk(user.id):
            afkst = check_afk_status(user.id)
            # if user is afk and no reason then decrease 7%
            # else if reason exist decrease 5%
            if not afkst.reason:
                new_hp -= no_by_per(total_hp, 7)
            else:
                new_hp -= no_by_per(total_hp, 5)

        # fbanned users will have (2*number of fbans) less from max HP
        # Example: if HP is 100 but user has 5 diff fbans
        # Available HP is (2*5) = 10% less than Max HP
        # So.. 10% of 100HP = 90HP

        _, fbanlist = get_user_fbanlist(user.id)
        new_hp -= no_by_per(total_hp, 2 * len(fbanlist))

    # Bad status effects:
    # gbanned users will always have 5% HP from max HP
    # Example: If HP is 100 but gbanned
    # Available HP is 5% of 100 = 5HP

    else:
        new_hp = no_by_per(total_hp, 5)

    return {
        "earnedhp": int(new_hp),
        "totalhp": int(total_hp),
        "percentage": get_percentage(total_hp, new_hp),
    }


def make_bar(per):
    done = min(round(per / 10), 10)
    return "█" * done + "▒" * (10 - done)


def info(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    user_id = extract_user(update.effective_message, args)

    if user_id:
        user = bot.get_chat(user_id)

    elif not message.reply_to_message and not args:
        user = message.from_user

    elif not message.reply_to_message and (
        not args
        or (
            len(args) >= 1
            and not args[0].startswith("@")
            and not args[0].isdigit()
            and not message.parse_entities([MessageEntity.TEXT_MENTION])
        )
    ):
        message.reply_text("No puedo extraer un usuario de esto.")
        return

    else:
        return

    rep = message.reply_text("Buscando...")

    text = (
        f"<b>Información:</b>\n"
        f"<b>ID:</b> <code>{user.id}</code>\n"
        f"<b>Nombre:</b> {html.escape(user.first_name)} "
    )

    if user.last_name:
        text += f"{html.escape(user.last_name)}"

    if user.username:
        text += f"\n<b>Alías:</b> <code>{html.escape(user.username)}</code>"

    if chat.type != "private" and user_id != bot.id:
        _stext = "\n<b>Presencia:</b> <code>{}</code>"

        afk_st = is_afk(user.id)
        if afk_st:
            text += _stext.format("AFK")
        else:
            status = status = bot.get_chat_member(chat.id, user.id).status
            if status:
                if status in {"left", "kicked"}:
                    text += _stext.format("Ausente")
                elif status == "member":
                    text += _stext.format("Presente")
                elif status in {"administrator"}:
                    text += _stext.format("Administrador")
                elif status in {"creator"}:
                    text += _stext.format("Propietario")
    if user_id != bot.id:
        userhp = hpmanager(user)
        text += f"\n<b>Vida:</b> <code>{userhp['earnedhp']}/{userhp['totalhp']}</code>\n »{make_bar(int(userhp['percentage']))}« "
        text += f"[{userhp['percentage']}%] "
        text += '» [<a href="https://t.me/MeguRobotChannel/7">Info</a>]'

    try:
        spamwtc = sw.get_ban(int(user.id))
        if spamwtc:
            text += "\n\n<b>Esta persona está vigilada por Spam!</b>"
            text += f"\n<b>Razón:</b> \n<pre>{spamwtc.reason}</pre>"
            text += "\n<b>Apelar en @SpamWatchSupport</b>"
        else:
            pass
    except:
        pass  # don't crash if api is down somehow...

    disaster_level_present = False

    if user.id == OWNER_ID:
        text += "\n\n<b>Es Kazuma.</b>"
        disaster_level_present = True
    elif user.id in DEV_USERS:
        text += "\n\nEste usuario es un <b>Demonio Carmesí</b>."
        disaster_level_present = True
    elif user.id in SUDO_USERS:
        text += "\n\nEste usuario es un <b>Destroyer</b>."
        disaster_level_present = True
    elif user.id in SUPPORT_USERS:
        text += "\n\nEste usuario es un <b>Demonio</b>."
        disaster_level_present = True
    elif user.id in FROG_USERS:
        text += "\n\nEste usuario es una <b>Rana Gigante</b>."
        disaster_level_present = True
    elif user.id in WHITELIST_USERS:
        text += "\n\nEste usuario es un <b>Sapo Gigante</b>."
        disaster_level_present = True

    if disaster_level_present:
        text += ' »[<a href="https://t.me/{}?start=adventurers">Info</a>]'.format(
            bot.username
        )

    try:
        user_member = chat.get_member(user.id)
        if user_member.status == "administrator":
            result = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={chat.id}&user_id={user.id}"
            )
            result = result.json()["result"]
            if "custom_title" in result.keys():
                custom_title = result["custom_title"]
                text += f"\n<b>Título:</b> <code>{custom_title}</code>"
    except BadRequest:
        pass

    for mod in USER_INFO:
        try:
            mod_info = mod.__user_info__(user.id).strip()
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    if INFOPIC:
        try:
            profile = bot.get_user_profile_photos(user.id).photos[0][-1]
            _file = bot.get_file(profile["file_id"])
            _file.download(f"{user.id}.png")

            message.reply_document(
                document=open(f"{user.id}.png", "rb"),
                caption=(text),
                parse_mode=ParseMode.HTML,
            )

            os.remove(f"{user.id}.png")
        # Incase user don't have profile pic, send normal text
        except IndexError:
            message.reply_text(
                text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )

    else:
        message.reply_text(
            text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )

    rep.delete()


@sudo_plus
def stats(update: Update, context: CallbackContext):
    stats = "<b>Estadísticas actuales:</b>\n\n" + "\n".join(
        [mod.__stats__() for mod in STATS]
    )
    result = re.sub(r"(\d+)", r"<code>\1</code>", stats)
    update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)


def get_id(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    msg = update.effective_message
    user_id = extract_user(msg, args)

    if user_id:

        if msg.reply_to_message and msg.reply_to_message.forward_from:

            user1 = message.reply_to_message.from_user
            user2 = message.reply_to_message.forward_from

            msg.reply_text(
                f"<b>Telegram IDs:</b>\n"
                f"• {html.escape(user2.first_name)} - <code>{user2.id}</code>.\n"
                f"• {html.escape(user1.first_name)} - <code>{user1.id}</code>.",
                parse_mode=ParseMode.HTML,
            )

        else:

            user = bot.get_chat(user_id)
            msg.reply_text(
                f"<b>El ID de {html.escape(user.first_name)} es:</b> <code>{user.id}</code>.",
                parse_mode=ParseMode.HTML,
            )

    else:

        if chat.type == "private":
            msg.reply_text(
                f"<b>Tu ID es:</b> <code>{chat.id}</code>.", parse_mode=ParseMode.HTML
            )

        else:
            msg.reply_text(
                f"<b>El ID de este grupo es:</b> <code>{chat.id}</code>.",
                parse_mode=ParseMode.HTML,
            )


def gifid(update: Update, context: CallbackContext):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.animation:
        update.effective_message.reply_text(
            f"GIF ID:\n<code>{msg.reply_to_message.animation.file_id}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        update.effective_message.reply_text("Responde a un gif para obtener su ID.")


def sisinfo(update: Update, context: CallbackContext):
    uptime = datetime.datetime.fromtimestamp(boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    status = "*>-------< Sistema >-------<*\n"
    status += "*T.A del sistema:* " + str(uptime) + "\n"

    uname = platform.uname()
    status += "*Sistema:* " + str(uname.system) + "\n"
    status += "*Nombre de nodo:* " + str(uname.node) + "\n"
    status += "*Versión:* " + str(uname.release) + "\n"
    status += "*Máquina:* " + str(uname.machine) + "\n"

    mem = virtual_memory()
    cpu = cpu_percent()
    disk = disk_usage("/")
    status += "*Uso de CPU:* " + str(cpu) + " %\n"
    status += "*Uso de RAM:* " + str(mem[2]) + " %\n"
    status += "*Espacio en uso:* " + str(disk[3]) + " %\n\n"
    status += "*Python:* " + python_version() + "\n"
    status += "*Versíon de Libreria:* " + str(__version__) + "\n"
    
    update.effective_message.reply_text(status)
    



INFO_HANDLER = DisableAbleCommandHandler("info", info, pass_args=True, run_async=True)
STATS_HANDLER = CommandHandler("stats", stats, run_async=True)
ID_HANDLER = DisableAbleCommandHandler("id", get_id, run_async=True)
GIFID_HANDLER = DisableAbleCommandHandler("gifid", gifid, run_async=True)


dispatcher.add_handler(INFO_HANDLER, STATS_HANDLER, ID_HANDLER, GIFID_HANDLER)

__mod_name__ = "Misceláneo"
__command_list__ = ["info", "id", "stats", "gifid"]
__handlers__ = [INFO_HANDLER, STATS_HANDLER, GIFID_HANDLER, ID_HANDLER]
