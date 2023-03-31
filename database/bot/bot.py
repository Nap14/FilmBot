import os
from threading import Thread

import schedule
import telebot

import init_django_orm  # noqa: F401
from db.models import Film, Chat


class FilmBot:
    def __init__(self, token, chat_id):
        self.bot = telebot.TeleBot(token)
        self.chat_id = chat_id
        with open("templates/main.html", "rt", encoding="utf-8") as file:
            self.template = file.read()


    def start(self):
        @self.bot.message_handler(commands=["start"])
        def start(message):
            chat_id = Chat.objects.get_or_create(chat_id=message.chat.chat_id)
            self.bot.send_message(chat_id, message)

        @self.bot.message_handler(commands=["film"])
        def film(message):
            film = Film.objects.filter(rating__gte=7).order_by("?").first()
            actors = [f"#{actor.name.split()[-1]}" for actor in film.actors.all()]

            response = self.template.format(
                name=film.name,
                release=film.release.year,
                trailer=film.trailer,
                description=film.description,
                actors=", ".join(actors),
            )
            self.bot.send_message(message.chat.id, response, parse_mode="HTML")

        Thread(target=self._scheduler, args=()).start()
        self.bot.polling(non_stop=True)

    def _sen_film_every_day(self):
        film = Film.objects.filter(rating__gte=7).order_by("?").first()
        actors = [f"#{actor.name.split()[-1]}" for actor in film.actors.all()]

        message = self.template.format(
            name=film.name,
            release=film.release.year,
            trailer=film.trailer,
            description=film.description,
            actors=", ".join(actors),
        )

        self.bot.send_message(self.chat_id, message, parse_mode="HTML")

    def _scheduler(self):
        schedule.every(3).days.at("19:42").do(self._sen_film_every_day)
        while True:
            schedule.run_pending()


if __name__ == "__main__":
    pass
