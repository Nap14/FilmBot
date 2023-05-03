import init_django_orm  # noqa: F401

from scripts import parse_films, get_empty_ids, get_last_film


def refresh_data():
    parse_films(ids=get_empty_ids(), stop_limit=100)


def continue_parsing(
        start: int = get_last_film(desc=True).external_id, *args, **kwargs
):
    parse_films(start=start, *args, **kwargs)


def main():
    refresh_data()
    continue_parsing(count=1000, stop_limit=100)


if __name__ == '__main__':
    refresh_data()
