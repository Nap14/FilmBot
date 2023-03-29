import json

import colorama
from winsound import Beep
from time import sleep

from django.core.exceptions import ObjectDoesNotExist

import init_django_orm  # noqa: F401


from db.models import MovieMaker, Profession, Genre, Dubbing, Film
from hdrezka_parser.parser import Maker


def add_movie_maker_to_database(movie_maker: dict):

    movie_maker["profession"] = [
        "актер" if prof == "актриса" else prof for prof in movie_maker["profession"]
    ]

    if movie_maker["birth_date"]:
        birth_date = movie_maker["birth_date"].split("-")
        for i in range(3):
            if not int(birth_date[i]):
                birth_date[i] = birth_date[i].replace("0", "1", 1)

        movie_maker["birth_date"] = "-".join(birth_date)

    professions = Profession.objects.filter(name__in=movie_maker["profession"])

    del movie_maker["profession"]

    m = MovieMaker.objects.create(**movie_maker)

    [m.profession.add(prof) for prof in professions]
    m.save()

    print(colorama.Fore.WHITE + f"{m} was added")

    return m


def get_dubbing(dubbings: list) -> [Dubbing]:
    result = []

    if not dubbings:
        return []

    for dub in dubbings:
        try:
            dubbing = Dubbing.objects.get(name=dub)
        except ObjectDoesNotExist:
            dubbing = Dubbing.objects.create(name=dub)
            print(f"Dubbing {dubbing.name}, was added")

        result.append(dubbing)

    return result


# использовать когда парсятся фильмы та актёры и продюсеры это словари
def get_movie_makers_from_film_page(makers: dict):
    result = []

    for maker in makers:
        try:
            m = MovieMaker.objects.get(external_id=maker["external_id"])
        except ObjectDoesNotExist:
            m = add_movie_maker_to_database(**maker)
        result.append(m)

    return result


def get_movie_makers(ex_ids: [int]):
    result = []
    for id_ in ex_ids:
        try:
            m = MovieMaker.objects.get(external_id=id_)
        except ObjectDoesNotExist:
            movie_maker = Maker(id_).parse_page()
            m = add_movie_maker_to_database(movie_maker)
            sleep(1)

        result.append(m)

    return result


def add_film(film):
    film["release"] = film["release"].split()[0]
    genres = Genre.objects.filter(name__in=film["genres"])

    actors = get_movie_makers(film["actors"])

    directors = get_movie_makers(film["directors"])

    dubbings = get_dubbing(film["dubbing"])

    del film["genres"]
    del film["actors"]
    del film["directors"]
    del film["dubbing"]

    film = Film.objects.create(**film)

    [film.genres.add(genre) for genre in genres]
    [film.actors.add(actor) for actor in actors]
    [film.directors.add(director) for director in directors]
    [film.dubbing.add(dubbin) for dubbin in dubbings]

    print(colorama.Fore.CYAN + f"Film {film} was added" + colorama.Style.RESET_ALL)

    return film


def add_films(file, start: int = 0):
    with open(file, "rb") as file:
        films = json.load(file)

    for i, film in list(enumerate(films))[start:]:
        print("Initialize film #", i)
        add_film(film)


def add_films_from_file(file: str, *args):
    try:
        add_films(file, *args)
    except Exception:
        Beep(2500, 1000)
        raise


if __name__ == "__main__":
    f = Film.objects.all()
    print(f)
