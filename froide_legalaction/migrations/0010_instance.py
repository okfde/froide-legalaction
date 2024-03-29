# Generated by Django 3.1.8 on 2021-06-07 14:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("publicbody", "0038_foilaw_scale_of_fees"),
        ("froide_legalaction", "0009_auto_20190527_1410"),
    ]

    operations = [
        migrations.CreateModel(
            name="Instance",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "court_type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("VG", "Verwaltungsgericht"),
                            ("OVG", "Oberverwaltungsgericht"),
                            ("BVerwG", "Bundesverwaltungsgericht"),
                            ("LG", "Landgericht"),
                            ("OLG", "Oberlandesgericht"),
                            ("BVerfG", "Bundesverfassungsgericht"),
                            ("LVerfG", "Landesverfassungsgericht"),
                            ("EUG", "Gericht der Europäischen Union"),
                            ("EUGH", "Europäischer Gerichtshof"),
                            ("EMRK", "European Court of Human Rights"),
                        ],
                        max_length=25,
                    ),
                ),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                (
                    "court",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="court_public_body",
                        to="publicbody.publicbody",
                    ),
                ),
                (
                    "lawsuit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="froide_legalaction.lawsuit",
                    ),
                ),
            ],
            options={
                "verbose_name": "lawsuit",
                "verbose_name_plural": "lawsuits",
            },
        ),
    ]
