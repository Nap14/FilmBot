import os
from threading import Thread

import schedule
import telebot

import init_django_orm  # noqa: F401
from db.models import Film


class FilmBot:
    def __init__(self, token, chat_id):
        self.bot = telebot.TeleBot(token)
        self.chat_id = chat_id

    def start(self):
        @self.bot.message_handler(commands=["start"])
        def start(message):
            self.bot.send_message(message.chat.id, message)

        Thread(target=self._scheduler, args=()).start()
        self.bot.polling(non_stop=True)

    def _sen_film_every_day(self):
        film = Film.objects.filter(rating__gte=7).order_by("?").first()
        with open("../templates/main.html", "rt", encoding="utf-8") as file:
            template = file.read()
        actors = [f"#{actor.name.split()[-1]}" for actor in film.actors.all()]

        message = template.format(
            name=film.name,
            release=film.release.year,
            trailer=film.trailer,
            description=film.description,
            actors=", ".join(actors),
        )

        self.bot.send_message(test_id, message, parse_mode="HTML")

    def _scheduler(self):
        schedule.every(10).seconds.do(self._sen_film_every_day)
        # schedule.every().day.at("19:42").do(sen_film_every_day)
        while True:
            schedule.run_pending()


if __name__ == "__main__":
    TOKEN = os.environ.get("BOT_TOKEN")
    films_chat_id = -1001620986020
    test_id = -1001156799972

    bot = FilmBot(TOKEN, films_chat_id)
    bot.start()
