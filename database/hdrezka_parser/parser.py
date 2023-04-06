from datetime import datetime
from abc import abstractmethod

from bs4 import BeautifulSoup

from hdrezka_parser.request import get_request_config, get_trailer_url, get_soup


class Page:
    BASE_URL = ""

    def __init__(self, id_):
        self.id = id_
        self._url = self.BASE_URL.format(self.id)

    @property
    def page(self) -> BeautifulSoup:
        return get_soup(
            url=self._url,
            headers=get_request_config()["headers"]
        )

    @abstractmethod
    def parse_page(self) -> dict:
        pass


class Movie(Page):
    BASE_URL = "https://hdrezka.ag/category/genre/{}-film_name.html"

    @staticmethod
    def get_date_from_site(str_date):
        month_dict = {
            "января": "1",
            "февраля": "2",
            "марта": "3",
            "апреля": "4",
            "мая": "5",
            "июня": "6",
            "июля": "7",
            "августа": "8",
            "сентября": "9",
            "октября": "10",
            "ноября": "11",
            "декабря": "12",
        }
        pattern = "%d-%m-%Y"

        text = str_date.split()
        text[1] = month_dict.get(text[1], "1")
        text = "-".join(text)
        try:
            return str(datetime.strptime(text, pattern).date())
        except ValueError:
            return None

    def parse_page(self):
        table = self.page.select_one("table")
        str_time = (
            table.find(itemprop="duration")
            and table.find(itemprop="duration").text.split()[0]
        )
        try:
            duration = int(str_time)
        except ValueError:
            hours, minutes = str_time.split(":")
            duration = int(hours) * 60 + int(minutes)
        except TypeError:
            duration = None

        original_name = (
            self.page.select_one(".b-post__origtitle")
            and self.page.select_one(".b-post__origtitle").text
        )
        dubbing = table.find(string="В переводе") and table.find(
            string="В переводе"
        ).parent.parent.parent.td.find_next_sibling("td").text.replace(
            " и ", ", "
        ).split(
            ", "
        )
        age = table.find(string="Возраст") and int(
            table.find(string="Возраст")
            .parent.parent.parent.td.find_next_sibling("td")
            .span.text[:-1]
        )
        description = (
            self.page.select_one(".b-post__description_text")
            and self.page.select_one(".b-post__description_text").text
            or table.find(string="Слоган")
            .parent.parent.parent.select_one("td:last-child")
            .text
        )

        return {
            "name": self.page.select_one(".b-post__title > h1").text,
            "original_name": original_name,
            "description": description,
            "country": table.find(string="Страна")
            and table.find(string="Страна")
            .parent.parent.parent.select_one("td > a")
            .text,
            "trailer": get_trailer_url(self.id),
            "release": table.find(string="Дата выхода")
            and self.get_date_from_site(
                table.find(string="Дата выхода")
                .parent.parent.parent.select_one("td:last-child")
                .text.replace("года", "")
            ),
            "rating": table.select_one(".imdb .bold")
            and float(table.select_one(".imdb .bold").text),
            "genres": [genre.text for genre in table.find_all(itemprop="genre")],
            "actors": [
                {
                    "external_id": actor["data-id"],
                    "name": actor.find(itemprop="name").text,
                    "profession": actor["data-job"].lower(),
                }
                for actor in table.find_all(itemprop="actor")
            ],
            "directors": [
                {
                    "external_id": director["data-id"],
                    "name": director.find(itemprop="name").text,
                    "profession": director["data-job"].lower(),
                }
                for director in table.find_all(itemprop="director")
            ],
            "external_id": self.id,
            "dubbing": dubbing,
            "duration": duration,
            "age_limit": age,
            "poster": self.page.select_one(".b-sidecover img")["src"],
        }


class Maker(Page):

    BASE_URL = "https://hdrezka.ag/person/{}-customer_name/"

    def parse_page(self):
        try:
            original_name = self.page.select_one(".t2").text
        except AttributeError:
            original_name = None

        try:
            date = self.page.select_one("time")["datetime"]
        except (AttributeError, TypeError):
            date = None

        return {
            "external_id": self.id,
            "name": self.page.select_one(".t1").text,
            "original_name": original_name,
            "birth_date": date,
            "profession": [
                "актер" if prof.text == "актриса" else prof.text
                for prof in self.page.find_all(itemprop="jobTitle")
            ],
        }
