# Generated by Django 4.1.7 on 2023-03-28 13:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("db", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="film",
            old_name="time",
            new_name="duration",
        ),
    ]