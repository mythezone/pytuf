# Generated by Django 5.1 on 2024-09-02 19:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PageType",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name="Page",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("url", models.CharField(max_length=500)),
                ("title", models.CharField(max_length=100)),
                ("intro", models.TextField()),
                (
                    "tp",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="page.pagetype"
                    ),
                ),
            ],
        ),
    ]