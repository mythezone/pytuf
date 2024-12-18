# Generated by Django 5.1 on 2024-09-02 19:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("person", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Movie",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=255)),
                ("published_date", models.DateField()),
                ("duration_min", models.IntegerField()),
                ("location", models.CharField(max_length=255)),
                ("info", models.JSONField()),
                ("rating", models.FloatField(default=0)),
                ("parsed", models.BooleanField(default=False)),
                ("favorite", models.BooleanField(default=False)),
                (
                    "actors",
                    models.ManyToManyField(related_name="actors", to="person.people"),
                ),
                (
                    "director",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="directors",
                        to="person.people",
                    ),
                ),
                (
                    "publisher",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="publishers",
                        to="person.people",
                    ),
                ),
                (
                    "series",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="series",
                        to="person.people",
                    ),
                ),
                (
                    "studio",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="studios",
                        to="person.people",
                    ),
                ),
                (
                    "tags",
                    models.ManyToManyField(related_name="tags", to="person.people"),
                ),
            ],
        ),
    ]
