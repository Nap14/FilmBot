import os
from threading import Thread

import schedule
import telebot
from django.db.models import Q

import init_django_orm  # noqa: F401
from db.models import Film, Chat


class FilmBot:
    """
    A bot that sends a message about a random film every 3 days.

    The message includes the film's name, release year, trailer link, description, and actors.

    The bot can also send the message about the film on demand via the "/film" command.
    """

    with open("templates/main.html", "rt", encoding="utf-8") as file:
        TEMPLATE = file.read()

    def __init__(self, token, chat_id):
        self.bot = telebot.TeleBot(token)
        self.chat_id = chat_id
        self.should_stop = False

    def start(self):
        self._setup_message_handlers()
        self._start_scheduler()
        self.bot.infinity_polling()

    def stop(self):
        self.should_stop = True

    def _start_scheduler(self):
        self._scheduler_thread = Thread(target=self._scheduler)
        self._scheduler_thread.start()

    def _setup_message_handlers(self):
        @self.bot.message_handler(commands=["start"])
        def start(message):
            chat_id = Chat.objects.get_or_create(chat_id=message.chat.id, spam=True)[0].chat_id
            self.bot.send_message(chat_id, "Hello in the library of the best films")
            self._send_random_film(chat_id=chat_id)

        @self.bot.message_handler(commands=["film"])
        def get_film(message):
            self._send_random_film(chat_id=message.chat.id)

    def _send_random_film(self, chat_id: int = None):
        if chat_id is None:
            chat_id = self.chat_id

        message = self._get_message()

        self.bot.send_message(chat_id, message, parse_mode="HTML")

    def _scheduler(self):
        schedule.every().day.at("19:42").do(self._send_random_film)
        schedule.every().minutes.do(print, "pending")
        while not self.should_stop:
            schedule.run_pending()

    def _get_message(self):
        film = Film.objects.filter(rating__gte=7).filter(~Q(country="Россия")).order_by("?").first()
        actors = [f"#{actor.name.split()[-1]}" for actor in film.actors.all()]

        return self.TEMPLATE.format(
            name=film.name,
            release=film.release.year,
            trailer=film.trailer,
            description=film.description,
            actors=", ".join(actors),
        )


TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = Chat.objects.get(chat_name="Фільми").chat_id
BOT = FilmBot(TOKEN, CHAT_ID)


if __name__ == "__main__":
    pass
