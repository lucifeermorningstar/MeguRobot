# Create a new config.py or rename this to config.py file in same dir and import, then extend this class.
import json
import os


def get_user_list(config, key):
    with open("{}/MeguRobot/{}".format(os.getcwd(), config), "r") as json_file:
        return json.load(json_file)[key]


# Create a new config.py or rename this to config.py file in same dir and import, then extend this class.
class Config(object):
    LOGGER = True
    # REQUIRED
    # Login to https://my.telegram.org and fill in these slots with the details given by it

    API_ID = 123456  # integer value, dont use ""
    API_HASH = "xd"
    TOKEN = "BOT_TOKEN"  # This var used to be API_KEY but it is now TOKEN, adjust accordingly.
    OWNER_ID = 1178259323  # If you dont know, run the bot and do /id in your private chat with it, also an integer
    OWNER_USERNAME = "CrimsonDemon"
    SUPPORT_CHAT = "MeguSupport"  # Your own group for support, do not add the @
    JOIN_LOGGER = (
        -1001335261915
    )  # Prints any new group the bot is added to, prints just the name and ID.
    GLOBAL_LOGS = (
        -1001191829350
    )  # Prints information like gbans, sudo promotes, AI enabled disable states that may help in debugging and shit
    DEV_GROUP = -1001183292794

    # RECOMMENDED
    SQLALCHEMY_DATABASE_URI = "something://somewhat:user@hosturl:port/databasename"  # needed for any database modules
    LOAD = []
    NO_LOAD = ["cleaner", "connection"]
    WEBHOOK = False
    INFOPIC = True
    URL = None
    SPAMWATCH_API = ""  # go to support.spamwat.ch to get key

    # OPTIONAL
    ##List of id's -  (not usernames) for users which have sudo access to the bot.
    SUDO_USERS = get_user_list("elevated_users.json", "sudos")
    ##List of id's - (not usernames) for developers who will have the same perms as the owner
    DEV_USERS = get_user_list("elevated_users.json", "devs")
    ##List of id's (not usernames) for users which are allowed to gban, but can also be banned.
    SUPPORT_USERS = get_user_list("elevated_users.json", "supports")
    # List of id's (not usernames) for users which WONT be banned/kicked by the bot.
    FROG_USERS = get_user_list("elevated_users.json", "frogs")
    WHITELIST_USERS = get_user_list("elevated_users.json", "whitelists")
    DONATION_LINK = None  # EG, paypal
    CERT_PATH = None
    PORT = 5000
    DEL_CMDS = True  # Delete commands that users dont have access to, like delete /ban if a non admin uses it.
    STRICT_GBAN = True
    WORKERS = (
        8  # Number of subthreads to use. Set as number of threads your processor uses
    )
    BAN_STICKER = "STICKER_ID"  # banhammer marie sticker id, the bot will send this sticker before banning or kicking a user in chat.
    ALLOW_EXCL = True  # Allow ! commands as well as / (Leave this to true so that blacklist can work)
    CUSTOM_CMD = True  # Allow ! . commands as well as / (Leave this to true so that blacklist can work)
    CASH_API_KEY = (
        "API"  # Get your API key from https://www.alphavantage.co/support/#api-key
    )
    TIME_API_KEY = "API"  # Get your API key from https://timezonedb.com/api
    WALL_API_KEY = (
        "API"  # For wallpapers, get one from https://wall.alphacoders.com/api.php
    )
    AI_API_KEY = (
        "API"  # For chatbot, get one from https://coffeehouse.intellivoid.net/dashboard
    )
    HEROKU_API = None
    BL_CHATS = []  # List of groups that you want blacklisted.
    SPAMMERS = get_user_list("elevated_users.json", "spammers")
    LASTFM_API_KEY = None
    BOT_USERNAME = "MeguRobot"


class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
