# Generated by Django 5.0.6 on 2024-09-05 15:36

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("person", "0003_alter_people_role_remove_people_code_and_more"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="People",
            new_name="Group",
        ),
    ]
