import datetime
import json

import colorama
import requests
import winsound
from django.db.models import Q
from time import sleep

import init_django_orm  # noqa: F401


from db.models import MovieMaker, Profession, Genre, Dubbing, Film
from hdrezka_parser.parser import Movie


class ExceptionHandler:
    """
    The ExceptionHandler class is a Python class that can be used as a context manager to handle exceptions in a specific way. It has two methods, __enter__ and __exit__, which are called when the context is entered and exited, respectively
    """

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        # If an exception occurred, beep at 2500Hz for 1 second
        if exc_type is not None:
            winsound.Beep(2500, 1000)
            return

        # Otherwise, play the default beep sound
        winsound.MessageBeep(winsound.MB_OK)
        print(
            colorama.Fore.GREEN
            + "All tasks are completed successfully🎉"
            + colorama.Style.RESET_ALL
        )


class Timer:
    def __enter__(self):
        self.start_time = datetime.datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(colorama.Fore.GREEN, end="")
        if exc_type is not None:
            print(
                colorama.Fore.RED
                + f"Process exited with an exception: {exc_val}"
            )

        print(
            f"Process finished with {self.elapsed_time()} seconds"
            + colorama.Style.RESET_ALL
        )

    def elapsed_time(self):
        return (datetime.datetime.now() - self.start_time).total_seconds()


def print_info(func: callable):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        print(
            colorama.Fore.CYAN
            + f"{len(result)} makers was added to db"
            + colorama.Style.RESET_ALL
        )
        return result

    return wrapper


def get_dubbing(dubbings: list) -> [Dubbing]:
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


def add_movie_maker_to_database(movie_maker: dict, save: bool = True):
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

        print(colorama.Fore.WHITE + f"{movie_maker_obj} was added")
    else:
        print(colorama.Fore.WHITE + f"{movie_maker_obj} was added to queue")

    return movie_maker_obj


@print_info
def save_movie_makers(makers: list):
    """
    Bulk create new moviemakers in the database and return a list of makers.

    :param maker_list: A list of dictionaries containing movie maker data.
    :return: A list of created movie maker objects.
    """
    makers = [add_movie_maker_to_database(maker, save=False) for maker in makers]
    return MovieMaker.objects.bulk_create(makers)


# использовать когда парсятся фильмы та актёры и продюсеры это словари
def get_movie_makers(makers: [dict]):
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


def add_film(film_data):
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

    # Print success message with Film object representation
    print(colorama.Fore.CYAN + f"Film {film_obj} was added" + colorama.Style.RESET_ALL)

    # Return created Film object
    return film_obj


def parese_films(start, stop):
    films = []
    makers = []
    try:
        for parser_id in range(start, stop):
            print(
                colorama.Fore.BLUE
                + f"parse movie #{parser_id}"
                + colorama.Style.RESET_ALL
            )
            movie = Movie(parser_id).parse_page()
            sleep(1)
            films.append(movie)
            print(f"{movie['name']} was add to queue")

            for maker in movie["actors"] + movie["directors"]:
                if maker["external_id"] in map(lambda x: x["external_id"], makers):
                    continue
                makers.append(maker)

            if not parser_id % 25:
                get_movie_makers(makers)
                makers.clear()
        get_movie_makers(makers)
    except Exception:
        get_movie_makers(makers)
        add_films(films)
        raise

    return films


def add_films(films, start: int = 0):

    for i, film in list(enumerate(films))[start:]:
        print("Initialize film_data #", i)
        add_film(film)


def main(*args):
    with Timer(), ExceptionHandler():
        add_films(parese_films(*args))


if __name__ == "__main__":
    pass
