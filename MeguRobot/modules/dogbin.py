import requests

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


DOGBIN_HANDLER = deldog, events.NewMessage(pattern="^[!/]dogbin(?: |$|\n)([\s\S]*)")
telethn.add_event_handler(*DOGBIN_HANDLER)

__command_list__ = ["dogbin"]

__handlers__ = [DOGBIN_HANDLER]
