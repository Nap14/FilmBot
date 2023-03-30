import json
from time import sleep

import colorama
from colorama import Fore, Style

import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup


def get_valid_page(func: callable):
    def wrapper(*args, **kwargs):
        count = 0
        while count < 10:
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException as e:
                print(colorama.Fore.RED + "Connection error. Try to reconnect...")
                print(str(e) + colorama.Style.RESET_ALL)
                sleep(10)
                count += 1
        raise Exception("Failed to establish connection after multiple attempts.")

    return wrapper


# Define a function to retrieve the BeautifulSoup object for a given URL
@get_valid_page
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
    response = requests.request(method, url, *args, **kwargs)

    response.raise_for_status()

    print(Fore.YELLOW + str(response.status_code) + Style.RESET_ALL)

    return BeautifulSoup(response.content, parser)


def get_request_config(request_type: str = "base") -> dict:
    with open("requests_data.json", "rb") as file:
        data = json.load(fp=file)

    return data[request_type]


@get_valid_page
def get_trailer_url(film_id: int):

    trailer_data = get_request_config("trailer")

    data = {
        "id": film_id,
    }

    response = requests.post(data=data, **trailer_data)

    try:
        soup = BeautifulSoup(response.json()["code"], "html.parser")
        return soup.select_one("iframe")["src"].split("?")[0]
    except KeyError:
        return None
