# Generated by Django 4.0.7 on 2022-11-03 16:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("publicbody", "0043_merge_20221019_1020"),
        ("froide_legalaction", "0016_auto_20221103_1239"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="legaldecision",
            name="foi_law",
        )
    ]
