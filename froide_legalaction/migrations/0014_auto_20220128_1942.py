# Generated by Django 3.2.8 on 2022-01-28 18:42

import django.contrib.postgres.search
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('publicbody', '0039_publicbody_alternative_emails'),
        ('froide_legalaction', '0013_legaldecision_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='legaldecisiontranslation',
            name='search_text',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='legaldecisiontranslation',
            name='search_vector',
            field=django.contrib.postgres.search.SearchVectorField(default='', editable=False),
        )
    ]
