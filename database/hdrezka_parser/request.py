import json
from colorama import Fore, Style

import requests
from dataclasses import dataclass, asdict
from fake_useragent import UserAgent

from bs4 import BeautifulSoup


# Define a dataclass for storing video details
@dataclass
class Video:
    external_id: int
    name: str
    original_name: str
    poster: str
    description: str
    country: str
    trailer: str
    release: str
    rating: float
    genres: [str]
    actors: [str]
    directors: [str]
    dubbing: [str]
    time: int
    age_limit: int

    def __str__(self):
        return f"{self.name}, ({self.release})"


@dataclass
class Customer:
    external_id: int
    name: str
    original_name: str
    birth_date: str
    profession: [str]

    def __str__(self):
        return f"{self.name} ({self.birth_date})"


# Define a function to retrieve the BeautifulSoup object for a given URL
def get_soup(
    url: str,
    method: str = "GET",
    parser: str = "html.parser",
    *args,
    **kwargs,
) -> BeautifulSoup:

    kwargs.setdefault("headers", {"User-Agent": None})[
        "User-Agent"
    ] = UserAgent().random

    # Make a request to the URL and raise an error if the response code is not 200
    if method == "POST":
        response = requests.post(url, *args, **kwargs)
    else:
        response = requests.get(url, *args, **kwargs)

    response.raise_for_status()

    print(Fore.YELLOW + str(response.status_code) + Style.RESET_ALL)

    return BeautifulSoup(response.content, parser)


def get_request_data(response_type: str = "base") -> dict:
    with open("requests_data.json", "rb") as file:
        data = json.load(fp=file)

    return data[response_type]


def get_trailer_url(film_id: int):

    trailer_data = get_request_data("trailer")

    data = {
        "id": film_id,
    }

    response = requests.post(data=data, **trailer_data)
    try:
        soup = BeautifulSoup(response.json()["code"], "html.parser")
    except KeyError:
        return None

    return soup.select_one("iframe")["src"].split("?")[0]
