import html
import random
import time

from MeguRobot import dispatcher
from MeguRobot.modules.disable import DisableAbleCommandHandler
from MeguRobot.modules.helper_funcs.chat_status import is_user_admin
from MeguRobot.modules.helper_funcs.extraction import extract_user
from telegram import ParseMode, Update, ChatPermissions
from telegram.ext import CallbackContext


runs_templates = (
    "Ahora me ves, ahora no",
    "ε=ε=ε=ε=┌(;￣ ▽￣)┘",
    "¡Regresa aquí!",
    "¡Cuidado con la pared!",
    "¡¡No me dejes solo con ellos!!",
    "¡Tienes compañía!",
    "¡Chotto mate!",
    "Yare yare daze",
    "*Naruto Run activado*",
    "*Nezuko run activado*",
    "¡Oye, hazte responsable de lo que acabas de hacer!",
    "Que las probabilidades estén siempre a tu favor.",
    "Corran todos, acaban de lanzar una bomba 💣💣",
    "Y desaparecieron para siempre, nunca más se los volvió a ver",
    "Hasta la vista baby.",
    "Como diría el Doctor... ¡CORRE!",
)

slap_megu_templates = (
    "Dame una bofetada más y te mutearé",
    [
        "Te estoy silenciando por un minuto :3",  # respuesta normal
        "Deja de abofetearme solo porque no puedo silenciarte.",  # Responder al administrador
        "tmute",  # comando
        "¡Cállate!",
        "¡Silencio!",
    ],
)

slap_templates = (
    "{user2} fue asesinado por arte de magia",
    "{user2} murió de hambre sin caricias",
    "{user2} fue derribado por {user1}.",
    "{user2} se desmayó",
    "¡{user2} se ha quedado sin Pokémon utilizable! ¡{user2} se ha agotado!",
    "¡{user2} no tiene Pokémon utilizables! ¡{user2} se desmayó!",
    "El melón de {user2} fue dividido por {user1}.",
    "{user2} fue cortado y cortado en cubitos por {user1}.",
    "{user2} jugó a la patata caliente con una granada.",
    "{user2} fue apuñalado por {user1}.",
    "{user2} se comió una granada",
    "¡{user2} es lo que hay para cenar!",
    "{user1} envió spam al correo electrónico de {user2}.",
    "{user1} puso a {user2} en la friendzone",
    "¡{user1} abofetea a {user2} con una solicitud de eliminación de DMCA!",
    "{user2} recibió una visita domiciliaria del doctor {user1}.",
    "{user1} decapitó a {user2}.",
    "{user2} se apedreó... por una turba furiosa",
    "{user1} demandó a {user2}.",
    "{user2} fue KO de un golpe por {user1}.",
    "{user1} envió a {user2} por el agujero de la memoria",
    "{user2} fue un error. - '{user1}'",
    "{user2} fue despedido.",
    "¡{user1} {hits} a {user2} con un bate!",
    "¡{user1} {hits} a {user2} con una patada de Taijutsu!.",
    "{user1} {hits} a {user2} con X-Gloves!.",
    "{user1} {hits} a {user2} with a Jet Punch!.",
    "¡{user1} {hits} a {user2} con una pistola Jet!.",
    "{user1} {hits} a {user2} con un United States of Smash!.",
    "¡{user1} {hits} a {user2} con un Detroit Smash!.",
    "{user1} {hits} a {user2} con un Texas Smash!.",
    "{user1} {hits} a {user2} con un California Smash!.",
    "{user1} {hits} a {user2} con un New Hampshire Smash!.",
    "{user1} {hits} a {user2} con un Missouri Smash!.",
    "{user1} {hits} a {user2} con un Carolina Smash!.",
    "¡{user1} {hits} a {user2} con una pistola King Kong!.",
    "{user1} {hits} a {user2} con un bate de béisbol, ¡uno de metal!",
    "*Serios golpes a {user2}*.",
    "*Punzones normales a {user2} *.",
    "*Punzones normales consecutivos a {user2}*.",
    "*Golpes normales consecutivos a dos manos a {user2}*.",
    "*Ignora a {user2} para dejar que muera de vergüenza*.",
    "*Señala a {user2} * ¿Qué pasa con este descarado... niño perdido?",
    "*Golpea a {user2} con un Tornado de fuego*.",
    "¡{user1} golpea a {user2} en el ojo!",
    "¡{user1} golpea a {user2} en los costados!",
    "¡{user1} empuja a {user2}!",
    "¡{user1} pincha a {user2} con una aguja!",
    "¡{user1} pincha a {user2} con un bolígrafo!",
    "¡{user1} golpea a {user2} con una pistola paralizante!",
    "¡{user2} es secretamente un furro! >:3",
    "¡Hola a todos! ¡{user1} me está pidiendo que sea mala!",
    "( ･_･)ﾉ⌒●~* (･.･;) <- {user2}",
    "Toma este {user2}\n(ﾉ ﾟ Д ﾟ)ﾉ))))●~*",
    "Aquí {user2} mantén presionado este\n(｀・ω・)つ●~＊",
    "( ・_・)ノΞ●~* {user2} \nMueré!!.",
    "( ・∀・)ｒ鹵~<≪巛;ﾟДﾟ)ﾉ\n*Aerosoles de insectos a {user2}*.",
    "( ﾟДﾟ)ﾉ占~<巛巛巛.\n- {user2} ¡Eres una plaga!",
    "( う-´)づ︻╦̵̵̿╤── \(˚☐˚”)/ {user2}. ",
    "{user1} {hits} {user2} con un {item}.",
    "{user1} {hits} {user2} en la cara con un {item}.",
    "{user1} {hits} {user2} alrededor un poco con un {item}.",
    "{user1} {lanza} un {item} a {user2}.",
    "{user1} agarra un {item} y {lo arroja} a la cara de {user2}.",
    "{user1} lanza un {item} en la dirección general de {user2}.",
    "{user1} comienza a abofetear a {user2} tontamente con un {item}.",
    "{user1} fija a {user2} y repetidamente {los golpea} con un {item}.",
    "{user1} agarra un {item} y {hits} {user2} con él.",
    "{user1} ata a {user2} a una silla y {lanza} un {item} hacia ellos.",
    "{user1} dio un empujón amistoso para ayudar a {user2} a aprender a nadar en lava",
    "{user1} acosó a {user2}.",
    "Nyaan se comió la pierna de {user2}. *Nomnomnom*",
    "{user1} lanza una bola maestra a {user2}, la resistencia es inútil.",
    "{user1} golpea a {user2} con un rayo de acción... bbbbbb (ง ・ ω ・)ง ====*",
    "{user1} ara ara's a {user2}.",
    "{user1} ora ora's a {user2}.",
    "{user1} muda muda's a {user2}.",
    "¡{user2} se convirtió en una Jojo referencia!",
    "{user1} golpeó a {user2} con un {item}.",
    "¡Ronda 2! ..¿Listo?.. ¡¡LUCHA!!",
    "WhoPixel saldrá de {user2}, hasta el infinito y más allá",
    "{user2} se comió un murciélago y descubrió una nueva enfermedad",
    "{user1} dobló a {user2} en un avión de papel",
    "{user2} hizo un 69 con un cactus",
    "{user1} le sirvió a {user2} sopa de murciélago.",
    "{user2} fue enviado a su casa, el planeta de los simios",
    "{user1} echó a {user2} de un tren en movimiento",
    "{user1} viajó al futuro y escupió en la tumba de {user2}.",
    "{user2} murió de talk-no-jutsu.",
    "{user2} se colocó como alfombra para una competencia de baile de pisotones",
    "{user2} acaba de matar al perro de John Wick",
    "{user1} realizó un hechizo Avada Kadavra en {user2}.",
    "{user1} sometió a {user2} a un horno de fuego.",
    "Sakura Haruno se volvió más útil que {user2}",
    "{user1} desconectó el soporte vital de {user2}.",
    "{user2} se suscribió a 5 años de mal Internet",
    "¿Sabes qué es peor que los chistes de papá? ¡{User2}!",
    "{user2} wa mou....... ¡Shindeiru! - {user1}.",
    "¡{user2} perdió su pieza de ajedrez!",
    "Cállate {user2}, solo eres {user2}.",
    "¡{user1} golpea a {user2} con Aka si anse!",
)

items = (
    "sartén de hierro fundido",
    "neko enojado",
    "Bate de cricket",
    "bastón de madera",
    "libro",
    "ordenador portátil",
    "pollo de goma",
    "murciélago con púas",
    "trozo de tierra",
    "tonelada de ladrillos",
    "rasengan",
    "bomba espiritual",
    "Bodhisattva Guanyin de tipo 100",
    "rasenshuriken",
    "Murasame",
    "banea",
    "chunchunmaru",
    "Kubikiribōchō",
    "rasengan",
)

throws = (
    "aventuras",
    "mandriles",
    "lanza",
)

hits = (
    "bofeteó",
    "golpeó",
    "palmeó",
)

eyes = [
    ["⌐■", "■"],
    [" ͠°", " °"],
    ["⇀", "↼"],
    ["´• ", " •`"],
    ["´", "`"],
    ["`", "´"],
    ["ó", "ò"],
    ["ò", "ó"],
    ["⸌", "⸍"],
    [">", "<"],
    ["Ƹ̵̡", "Ʒ"],
    ["ᗒ", "ᗕ"],
    ["⟃", "⟄"],
    ["⪧", "⪦"],
    ["⪦", "⪧"],
    ["⪩", "⪨"],
    ["⪨", "⪩"],
    ["⪰", "⪯"],
    ["⫑", "⫒"],
    ["⨴", "⨵"],
    ["⩿", "⪀"],
    ["⩾", "⩽"],
    ["⩺", "⩹"],
    ["⩹", "⩺"],
    ["◥▶", "◀◤"],
    ["◍", "◎"],
    ["/͠-", "┐͡-\\"],
    ["⌣", "⌣”"],
    [" ͡⎚", " ͡⎚"],
    ["≋"],
    ["૦ઁ"],
    ["  ͯ"],
    ["  ͌"],
    ["ළ"],
    ["◉"],
    ["☉"],
    ["・"],
    ["▰"],
    ["ᵔ"],
    [" ﾟ"],
    ["□"],
    ["☼"],
    ["*"],
    ["`"],
    ["⚆"],
    ["⊜"],
    [">"],
    ["❍"],
    ["￣"],
    ["─"],
    ["✿"],
    ["•"],
    ["T"],
    ["^"],
    ["ⱺ"],
    ["@"],
    ["ȍ"],
    ["  "],
    ["  "],
    ["x"],
    ["-"],
    ["$"],
    ["Ȍ"],
    ["ʘ"],
    ["Ꝋ"],
    [""],
    ["⸟"],
    ["๏"],
    ["ⴲ"],
    ["◕"],
    ["◔"],
    ["✧"],
    ["■"],
    ["♥"],
    [" ͡°"],
    ["¬"],
    [" º "],
    ["⨶"],
    ["⨱"],
    ["⏓"],
    ["⏒"],
    ["⍜"],
    ["⍤"],
    ["ᚖ"],
    ["ᴗ"],
    ["ಠ"],
    ["σ"],
    ["☯"],
]

mouths = [
    ["v"],
    ["ᴥ"],
    ["ᗝ"],
    ["Ѡ"],
    ["ᗜ"],
    ["Ꮂ"],
    ["ᨓ"],
    ["ᨎ"],
    ["ヮ"],
    ["╭͜ʖ╮"],
    [" ͟ل͜"],
    [" ͜ʖ"],
    [" ͟ʖ"],
    [" ʖ̯"],
    ["ω"],
    [" ³"],
    [" ε "],
    ["﹏"],
    ["□"],
    ["ل͜"],
    ["‿"],
    ["╭╮"],
    ["‿‿"],
    ["▾"],
    ["‸"],
    ["Д"],
    ["∀"],
    ["!"],
    ["人"],
    ["."],
    ["ロ"],
    ["_"],
    ["෴"],
    ["ѽ"],
    ["ഌ"],
    ["⏠"],
    ["⏏"],
    ["⍊"],
    ["⍘"],
    ["ツ"],
    ["益"],
    ["╭∩╮"],
    ["Ĺ̯"],
    ["◡"],
    [" ͜つ"],
]

ears = [
    ["q", "p"],
    ["ʢ", "ʡ"],
    ["⸮", "?"],
    ["ʕ", "ʔ"],
    ["ᖗ", "ᖘ"],
    ["ᕦ", "ᕥ"],
    ["ᕦ(", ")ᕥ"],
    ["ᕙ(", ")ᕗ"],
    ["ᘳ", "ᘰ"],
    ["ᕮ", "ᕭ"],
    ["ᕳ", "ᕲ"],
    ["(", ")"],
    ["[", "]"],
    ["¯\\_", "_/¯"],
    ["୧", "୨"],
    ["୨", "୧"],
    ["⤜(", ")⤏"],
    ["☞", "☞"],
    ["ᑫ", "ᑷ"],
    ["ᑴ", "ᑷ"],
    ["ヽ(", ")ﾉ"],
    ["\\(", ")/"],
    ["乁(", ")ㄏ"],
    ["└[", "]┘"],
    ["(づ", ")づ"],
    ["(ง", ")ง"],
    ["⎝", "⎠"],
    ["ლ(", "ლ)"],
    ["ᕕ(", ")ᕗ"],
    ["(∩", ")⊃━☆ﾟ.*"],
]

toss = (
    "Cara",
    "Cruz",
)

decide = ("Si.", "No.", "Talvez.")

table = (
    "(╯°□°）╯彡 ┻━┻",
    "Me quedé sin mesas, pediré más.",
    "Ve a trabajar un poco en lugar de girar mesas.",
)



normiefont = [
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
]
weebyfont = [
    "卂",
    "乃",
    "匚",
    "刀",
    "乇",
    "下",
    "厶",
    "卄",
    "工",
    "丁",
    "长",
    "乚",
    "从",
    "𠘨",
    "口",
    "尸",
    "㔿",
    "尺",
    "丂",
    "丅",
    "凵",
    "リ",
    "山",
    "乂",
    "丫",
    "乙",
]


def weebify(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    string = ""

    if message.reply_to_message:
        string = message.reply_to_message.text.lower().replace(" ", "  ")

    if args:
        string = "  ".join(args).lower()

    if not string:
        message.reply_text(
            "El uso es `/weebify <texto>`", parse_mode=ParseMode.MARKDOWN
        )
        return

    for normiecharacter in string:
        if normiecharacter in normiefont:
            weebycharacter = weebyfont[normiefont.index(normiecharacter)]
            string = string.replace(normiecharacter, weebycharacter)

    if message.reply_to_message:
        message.reply_to_message.reply_text(string)
    else:
        message.reply_text(string)


def runs(update: Update, context: CallbackContext):
    update.effective_message.reply_text(random.choice(runs_templates))


def slap(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat

    reply_text = (
        message.reply_to_message.reply_text
        if message.reply_to_message
        else message.reply_text
    )

    curr_user = html.escape(message.from_user.first_name)
    user_id = extract_user(message, args)

    if user_id == bot.id:
        temp = random.choice(slap_megu_templates)

        if isinstance(temp, list):
            if temp[2] == "tmute":
                if is_user_admin(chat, message.from_user.id):
                    reply_text(temp[1])
                    return

                mutetime = int(time.time() + 60)
                bot.restrict_chat_member(
                    chat.id,
                    message.from_user.id,
                    until_date=mutetime,
                    permissions=ChatPermissions(can_send_messages=False),
                )
            reply_text(temp[0])
        else:
            reply_text(temp)
        return

    if user_id:

        slapped_user = bot.get_chat(user_id)
        user1 = curr_user
        user2 = html.escape(slapped_user.first_name)

    else:
        user1 = bot.first_name
        user2 = curr_user

    temp = random.choice(slap_templates)
    item = random.choice(items)
    hit = random.choice(hits)
    throw = random.choice(throws)

    reply = temp.format(user1=user1, user2=user2, item=items, hits=hits, throws=throws)

    reply_text(reply, parse_mode=ParseMode.HTML)


def toss(update: Update, context: CallbackContext):
    update.message.reply_text(random.choice(toss))


def dice(update, context):
    bot = context.bot
    chat_id = update.message.chat_id
    bot.send_dice(chat_id, emoji="🎲")


def shrug(update: Update, context: CallbackContext):
    msg = update.effective_message
    reply_text = (
        msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text
    )
    reply_text(r"¯\_(ツ)_/¯")


def rlg(update: Update, context: CallbackContext):
    eye = random.choice(eyes)
    mouth = random.choice(mouths)
    ear = random.choice(ears)

    if len(eye) == 2:
        repl = ear[0] + eye[0] + mouth[0] + eye[1] + ear[1]
    else:
        repl = ear[0] + eye[0] + mouth[0] + eye[0] + ear[1]
    update.message.reply_text(repl)


def decide(update: Update, context: CallbackContext):
    reply_text = (
        update.effective_message.reply_to_message.reply_text
        if update.effective_message.reply_to_message
        else update.effective_message.reply_text
    )
    reply_text(random.choice(decide))


def table(update: Update, context: CallbackContext):
    reply_text = (
        update.effective_message.reply_to_message.reply_text
        if update.effective_message.reply_to_message
        else update.effective_message.reply_text
    )
    reply_text(random.choice(table))


__help__ = """
 •`/runs`: Responde una cadena aleatoria de una matriz de respuestas.
 •`/slap`: Abofetear a un usuario, o recibir una bofetada si no hay a quien reponder.
 •`/shrug`: Shrugs XD.
 •`/table`: Obtener flip/unflip.
 •`/decide`: Responde aleatoriamente sí/no/tal vez
 •`/toss`: Lanza una moneda
 •`/dice`: Tira un dado
 •`/rlg`: Une oídos, nariz, boca y crea un emo ;-;
 •`/shout <palabra clave>`: Escribe cualquier cosa que quieras dar un grito fuerte
 •`/weebify <text>`: Devuelve un texto weebify
"""


WEEBIFY_HANDLER = DisableAbleCommandHandler("weebify", weebify, run_async=True)
RUNS_HANDLER = DisableAbleCommandHandler("runs", runs, run_async=True)
SLAP_HANDLER = DisableAbleCommandHandler("slap", slap, run_async=True)
TOSS_HANDLER = DisableAbleCommandHandler("toss", toss, run_async=True)
DICE_HANDLER = DisableAbleCommandHandler("dice", dice, run_async=True)
SHRUG_HANDLER = DisableAbleCommandHandler("shrug", shrug, run_async=True)
RLG_HANDLER = DisableAbleCommandHandler("rlg", rlg, run_async=True)
DECIDE_HANDLER = DisableAbleCommandHandler("decide", decide, run_async=True)
TABLE_HANDLER = DisableAbleCommandHandler("table", table, run_async=True)

dispatcher.add_handler(WEEBIFY_HANDLER)
dispatcher.add_handler(RUNS_HANDLER)
dispatcher.add_handler(SLAP_HANDLER)
dispatcher.add_handler(TOSS_HANDLER)
dispatcher.add_handler(DICE_HANDLER)
dispatcher.add_handler(SHRUG_HANDLER)
dispatcher.add_handler(RLG_HANDLER)
dispatcher.add_handler(DECIDE_HANDLER)
dispatcher.add_handler(TABLE_HANDLER)

__mod_name__ = "Diversión"
__command_list__ = [
    "weebify",
    "runs",
    "slap",
    "toss",
    "dice",
    "shrug",
    "rlg",
    "decide",
    "table",
]
__handlers__ = [
    WEEBIFY_HANDLER,
    RUNS_HANDLER,
    SLAP_HANDLER,
    TOSS_HANDLER,
    DICE_HANDLER,
    SHRUG_HANDLER,
    RLG_HANDLER,
    DECIDE_HANDLER,
    TABLE_HANDLER,
]
