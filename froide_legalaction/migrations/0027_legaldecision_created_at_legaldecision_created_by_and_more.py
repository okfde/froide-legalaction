# Generated by Django 4.2.4 on 2024-07-04 14:25

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("froide_legalaction", "0026_legaldecision_source_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="legaldecision",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="legaldecision",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_legaldecisions",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="legaldecision",
            name="decision_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("court_notice", "Court Notice"),
                    ("court_decision", "Court Decision"),
                    ("court_ruling", "Court Ruling"),
                    ("court_order", "Court Order"),
                ],
                max_length=20,
                verbose_name="Decision Type",
            ),
        ),
    ]
