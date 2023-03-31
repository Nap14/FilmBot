import os

from bot.bot import FilmBot
from db.models import Chat

import init_django_orm  # noqa: F401


if __name__ == '__main__':
    token = os.environ.get("BOT_TOKEN")
    chat_id = Chat.objects.get(chat_name="Фільми").chat_id
    bot = FilmBot(token, chat_id)
    bot.start()



