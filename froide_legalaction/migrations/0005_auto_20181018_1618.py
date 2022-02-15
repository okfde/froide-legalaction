# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-10-18 14:18
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('froide_legalaction', '0004_lawsuit'),
    ]

    operations = [
        migrations.AddField(
            model_name='lawsuit',
            name='cost_detail',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='lawsuit',
            name='reference',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='lawsuit',
            name='court',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ruling_over', to='publicbody.PublicBody'),
        ),
        migrations.AlterField(
            model_name='lawsuit',
            name='publicbody',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='defendant_in', to='publicbody.PublicBody'),
        ),
        migrations.AlterField(
            model_name='lawsuit',
            name='result',
            field=models.CharField(blank=True, choices=[('won', 'gewonnen'), ('lost', 'verloren'), ('settled', 'Erledigung')], max_length=20),
        ),
    ]
