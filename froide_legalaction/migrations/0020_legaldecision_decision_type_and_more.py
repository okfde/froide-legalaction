# Generated by Django 4.2.1 on 2023-06-14 10:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("froide_legalaction", "0019_legaldecision_ecli_legaldecision_slug_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="legaldecision",
            name="decision_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("court_notice", "Court Notice"),
                    ("court_decision", "Court Decision"),
                    ("court_ruling", "Court Ruling"),
                ],
                max_length=20,
            ),
        ),
    ]
