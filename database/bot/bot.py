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

    def __init__(self, token, chat_id):
        self.bot = telebot.TeleBot(token)
        self.chat_id = chat_id
        with open("database/templates/main.html", "rt", encoding="utf-8") as file:
            self.template = file.read()

    def start(self):
        @self.bot.message_handler(commands=["start"])
        def start(message):
            chat_id = Chat.objects.get_or_create(chat_id=message.chat.id, spam=True)[0].chat_id
            self.bot.send_message(chat_id, "Hello in the library of the best films")
            self._sen_film_every_day(chat_id=chat_id)

        @self.bot.message_handler(commands=["film"])
        def get_film(message):
            film = self._get_message()

            self.bot.send_message(message.chat.id, film, parse_mode="HTML")

        thread = Thread(target=self._scheduler, args=())
        thread.start()
        try:
            self.bot.polling(non_stop=True)
        except Exception as e:
            print(e)
            thread.join()
            raise

    def _sen_film_every_day(self, chat_id: int = None):
        if chat_id is None:
            chat_id = self.chat_id

        message = self._get_message()

        self.bot.send_message(chat_id, message, parse_mode="HTML")

    def _scheduler(self):
        schedule.every().day.at("19:42").do(self._sen_film_every_day)
        schedule.every().hour.do(self._sen_film_every_day)
        while True:
            schedule.run_pending()

    def _get_message(self):
        film = Film.objects.filter(rating__gte=7).filter(~Q(country="Россия")).order_by("?").first()
        actors = [f"#{actor.name.split()[-1]}" for actor in film.actors.all()]

        return self.template.format(
            name=film.name,
            release=film.release.year,
            trailer=film.trailer,
            description=film.description,
            actors=", ".join(actors),
        )


if __name__ == "__main__":
    pass
