import time

from MeguRobot import pyrogrm
from MeguRobot.modules.helper_funcs.pyrogrm import admincheck


async def purge_messages(client, message):
    if message.chat.type not in ("supergroup", "channel"):
        return
    is_admin = await admin_check(message)
    if not is_admin:
        await client.send_message(
            message.chat.id, "Solo los administradores pueden usar este comando."
        )
        return
    start_t = datetime.now()
    await message.delete()
    message_ids = []
    count_del_etion_s = 0
    if not message.reply_to_message:
        await client.send_message(
            message.chat.id,
            "Responde a un mensaje para seleccionar desde dónde empezar a eliminar.",
        )
    if message.reply_to_message:
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
    end_t = datetime.now()
    time_taken_ms = (end_t - start_t).seconds
    ms_g = await client.send_message(
        message.chat.id,
        f"Se eliminaron {count_del_etion_s} mensajes en {time_taken_ms} segundos",
    )
    await asyncio.sleep(5)
    await ms_g.delete()


async def delete_message(client, message):
    msg_ids = [message.message_id]
    is_admin = await admin_check(message)
    if not is_admin:
        await client.send_message(
            message.chat.id, "Solo los administradores pueden usar este comando."
        )
    
    if not message.reply_to_message:
        client.send_message(message.chat.id, "Que quieres eliminar?")
    if message.reply_to_message:
        msg_ids.append(message.reply_to_message.message_id)
    await client.delete_messages(message.chat.id, msg_ids)



__help__ = """
*Solo administradores:*
 •`/del`*:* Elimina el mensaje al que respondió
 •`/purge`*:* Elimina todos los mensajes entre este y el mensaje respondido.
 •`/purge <X>`*:* Elimina el mensaje respondido y los X mensajes que lo siguen si respondieron a un mensaje.
"""


__mod_name__ = "Eliminacion"
