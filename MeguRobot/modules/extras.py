import datetime
from typing import List

from MeguRobot.modules.helper_funcs.chat_status import user_admin
from MeguRobot.modules.disable import DisableAbleCommandHandler
from MeguRobot import dispatcher, SUPPORT_CHAT, CASH_API_KEY, TIME_API_KEY, telethn

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import MessageEntity, ParseMode, Update
from telegram.ext import CallbackContext, Filters, CommandHandler

from telethon import events
from telethon.tl import types, functions
from telethon.events.newmessage import NewMessage


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

*Descargo de responsabilidad*: Los *Demonios*(Soporte) de Megu sirven para solucionar problemas, brindar asistencia y prohibir a los posibles estafadores.

Informar sobre abusos o preguntarnos más sobre estos en @{SUPPORT_CHAT}.
"""


# do not async, not a handler
def send_adventurers(update):
    update.effective_message.reply_text(adventurers, parse_mode=ParseMode.MARKDOWN)


@user_admin
def say(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message

    if message.reply_to_message:
        message.reply_to_message.reply_text(
            args[1], parse_mode="MARKDOWN", disable_web_page_preview=True
        )
    else:
        message.reply_text(
            args[1], quote=False, parse_mode="MARKDOWN", disable_web_page_preview=True
        )
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
            "Contactame en privado",
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


dogheaders = {
    "Content-type": "text/plain",
    "Accept": "application/json",
    "charset": "utf-8",
}


async def deldog(event: NewMessage.Event) -> None:
    match = event.pattern_match.group(1)
    if match:
        text = match.strip()
    elif event.reply_to_msg_id:
        reply = await event.get_reply_message()
        text = reply.raw_text
        if reply.document and reply.document.mime_type.startswith("text"):
            text = await reply.download_media(file=bytes)
    else:
        await event.reply("Dame algo para copiar", link_preview=False)
        return
    response = requests.post(
        "https://del.dog/documents",
        data=text.encode("UTF-8") if isinstance(text, str) else text,
        headers=dogheaders,
    )
    if not response.ok:
        await event.reply(
            "No se pudo copiar a [DelDog](https://del.dog/)", link_preview=False
        )
        return
    key = response.json()["key"]
    await event.reply(f"Copiado a [DelDog](https://del.dog/{key})", link_preview=False)


def paste(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message

    if message.reply_to_message:
        data = message.reply_to_message.text

    elif len(args) >= 1:
        data = message.text.split(None, 1)[1]

    else:
        message.reply_text("Qué se supone que debo hacer con esto?")
        return

    key = (
        requests.post("https://nekobin.com/api/documents", json={"content": data})
        .json()
        .get("result")
        .get("key")
    )

    url = f"https://nekobin.com/{key}"

    reply_text = f"Copiado a *Nekobin* : {url}"

    message.reply_text(
        reply_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
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
        update.effective_message.reply_text(__help__, parse_mode=ParseMode.MARKDOWN)

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
•`/time <lugar>: Da información sobre una zona horaria, 🕐 [Lista de Zonas Horarias](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

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
PASTE_HANDLER = DisableAbleCommandHandler("paste", paste, run_async=True)
CONVERTER_HANDLER = CommandHandler("cash", convert, run_async=True)
TIME_HANDLER = DisableAbleCommandHandler("time", gettime, run_async=True)

dispatcher.add_handler(SAY_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(PASTE_HANDLER)
dispatcher.add_handler(CONVERTER_HANDLER)
dispatcher.add_handler(TIME_HANDLER)


DOGBIN_HANDLER = deldog, events.NewMessage(pattern="^[!/]dogbin(?: |$|\n)([\s\S]*)")
telethn.add_event_handler(*DOGBIN_HANDLER)


__mod_name__ = "Extras"
__command_list__ = ["say", "markdownhelp", "cash", "dogbin", "time"]
__handlers__ = [
    SAY_HANDLER,
    MD_HELP_HANDLER,
    CONVERTER_HANDLER,
    DOGBIN_HANDLER,
    TIME_HANDLER,
]
