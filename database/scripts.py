import json

import colorama
from django.db.models import Q
from winsound import Beep
from time import sleep

from django.core.exceptions import ObjectDoesNotExist

import init_django_orm  # noqa: F401


from db.models import MovieMaker, Profession, Genre, Dubbing, Film
from hdrezka_parser.parser import Maker


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
    if movie_maker["birth_date"]:
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
        movie_maker_obj.profession.set(professions)

        print(colorama.Fore.WHITE + f"{movie_maker_obj} was added")
    else:
        print(colorama.Fore.WHITE + f"{movie_maker_obj} was added to queue")

    return movie_maker_obj


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


# использовать когда парсятся фильмы та актёры и продюсеры это словари
def get_movie_makers_from_film_page(makers: [dict]):
    # Create a list of moviemaker IDs from the given list of dictionaries
    makers_ids = [maker["external_id"] for maker in makers]

    # Find all moviemakers in the database with an external ID matching one of the IDs in the maker_ids list
    existing_makers = MovieMaker.objects.filter(external_id__in=makers_ids)

    # If all of makers IDs in the list already exist in the database, return a list of their IDs
    if len(makers) == len(existing_makers):
        return existing_makers

    # Create a set of existing maker IDs to check against when adding new makers to the database
    existing_ids = list(existing_makers.values_list("external_id", flat=True))

    # Create a list of new movie makers to add to the database, skipping any makers that already exist
    new_makers = [
        add_movie_maker_to_database(maker, save=False)
        for maker in makers
        if maker['external_id'] not in existing_ids
    ]

    # Bulk create new moviemakers in the database and return a list of all maker IDs (existing and new)
    new_makers = MovieMaker.objects.bulk_create(new_makers)
    new_ids = [maker.id for maker in new_makers]

    all_ids = list(existing_makers.values_list('id', flat=True)) + new_ids
    return all_ids


def get_movie_makers(external_ids: [int]):
    """
    Retrieve existing MovieMaker objects from the database based on the given list of external IDs.
    Create and retrieve any new Movie objects and return the complete list of objects.
    """

    # Retrieve existing Movie objects from the database
    existing_makers = MovieMaker.objects.filter(external_id__in=external_ids)

    if len(existing_makers) == len(external_ids):
        return existing_makers

    # Identify any external IDs not found in existing Movie objects
    existing_ids = set(existing_makers.values_list("external_id", flat=True))
    new_ids = set(map(int, external_ids)) - existing_ids
    new_makers = []

    # Create new Movie objects for any external IDs not found in existing Movie objects
    for id_ in new_ids:
        maker = Maker(id_).parse_page()
        if maker:
            m = add_movie_maker_to_database(maker, save=False)
            sleep(1)
            new_makers.append(m)
            print(f"maker {m.external_id} was add to queue")

    new_makers = MovieMaker.objects.bulk_create(new_makers)

    makers_ids = [maker.id for maker in new_makers]
    makers_ids.extend(existing_makers.values_list("id", flat=True))

    return makers_ids


def add_film(film_data):
    # Split release date string to get only the date
    film_data["release"] = film_data["release"].split()[0]

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
    film_obj.genres.set(genres)
    film_obj.actors.set(actors)
    film_obj.directors.set(directors)
    film_obj.dubbing.set(dubbings)

    # Print success message with Film object representation
    print(colorama.Fore.CYAN + f"Film {film_obj} was added" + colorama.Style.RESET_ALL)

    # Return created Film object
    return film_obj


def add_films(file, start: int = 0):
    with open(file, "rb") as file:
        films = json.load(file)

    for i, film in list(enumerate(films))[start:]:
        print("Initialize film_data #", i)
        add_film(film)


def add_films_from_file(file: str, *args):
    try:
        add_films(file, *args)
    except Exception:
        Beep(2500, 1000)
        raise


if __name__ == "__main__":
    pass
