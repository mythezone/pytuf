# Generated by Django 5.1 on 2024-10-24 15:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("movie", "0010_movie_my_rate_movie_status_alter_movie_current_title_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="movie",
            name="comment",
            field=models.CharField(default="", max_length=500),
        ),
    ]
