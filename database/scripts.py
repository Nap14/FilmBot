import threading

import colorama
import requests
from django.db.models import Q
from time import sleep

import init_django_orm  # noqa: F401

from db.models import MovieMaker, Profession, Genre, Dubbing, Film
from hdrezka_parser.parser import Movie
from utils import print_info, Timer, ExceptionHandler


def get_dubbing(dubbings: list) -> list[Dubbing]:
    """
    Retrieve existing Dubbing objects from the database based on the given list of names.
    Create and retrieve any new Dubbing objects and return the complete list of objects.
    """

    if not dubbings:
        return []

    # Retrieve existing Dubbing objects from the database
    existing_dubbings = Dubbing.objects.filter(name__in=dubbings)

    if len(existing_dubbings) == len(dubbings):
        return existing_dubbings

    # Identify any names not found in existing Dubbing objects
    existing_names = set(existing_dubbings.values_list("name", flat=True))
    new_names = list(set(dubbings) - existing_names)

    # Create new Dubbing objects for any names not found in existing Dubbing objects
    new_dubbings = [Dubbing(name=name) for name in new_names]
    Dubbing.objects.bulk_create(new_dubbings)

    # Retrieve all Dubbing objects (including newly created objects)
    all_dubbings = Dubbing.objects.filter(
        Q(name__in=existing_names) | Q(name__in=new_names)
    )

    return all_dubbings


@print_info(message="was added to queue", color="white", method=lambda m: m.name)
def add_movie_maker_to_database(movie_maker: dict, save: bool = True) -> MovieMaker:
    """
    Add a new MovieMaker object to the database based on the given dictionary.
    Return the newly created object.
    """

    # Map "актриса" to "актер" in the profession list
    movie_maker["profession"] = [
        p if p != "актриса" else "актер" for p in movie_maker["profession"]
    ]

    # Fix birthdate format if needed
    if movie_maker.get("birth_date"):
        birth_date_parts = movie_maker["birth_date"].split("-")
        for i in range(3):
            if not int(birth_date_parts[i]):
                birth_date_parts[i] = birth_date_parts[i].replace("0", "1", 1)
        movie_maker["birth_date"] = "-".join(birth_date_parts)

    # Get Profession objects for the given profession names
    profession_names = movie_maker.pop("profession")
    professions = Profession.objects.filter(name__in=profession_names)

    # Create and save new MovieMaker object
    movie_maker_obj = MovieMaker(**movie_maker)
    if save:
        movie_maker_obj.save()

        # Add Profession objects to MovieMaker object
        [movie_maker_obj.profession.add(prof) for prof in professions]
        print(colorama.Fore.GREEN + "and was saved" + colorama.Style.RESET_ALL)

    return movie_maker_obj


@print_info(message="makers was added to db")
def save_movie_makers(makers: list) -> list[MovieMaker]:
    """
    Bulk create new moviemakers in the database and return a list of makers.

    :param makers: A list of dictionaries containing moviemaker data.
    :return: A list of created moviemaker objects.
    """
    makers = [add_movie_maker_to_database(maker, save=False) for maker in makers]
    return MovieMaker.objects.bulk_create(makers)


# использовать когда парсятся фильмы та актёры и продюсеры это словари
def get_movie_makers(makers: [dict]) -> list[MovieMaker]:
    """
    Get a list of moviemakers from the database, creating new ones if necessary.

    :param makers: A list of dictionaries containing moviemaker data.
    :return: A list of moviemaker objects.
    """

    # Create a list of moviemaker IDs from the given list of dictionaries
    makers_ids = [int(maker["external_id"]) for maker in makers]

    # Find all moviemakers in the database with an external ID matching one of the IDs in the maker_ids list
    existing_makers = MovieMaker.objects.filter(external_id__in=makers_ids)

    # If all of makers IDs in the list already exist in the database, return a list of their IDs
    if len(makers) == len(existing_makers):
        return existing_makers

    # Create a set of existing maker IDs to check against when adding new makers to the database
    existing_ids = list(existing_makers.values_list("external_id", flat=True))

    # Create a list of new movie makers to add to the database, skipping any makers that already exist
    new_makers = save_movie_makers(
        list(
            filter(lambda maker: int(maker["external_id"]) not in existing_ids, makers)
        )
    )

    # Return a list of all maker objects (existing and new)
    return list(existing_makers) + list(new_makers)


@print_info(
    message="was added to db",
    color="cyan",
    method=lambda f: f"Film {f} #{f.external_id}",
)
def add_film(film_data: dict) -> Film:
    """
    Get film data, save film to database and return Film object
    :param film_data:
    :return: Film obj
    """

    # Split release date string to get only the date and NULL if it NULL
    film_data["release"] = film_data["release"] and film_data["release"].split()[0]

    # Get Genre objects for each genre name
    genres = Genre.objects.filter(name__in=film_data.pop("genres"))

    # Get MovieMaker objects for each actor and director external ID
    actors = get_movie_makers(film_data.pop("actors"))
    directors = get_movie_makers(film_data.pop("directors"))

    # Get Dubbing objects for each dubbing language name
    dubbings = get_dubbing(film_data.pop("dubbing"))

    # Create Film object with given data
    film_obj = Film.objects.create(**film_data)

    # Set many-to-many relationships for genres, actors, directors, and dubbings
    [film_obj.genres.add(genre) for genre in genres]
    [film_obj.actors.add(actor) for actor in actors]
    [film_obj.directors.add(director) for director in directors]
    [film_obj.dubbing.add(dubbing) for dubbing in dubbings]

    # Return created Film object
    return film_obj


@print_info(message="films was add to database", color="LIGHTGREEN_EX")
def add_films(films, start: int = 0):
    result = []
    films_count = len(films)
    for i, film in list(enumerate(films))[start:]:
        print(
            f"Initializing adding to database: {i+1}/{films_count} - Movie ID: {film.get('external_id')}"
        )
        result.append(add_film(film))

    return result


@Timer()
@ExceptionHandler()
def parse_films(
    start: int = 1,
    stop: int = None,
    count: int = 1000,
    ids: list[int] = None,
    stop_limit: int = 10
):
    films = []
    makers = []
    thread = None
    errors = 0

    if ids is None:

        if stop is None:
            stop = start + count

        ids = range(start, stop)

    try:
        for parser_id in ids:
            print(
                colorama.Fore.BLUE
                + f"parse movie #{parser_id}"
                + colorama.Style.RESET_ALL
            )
            try:
                movie = Movie(parser_id).parse_page()
                errors = 0
            except requests.exceptions.HTTPError as e:
                errors += 1
                print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)
                if errors > stop_limit:
                    raise Exception(
                        f"{stop_limit} last pages was returns without response"
                    )
                continue
            except AttributeError:
                print("bad parser")
                continue

            films.append(movie)
            print(f"{movie['name']} was add to queue")
            sleep(1)

            for maker in movie["actors"] + movie["directors"]:
                if maker["external_id"] in map(lambda x: x["external_id"], makers):
                    continue
                makers.append(maker)

            if len(films) >= 50:
                get_movie_makers(makers)
                makers.clear()

                if thread is not None and thread.is_alive():
                    thread.join()
                thread = threading.Thread(target=add_films, args=(films,), daemon=True)
                thread.start()
                films.clear()

    except Exception as e:
        print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)
        raise
    finally:
        get_movie_makers(makers)
        add_films(films)

        if thread is not None and thread.is_alive():
            thread.join()
            print("All threads are joined.")


def get_empty_ids():
    """
    Returns a list of empty external_ids that can be used to create new Film objects.
    """
    used_ids = set(Film.objects.all().values_list("external_id", flat=True))
    all_ids = set(range(1, max(used_ids)))

    return sorted(all_ids - used_ids)


def get_last_film(order_by: str = "external_id", desc=True):

    if desc:
        order_by = "-" + order_by

    return Film.objects.order_by(order_by).first()


def main(*args, **kwargs):
    parse_films(*args, **kwargs)


if __name__ == "__main__":
    pass
