import threading
from datetime import datetime

from MeguRobot.modules.sql import BASE, SESSION
from sqlalchemy import Boolean, Column, Integer, UnicodeText, Float


class AFK(BASE):
    __tablename__ = "afk_users"

    user_id = Column(Integer, primary_key=True)
    is_afk = Column(Boolean)
    reason = Column(UnicodeText)
    time_start = Column(Float)

    def __init__(self, user_id, reason="", is_afk=True, time_start=None):
        self.user_id = user_id
        self.reason = reason
        self.is_afk = is_afk
        self.time_start = time_start

    def __repr__(self):
        return "afk_status for {}".format(self.user_id)


AFK.__table__.create(checkfirst=True)
INSERTION_LOCK = threading.RLock()

AFK_USERS = {}


def is_afk(user_id):
    return user_id in AFK_USERS


def check_afk_status(user_id):
    try:
        return SESSION.query(AFK).get(user_id)
    finally:
        SESSION.close()


def set_afk(user_id, reason="", time_start=None):
    with INSERTION_LOCK:
        curr = SESSION.query(AFK).get(user_id)
        if not curr:
            curr = AFK(user_id, reason, True, time_start)
        else:
            curr.is_afk = True

        AFK_USERS[user_id] = reason

        SESSION.add(curr)
        SESSION.commit()


def rm_afk(user_id):
    with INSERTION_LOCK:
        curr = SESSION.query(AFK).get(user_id)
        if curr:
            if user_id in AFK_USERS:  # sanity check
                del AFK_USERS[user_id]

            time_start = get_time(curr)
            SESSION.delete(curr)
            SESSION.commit()
            return time_start

        SESSION.close()
        return False


def toggle_afk(user_id, reason=""):
    with INSERTION_LOCK:
        curr = SESSION.query(AFK).get(user_id)
        if not curr:
            curr = AFK(user_id, reason, True)
        elif curr.is_afk:
            curr.is_afk = False
        elif not curr.is_afk:
            curr.is_afk = True
        SESSION.add(curr)
        SESSION.commit()


def get_time(user):
    afk_diff = datetime.now() - datetime.fromtimestamp(user.time_start)
    seconds_r = afk_diff.seconds
    seconds = seconds_r % 60

    minutes_r = int(seconds_r / 60)
    minutes = minutes_r % 60

    hours_r = int(minutes_r / 60)
    hours = hours_r % 24

    days = afk_diff.days
    if days > 0:
        afk_time = "{} dias y {} horas".format(days, hours)
    elif hours_r > 0:
        afk_time = "{} horas y {} minutos".format(hours, minutes)
    elif minutes_r > 0:
        afk_time = "{} minutos y {} segundos".format(minutes, seconds)
    else:
        afk_time = "{} segundos".format(seconds)
    return afk_time


def __load_afk_users():
    global AFK_USERS
    try:
        all_afk = SESSION.query(AFK).all()
        AFK_USERS = {user.user_id: user.reason for user in all_afk if user.is_afk}
    finally:
        SESSION.close()


__load_afk_users()
