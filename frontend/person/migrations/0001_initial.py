# Generated by Django 5.1 on 2024-09-02 19:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("page", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PeopleType",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name="People",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("code", models.CharField(max_length=20)),
                ("name", models.CharField(max_length=100)),
                ("avatar", models.CharField(max_length=200)),
                ("intro", models.TextField()),
                ("urls", models.ManyToManyField(related_name="people", to="page.page")),
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="people",
                        to="person.peopletype",
                    ),
                ),
            ],
        ),
    ]