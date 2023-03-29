from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=255)


class Genre(models.Model):
    name = models.CharField(max_length=255)


class Profession(models.Model):
    name = models.CharField(max_length=255)


class Dubbing(models.Model):
    name = models.CharField(max_length=255)


class MovieMaker(models.Model):
    external_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255)
    birth_date = models.DateField()
    profession = models.ForeignKey(Profession, related_name="workers", on_delete=models.SET_DEFAULT, default=1)

    class Meta:
        verbose_name = "movie_maker"
        verbose_name_plural = "movie_makers"

    def __str__(self):
        return f"{self.name} ({self.birth_date})"


class Film(models.Model):
    external_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255)
    poster = models.URLField(max_length=500)
    description = models.TextField()
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING)
    trailer = models.URLField(max_length=500)
    release = models.DateField()
    rating = models.FloatField()
    genres = models.ManyToManyField(Genre)
    actors = models.ManyToManyField(MovieMaker, related_name="films")
    directors = models.ManyToManyField(MovieMaker, related_name="projects")
    dubbing = models.ManyToManyField(Dubbing)
    time = models.TimeField()
    age_limit = models.IntegerField()

    def __str__(self):
        return f"{self.name}, ({self.release})"

    class Meta:
        default_related_name = "films"
