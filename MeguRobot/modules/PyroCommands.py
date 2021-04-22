from MeguRobot import pyrogrm
from MeguRobot.modules.anime import (
    anime_airing,
    anime_search,
    character_search,
    manga_search,
    downanime,
    download_episode,
    search_episodes,
    confirm_dowload,
)
from MeguRobot.modules.nekobin import get_paste_, paste
from MeguRobot.modules.purge import delete_message, purge_messages
from MeguRobot.modules.reverse import google_rs
from MeguRobot.modules.spbinfo import lookup
from MeguRobot.modules.telegraph import telegraph
from MeguRobot.modules.usage import usage
from MeguRobot.modules.whatanime import whatanime
from MeguRobot.modules.whois import whois
from MeguRobot.modules.lastfm import set_user, clear_user, last_fm, get_yt
from MeguRobot.utils import filters
from pyrogram.handlers import CallbackQueryHandler, MessageHandler

handlers = [
    MessageHandler(whois, filters.command("whois")),
    MessageHandler(telegraph, filters.command("telegraph")),
    MessageHandler(google_rs, filters.command("reverse")),
    MessageHandler(lookup, filters.command("spbinfo")),
    MessageHandler(usage, filters.command("usage") & filters.dev),
    MessageHandler(whatanime, filters.command("whatanime")),
    MessageHandler(purge_messages, filters.command("purge") & filters.admin),
    MessageHandler(delete_message, filters.command("del") & filters.admin),
    MessageHandler(downanime, filters.command("downanime")),
    CallbackQueryHandler(search_episodes, filters.regex("^title_.*$")),
    CallbackQueryHandler(confirm_dowload, filters.regex("^episode_.*$")),
    CallbackQueryHandler(download_episode, filters.regex("^download_.*$")),
    MessageHandler(anime_airing, filters.command("airing")),
    MessageHandler(anime_search, filters.command("anime")),
    MessageHandler(character_search, filters.command("character")),
    MessageHandler(manga_search, filters.command("manga")),
    MessageHandler(paste, filters.command("paste")),
    MessageHandler(get_paste_, filters.command("gpaste")),
    MessageHandler(set_user, filters.command("setuser")),
    MessageHandler(clear_user, filters.command("clearuser")),
    MessageHandler(last_fm, filters.command("lastfm")),
    CallbackQueryHandler(get_yt, filters.regex("^get_music_.*$")),
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
    "airing",
    "anime",
    "character",
    "manga",
    "paste",
    "gpaste",
    "setuser",
    "clearuser",
    "lastfm",
]
