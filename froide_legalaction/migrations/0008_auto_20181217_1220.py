# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-12-17 11:20
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("froide_legalaction", "0007_auto_20181107_1950"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lawsuit",
            name="court",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="ruling_over",
                to="publicbody.PublicBody",
            ),
        ),
        migrations.AlterField(
            model_name="lawsuit",
            name="plaintiff_user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="lawsuit",
            name="publicbody",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="defendant_in",
                to="publicbody.PublicBody",
            ),
        ),
        migrations.AlterField(
            model_name="lawsuit",
            name="request",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="foirequest.FoiRequest",
            ),
        ),
    ]
