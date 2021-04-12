import datetime
from typing import List

import requests
import wikipedia
from MeguRobot import CASH_API_KEY, SUPPORT_CHAT, TIME_API_KEY, dispatcher
from MeguRobot.modules.disable import DisableAbleCommandHandler
from MeguRobot.modules.helper_funcs.chat_status import bot_can_delete, user_admin
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MessageEntity,
    ParseMode,
    Update,
)
from telegram.ext import CallbackContext, CommandHandler, Filters
from wikipedia.exceptions import DisambiguationError, PageError

from nekobin import NekoBin

MARKDOWN_HELP = f"""
Markdown es una herramienta de formato muy poderosa compatible con Telegram. {dispatcher.bot.first_name} tiene algunas mejoras, para asegurarse de que
los mensajes guardados se analizen correctamente y le permitan crear botones.\n
• <code>_cursiva_</code><b>:</b> Ajustar el texto con '_' producirá texto en cursiva
• <code>*negrita*</code><b>:</b> Ajustar el texto con '*' producirá texto en negrita
• <code>`código`</code><b>:</b> Ajustar el texto con '`' producirá texto monoespaciado, también conocido como 'código'
• <code>[texto](URL)</code><b>:</b> Esto creará un enlace - el mensaje solo se verá el <code>texto</code>,
y al tocarlo se abrirá la página en <code>URL</code>.
<b>Ejemplo:</b> <code>[test](example.com)</code>
• <code>[buttontext](buttonurl:URL)</code><b>:</b> Esta es una mejora especial para permitir que los usuarios tengan botones con markdown. <code>buttontext</code> será lo que se muestra en el botón, y <code>URL</code>\
será la url que se abre.
<b>Ejemplo:</b> <code>[Este es un botón](buttonurl: example.com)</code>
Si desea varios botones en la misma línea, use :same, como tal:
<code>[uno](buttonurl://example.com)
[dos](buttonurl://google.com:same)</code>\n
Esto creará dos botones en una sola línea, en lugar de un botón por línea.
Tenga en cuenta que su mensaje <b>DEBE</b> contener algún texto que no sea solo un botón.!
"""


adventurers = f"""Megu tiene niveles de acceso de bot:

*Demonios Carmesí:* Desarrolladores que pueden acceder al servidor del bot y pueden ejecutar, editar y modificar el código del bot. También puede gestionar otros problemas.

*CrimsonDemon:* Solo existe uno, el propietario del bot.
El propietario tiene acceso completo al bot, incluida la administración del bot en los chats en los que Megu está.

*Destroyers:* Tienen acceso de superusuario, pueden banear globalmente, administrar niveles menores que ellos y son administradores en Megu.

*Demonios:* Tienen acceso al baneo global de usuarios en Megu.

*Ranas Gigantes:* Igual que los Sapos Gigantes, pero pueden deshacerse si están baneados.

*Sapos Gigantes:* No se puede banear, si hace flood se silencia o kickea, pero los administradores pueden banearlo manualmente.

*Descargo de responsabilidad:* Los *Demonios*(Soporte) de Megu sirven para solucionar problemas, brindar asistencia y prohibir a los posibles estafadores.

Informar sobre abusos o preguntarnos más sobre estos en @{SUPPORT_CHAT}.
"""


# do not async, not a handler
def send_adventurers(update):
    update.effective_message.reply_text(adventurers, parse_mode=ParseMode.MARKDOWN)


@bot_can_delete
@user_admin
def say(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message

    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1], parse_mode=ParseMode.MARKDOWN)
    else:
        message.reply_text(args[1], quote=False, parse_mode=ParseMode.MARKDOWN)
    message.delete()


def markdown_help_sender(update: Update):
    update.effective_message.reply_text(MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        "Intenta enviar el siguiente mensaje a mí, y verás, usa #test!"
    )
    update.effective_message.reply_text(
        "/save test Esta es una prueba de markdown. _cursiva_, *negrita*, `código`, "
        "[URL](ejemplo.com) [Botón](buttonurl:github.com) "
        "[Botón2](buttonurl://google.com:same)"
    )


def markdown_help(update: Update, context: CallbackContext):
    if update.effective_chat.type != "private":
        update.effective_message.reply_text(
            "Contactame en privado.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Ayuda de Markdown",
                            url=f"t.me/{context.bot.username}?start=markdownhelp",
                        )
                    ]
                ]
            ),
        )
        return
    markdown_help_sender(update)


def ud(update: Update, context: CallbackContext):
    message = update.effective_message
    text = message.text[len("/ud ") :]
    results = requests.get(
        f"https://api.urbandictionary.com/v0/define?term={text}"
    ).json()
    try:
        reply_text = f'*{text}*\n\n{results["list"][0]["definition"]}\n\n_{results["list"][0]["example"]}_'
    except:
        reply_text = "Sin resultados."
    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)


def wiki(update: Update, context: CallbackContext):
    msg = (
        update.effective_message.reply_to_message
        if update.effective_message.reply_to_message
        else update.effective_message
    )
    res = ""
    if msg == update.effective_message:
        search = msg.text.split(" ", maxsplit=1)[1]
    else:
        search = msg.text
    try:
        res = wikipedia.summary(search)
    except DisambiguationError as e:
        update.message.reply_text(
            "¡Se han encontrado páginas desambiguadas! Ajuste su busqueda en consecuencia.\n<i>{}</i>".format(
                e
            ),
            parse_mode=ParseMode.HTML,
        )
    except PageError as e:
        update.message.reply_text(
            "<code>{}</code>".format(e), parse_mode=ParseMode.HTML
        )
    if res:
        result = f"<b>{search}</b>\n\n"
        result += f"<i>{res}</i>\n"
        result += f"""<a href="https://es.wikipedia.org/wiki/{search.replace(" ", "%20")}">Leer más...</a>"""
        if len(result) > 4000:
            with open("result.txt", "w") as f:
                f.write(f"{result}\n\nUwU OwO OmO UmU")
            with open("result.txt", "rb") as f:
                context.bot.send_document(
                    document=f,
                    filename=f.name,
                    reply_to_message_id=update.message.message_id,
                    chat_id=update.effective_chat.id,
                    parse_mode=ParseMode.HTML,
                )
        else:
            update.message.reply_text(
                result, parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )


def convert(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(" ")

    if len(args) == 4:
        try:
            orig_cur_amount = float(args[1])

        except ValueError:
            update.effective_message.reply_text("Cantidad de moneda no válida")
            return

        orig_cur = args[2].upper()

        new_cur = args[3].upper()

        request_url = (
            f"https://www.alphavantage.co/query"
            f"?function=CURRENCY_EXCHANGE_RATE"
            f"&from_currency={orig_cur}"
            f"&to_currency={new_cur}"
            f"&apikey={CASH_API_KEY}"
        )
        response = requests.get(request_url).json()
        try:
            current_rate = float(
                response["Realtime Currency Exchange Rate"]["5. Exchange Rate"]
            )
        except KeyError:
            update.effective_message.reply_text("Moneda no admitida.")
            return
        new_cur_amount = round(orig_cur_amount * current_rate, 5)
        update.effective_message.reply_text(
            f"{orig_cur_amount} {orig_cur} = {new_cur_amount} {new_cur}"
        )

    elif len(args) == 1:
        update.effective_message.reply_text(
            "*Ejemplo:*"
            "  `/cash 1 USD INR`"
            "        O          "
            "  `/cash 1 usd inr`"
            "*Salida:* `1.0 USD = 75.505 INR`",
            parse_mode=ParseMode.MARKDOWN,
        )

    else:
        update.effective_message.reply_text(
            f"*Argumentos no válidos!:* Requerido 3 pero aprobado {len(args) -1}",
            parse_mode=ParseMode.MARKDOWN,
        )


def generate_time(to_find: str, findtype: List[str]) -> str:
    data = requests.get(
        f"https://api.timezonedb.com/v2.1/list-time-zone"
        f"?key={TIME_API_KEY}"
        f"&format=json"
        f"&fields=countryCode,countryName,zoneName,gmtOffset,timestamp,dst"
    ).json()

    for zone in data["zones"]:
        for eachtype in findtype:
            if to_find in zone[eachtype].lower():
                country_name = zone["countryName"]
                country_zone = zone["zoneName"]
                country_code = zone["countryCode"]

                if zone["dst"] == 1:
                    daylight_saving = "Yes"
                else:
                    daylight_saving = "No"

                date_fmt = r"%d-%m-%Y"
                time_fmt = r"%H:%M:%S"
                day_fmt = r"%A"
                gmt_offset = zone["gmtOffset"]
                timestamp = datetime.datetime.now(
                    datetime.timezone.utc
                ) + datetime.timedelta(seconds=gmt_offset)
                current_date = timestamp.strftime(date_fmt)
                current_time = timestamp.strftime(time_fmt)
                current_day = timestamp.strftime(day_fmt)

                break

    try:
        result = (
            f"<b>Pais:</b> <code>{country_name}</code>\n"
            f"<b>Nombre de zona:</b> <code>{country_zone}</code>\n"
            f"<b>Código de Pais:</b> <code>{country_code}</code>\n"
            f"<b>Horario de verano:</b> <code>{daylight_saving}</code>\n"
            f"<b>Día:</b> <code>{current_day}</code>\n"
            f"<b>Tiempo actual:</b> <code>{current_time}</code>\n"
            f"<b>Fecha actual:</b> <code>{current_date}</code>\n"
            '<b>Zonas horarias:</b> <a href="https://en.wikipedia.org/wiki/List_of_tz_database_time_zones">Lista aquí</a>'
        )
    except:
        result = None

    return result


def gettime(update: Update, context: CallbackContext):
    message = update.effective_message

    try:
        query = message.text.strip().split(" ", 1)[1]
    except:
        message.reply_text(
            "Dame un nombre/abreviatura/zona horaria del país para buscar."
        )
        return
    send_message = message.reply_text(
        f"Buscando información de zona horaria para <b>{query}</b>",
        parse_mode=ParseMode.HTML,
    )

    query_timezone = query.lower()
    if len(query_timezone) == 2:
        result = generate_time(query_timezone, ["countryCode"])
    else:
        result = generate_time(query_timezone, ["zoneName", "countryName"])

    if not result:
        send_message.edit_text(
            f"La información de zona horaria no está disponible para <b>{query}</b>\n"
            '<b>Todas las zonas horarias:</b> <a href="https://en.wikipedia.org/wiki/List_of_tz_database_time_zones">Lista aquí</a>',
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return

    send_message.edit_text(
        result, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


__help__ = """
*Comandos disponibles:*

*Markdown:*
 •`/markdownhelp`: resumen rápido de cómo funciona Markdown en Telegram - solo se puede llamar en chats privados

*Pegar:*
 •`/paste`: Guarda el contenido respondido en `nekobin.com` y responde con una URL.
 •`/dogbin`: Guarda el contenido respondido en `del.dog` y responde con una URL.

*Urban Dictonary(ENG):*
 •`/ud <palabra>`: Escriba la palabra o expresión que desea utilizar para la búsqueda

*Wikipedia:*
 •`/wiki <query>`: Busca en Wikipedia

*Tiempo:*
•`/time <lugar>`: Da información sobre una zona horaria, 🕐 [Lista de Zonas Horarias](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

*Convertidor de moneda:*
 •`/cash`: Convertidor de moneda
*Ejemplo:*
  `/cash 1 USD INR`
        O
  `/cash 1 usd inr`
*Salida:* `1.0 USD = 75.505 INR`
"""

SAY_HANDLER = DisableAbleCommandHandler(
    "say", say, filters=Filters.chat_type.groups, run_async=True
)
MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help, run_async=True)
WIKI_HANDLER = DisableAbleCommandHandler("wiki", wiki, run_async=True)
UD_HANDLER = DisableAbleCommandHandler("ud", ud, run_async=True)
CONVERTER_HANDLER = CommandHandler("cash", convert, run_async=True)
TIME_HANDLER = DisableAbleCommandHandler("time", gettime, run_async=True)

dispatcher.add_handler(SAY_HANDLER)
dispatcher.add_handler(WIKI_HANDLER)
dispatcher.add_handler(UD_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(CONVERTER_HANDLER)
dispatcher.add_handler(TIME_HANDLER)


__mod_name__ = "Extras"
__command_list__ = ["say", "markdownhelp", "wiki", "ud", "cash", "time"]
__handlers__ = [
    SAY_HANDLER,
    MD_HELP_HANDLER,
    WIKI_HANDLER,
    UD_HANDLER,
    CONVERTER_HANDLER,
    TIME_HANDLER,
]
