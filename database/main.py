import os
from wsgiref.simple_server import make_server

import fasteners

from bot.bot import BOT

import init_django_orm  # noqa: F401


def film_bot(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'text/plain; charset=utf-8')]
    start_response(status, headers)

    lock = fasteners.InterProcessLock('bot/bot.py')
    print(lock.acquired)
    with lock:
        BOT.start()
    BOT.stop()

    response_body = b"Hello, world!\n"
    return [response_body]


if __name__ == '__main__':
    httpd = make_server('', 8000, film_bot)
    print("Serving on port 8000...")

    httpd.serve_forever()
