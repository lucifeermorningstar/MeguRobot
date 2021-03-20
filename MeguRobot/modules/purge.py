import asyncio
import time

from pyrogram import errors
from MeguRobot import pyrogrm
from MeguRobot.modules.helper_funcs.pyrogrm.admincheck import admin_check


async def purge_messages(client, message):
    if message.chat.type not in ("supergroup", "channel"):
        return
    start_t = time.perf_counter()
    message_ids = []
    count_del_etion_s = 0
    if not message.reply_to_message:
        await client.send_message(
            message.chat.id,
            "Responde a un mensaje para seleccionar desde dónde empezar a eliminar.",
        )
    elif message.reply_to_message:
        try:
            for a_s_message_id in range(
                message.reply_to_message.message_id,
                message.message_id,
            ):
                message_ids.append(a_s_message_id)
                if len(message_ids) == 100:
                    await client.delete_messages(
                        chat_id=message.chat.id,
                        message_ids=message_ids,
                        revoke=True,
                    )
                    count_del_etion_s += len(message_ids)
                    message_ids = []
            if message_ids:
                await client.delete_messages(
                    chat_id=message.chat.id,
                    message_ids=message_ids,
                    revoke=True,
                )
                count_del_etion_s += len(message_ids)
                end_t = time.perf_counter()
                time_taken_ms = end_t - start_t
                ms_g = await client.send_message(
                    message.chat.id,
                    f"Se eliminaron {count_del_etion_s} mensajes en {time_taken_ms:0.2f} segundos",
                )
                await message.delete()
        except errors.exceptions.forbidden_403.MessageDeleteForbidden:
            await client.send_message(
                message.chat.id, "No tengo derechos para borrar mensajes."
            )


async def delete_message(client, message):
    msg_ids = [message.message_id]
    if not message.reply_to_message:
        await client.send_message(message.chat.id, "Que quieres eliminar?")
    if message.reply_to_message:
        try:
            msg_ids.append(message.reply_to_message.message_id)
            await client.delete_messages(message.chat.id, msg_ids)
        except errors.exceptions.forbidden_403.MessageDeleteForbidden:
            await client.send_message(
                message.chat.id, "No tengo derechos para borrar el mensaje."
            )


__help__ = """
*Solo administradores:*
 •`/del`*:* Elimina el mensaje al que respondió
 •`/purge`*:* Elimina todos los mensajes entre este y el mensaje respondido.
 •`/purge <X>`*:* Elimina el mensaje respondido y los X mensajes que lo siguen si respondieron a un mensaje.
"""


__mod_name__ = "Eliminacion"
