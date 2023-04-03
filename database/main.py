import os
from wsgiref.simple_server import make_server

import fasteners

from bot.bot import BOT

import init_django_orm  # noqa: F401


def film_bot_set_up():

    lock = fasteners.InterProcessLock('database/bot/bot.py')
    print(lock.acquired)
    with lock:
        BOT.start()
    BOT.stop()


if __name__ == '__main__':
    film_bot_set_up()
