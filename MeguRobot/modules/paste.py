import requests
from MeguRobot import dispatcher
from MeguRobot.modules.disable import DisableAbleCommandHandler
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from telethon import events
from telethon.tl import types, functions
from telethon.events.newmessage import NewMessage
from MeguRobot import telethn


dogheaders = {
    "Content-type": "text/plain",
    "Accept": "application/json",
    "charset": "utf-8",
}


async def deldog(event: NewMessage.Event) -> None:
    """
    Pega un documento en DelDog.
    `{prefix}dogbin` en respuesta a un documento o **{prefix}dogbin (text)**
    """
    match = event.pattern_match.group(1)
    if match:
        text = match.strip()
    elif event.reply_to_msg_id:
        reply = await event.get_reply_message()
        text = reply.raw_text
        if reply.document and reply.document.mime_type.startswith("text"):
            text = await reply.download_media(file=bytes)
    else:
        await event.reply("`Dame algo para copiar` https://del.dog", link_preview=False)
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
    await event.reply(
        f"`Copiado a` [DelDog](https://del.dog/{key})", link_preview=False
    )


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


PASTE_HANDLER = DisableAbleCommandHandler("paste", paste, run_async=True)
dispatcher.add_handler(PASTE_HANDLER)


DOGBIN_HANDLER = deldog, events.NewMessage(pattern="^[!/]dogbin(?: |$|\n)([\s\S]*)")
telethn.add_event_handler(*DOGBIN_HANDLER)

__mod_name__ = "Paste"
__command_list__ = ["paste", "dogbin"]
__handlers__ = [PASTE_HANDLER, DOGBIN_HANDLER]
