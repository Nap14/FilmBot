import init_django_orm  # noqa: F401

from scripts import parse_films, get_empty_ids


def refresh_data():
    parse_films(ids=get_empty_ids(), stop_limit=100)


if __name__ == '__main__':
    pass



