import sys
import traceback
from functools import wraps

from MeguRobot import DEV_GROUP, pyrogrm
from MeguRobot.utils.parser import split_limits


def capture_err(func):
    @wraps(func)
    async def capture(client, message, *args, **kwargs):
        try:
            return await func(client, message, *args, **kwargs)
        except Exception as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            errors = traceback.format_exception(
                etype=exc_type,
                value=exc_obj,
                tb=exc_tb,
            )
            text = "**ERROR**\n\n**Usuario:** `{}`\n**Chat:** `{}`\n**Mensaje:**\n`{}`".format(
                0 if not message.from_user else message.from_user.id,
                0 if not message.chat else message.chat.id,
                message.text or message.caption,
            )
            with open("error.txt", "w") as f:
                f.write(str(errors))
            await client.send_document(
                DEV_GROUP,
                document="error.txt",
                caption=text,
            )
            raise err

    return capture
