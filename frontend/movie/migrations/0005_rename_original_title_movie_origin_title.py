# Generated by Django 5.0.6 on 2024-09-05 15:09

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("movie", "0004_movie_rate_movie_rater"),
    ]

    operations = [
        migrations.RenameField(
            model_name="movie",
            old_name="original_title",
            new_name="origin_title",
        ),
    ]