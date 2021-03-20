from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from MeguRobot.utils import filters
from MeguRobot import pyrogrm

from MeguRobot.modules.whois import whois
from MeguRobot.modules.reverse import google_rs
from MeguRobot.modules.telegraph import telegraph
from MeguRobot.modules.spbinfo import lookup
from MeguRobot.modules.usage import usage
from MeguRobot.modules.whatanime import whatanime
from MeguRobot.modules.purge import purge_messages, delete_message
from MeguRobot.modules.downanime import downanime, search_episodes, download_episode


handlers = [
    MessageHandler(whois, filters.command("whois")),
    MessageHandler(telegraph, filters.command("telegraph")),
    MessageHandler(google_rs, filters.command("reverse")),
    MessageHandler(lookup, filters.command("spbinfo")),
    MessageHandler(usage, filters.command("usage") & filters.dev),
    MessageHandler(whatanime, filters.command("whatanime")),
    MessageHandler(purge_messages, filters.command("purge") & filters.admin & filters.dev & filters.sudo),
    MessageHandler(delete_message, filters.command("del") & filters.admin & filters.dev & filters.sudo),
    MessageHandler(downanime, filters.command("downanime")),
    CallbackQueryHandler(search_episodes, filters.regex("^title_.*$")),
    CallbackQueryHandler(download_episode, filters.regex("^episode_.*$"))
]

for handler in handlers:
    pyrogrm.add_handler(handler)

__command_list__ = [
    "whois",
    "telegraph",
    "reverse",
    "spbinfo",
    "usage",
    "whatanime",
    "purge",
    "del",
    "downanime",
]
