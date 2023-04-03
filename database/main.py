import os
import sys

import fasteners

from bot.bot import BOT

import init_django_orm  # noqa: F401


if __name__ == '__main__':
    lock = fasteners.InterProcessLock('database/bot/bot.py')
    print(lock.acquired)
    with lock:
        BOT.start()
    BOT.stop()
