import shlex

from pyrogram.filters import *
from pyrogram.types import Message

from MeguRobot import BOT_USERNAME, SUDO_USERS, DEV_USERS, pyrogrm


def command(
    commands: str or List[str],
    prefixes: str or List[str] = "/",
    case_sensitive: bool = False,
):
    """
    This is a drop in replacement for the default Filters.command that is included
    in Pyrogram. The Pyrogram one does not support /command@botname type commands,
    so this custom filter enables that throughout all groups and private chats.
    This filter works exactly the same as the original command filter even with support for multiple command
    prefixes and case sensitivity.
    Command arguments are given to user as message.command
    """

    async def func(flt, _, message: Message):
        text: str = message.text or message.caption
        message.command = None

        if not text:
            return False

        regex = "^({prefix})+\\b({regex})\\b(\\b@{bot_name}\\b)?(.*)".format(
            prefix="|".join(re.escape(x) for x in flt.prefixes),
            regex="|".join(flt.commands),
            bot_name=BOT_USERNAME,
        )

        matches = re.search(re.compile(regex), text)
        if matches:
            message.command = [matches.group(2)]
            for arg in shlex.split(matches.group(4).strip()):
                message.command.append(arg)
            return True
        else:
            return False

    commands = commands if type(commands) is list else [commands]
    commands = {c if case_sensitive else c.lower() for c in commands}

    prefixes = [] if prefixes is None else prefixes
    prefixes = prefixes if type(prefixes) is list else [prefixes]
    prefixes = set(prefixes) if prefixes else {""}

    return create(
        func,
        "CustomCommandFilter",
        commands=commands,
        prefixes=prefixes,
        case_sensitive=case_sensitive,
    )


async def admin_filter(_, __, m: Message):
    user = await m.chat.get_member(m.from_user.id)
    user_id = m.from_user.id
    is_admin = user.status == "administrator" or user.status == "creator"
    is_sudo = user_id in SUDO_USERS
    if is_admin or is_sudo:
        return True
    if not is_admin:
        await pyrogrm.send_message(
            m.chat.id, "Solo los administradores pueden usar este comando"
        )
        return False


admin = create(admin_filter)


async def sudo_filter(_, __, m: Message):
    if m.from_user.id in SUDO_USERS:
        return True


sudo = create(sudo_filter)


async def dev_filter(_, __, m: Message):
    if m.from_user.id in DEV_USERS:
        return True


dev = create(dev_filter)
