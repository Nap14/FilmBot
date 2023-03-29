from django.db import models
from django_countries.fields import CountryField


class Genre(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.name}"


class Profession(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.name}"


class Dubbing(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.name}"


class MovieMaker(models.Model):
    external_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255, null=True)
    birth_date = models.DateField(null=True, default=None)
    profession = models.ManyToManyField(Profession, related_name="workers", default=3)

    class Meta:
        verbose_name = "movie_maker"
        verbose_name_plural = "movie_makers"

    def __str__(self):
        return f"{self.name} ({self.birth_date})"


class Film(models.Model):
    external_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255, null=True, blank=True)
    poster = models.URLField(max_length=500, null=True, blank=True)
    description = models.TextField()
    country = CountryField(max_length=255)
    trailer = models.URLField(max_length=500, null=True, blank=True)
    release = models.DateField(null=True, default=None)
    rating = models.FloatField()
    genres = models.ManyToManyField(Genre)
    actors = models.ManyToManyField(MovieMaker, related_name="films")
    directors = models.ManyToManyField(MovieMaker, related_name="projects")
    dubbing = models.ManyToManyField(Dubbing)
    duration = models.IntegerField()
    age_limit = models.IntegerField(null=True)

    def __str__(self):
        return f"{self.name}, ({self.release})"

    class Meta:
        default_related_name = "films"
