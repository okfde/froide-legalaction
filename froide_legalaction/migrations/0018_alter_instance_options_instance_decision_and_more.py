# Generated by Django 4.2.1 on 2023-06-08 09:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.FILINGCABINET_DOCUMENT_MODEL),
        ("publicbody", "0043_merge_20221019_1020"),
        ("froide_legalaction", "0017_remove_legaldecision_foi_law"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="instance",
            options={
                "ordering": ("start_date",),
                "verbose_name": "lawsuit",
                "verbose_name_plural": "lawsuits",
            },
        ),
        migrations.AddField(
            model_name="instance",
            name="decision",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="froide_legalaction.legaldecision",
            ),
        ),
        migrations.AddField(
            model_name="instance",
            name="result",
            field=models.CharField(
                blank=True,
                choices=[
                    ("won", "won"),
                    ("lost", "lost"),
                    ("not_accepted", "not accepted"),
                    ("partially_successful", "partially successful"),
                    ("settled", "settled"),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="instance",
            name="court_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("VG", "Administrative Court"),
                    ("OVG", "Higher Administrative Court"),
                    ("BVerwG", "Federal Administrative Court"),
                    ("LG", "Regional Court"),
                    ("OLG", "Higher Regional Court"),
                    ("BVerfG", "Federal Constitutional Court"),
                    ("LVerfG", "State Constitutional Court"),
                    ("EUG", "European General Court"),
                    ("EUGH", "European Court of Justice"),
                    ("EMRK", "European Court of Human Rights"),
                ],
                max_length=25,
            ),
        ),
        migrations.AlterField(
            model_name="lawsuit",
            name="result",
            field=models.CharField(
                blank=True,
                choices=[
                    ("won", "won"),
                    ("lost", "lost"),
                    ("not_accepted", "not accepted"),
                    ("partially_successful", "partially successful"),
                    ("settled", "settled"),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="legaldecision",
            name="date",
            field=models.DateField(blank=True, null=True, verbose_name="Date"),
        ),
        migrations.AlterField(
            model_name="legaldecision",
            name="foi_court",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="pb_legaldecisions",
                to="publicbody.publicbody",
                verbose_name="Link to Court",
            ),
        ),
        migrations.AlterField(
            model_name="legaldecision",
            name="foi_document",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.FILINGCABINET_DOCUMENT_MODEL,
                verbose_name="Document",
            ),
        ),
        migrations.AlterField(
            model_name="legaldecision",
            name="foi_laws",
            field=models.ManyToManyField(
                blank=True,
                related_name="legal_decisions",
                to="publicbody.foilaw",
                verbose_name="Laws",
            ),
        ),
        migrations.AlterField(
            model_name="legaldecision",
            name="foi_lawsuit",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="froide_legalaction.lawsuit",
                verbose_name="Lawsuit",
            ),
        ),
        migrations.AlterField(
            model_name="legaldecision",
            name="outcome",
            field=models.CharField(blank=True, max_length=500, verbose_name="Outcome"),
        ),
        migrations.AlterField(
            model_name="legaldecision",
            name="paragraphs",
            field=models.JSONField(blank=True, default=list, verbose_name="Paragraphs"),
        ),
        migrations.AlterField(
            model_name="legaldecision",
            name="reference",
            field=models.CharField(
                blank=True, max_length=200, verbose_name="Reference"
            ),
        ),
        migrations.AlterField(
            model_name="legaldecision",
            name="type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="froide_legalaction.legaldecisiontype",
                verbose_name="Legal Decision Type",
            ),
        ),
        migrations.AlterField(
            model_name="legaldecisiontranslation",
            name="abstract",
            field=models.TextField(blank=True, verbose_name="Abstract"),
        ),
        migrations.AlterField(
            model_name="legaldecisiontranslation",
            name="court",
            field=models.CharField(
                blank=True, max_length=500, verbose_name="Name of Court"
            ),
        ),
        migrations.AlterField(
            model_name="legaldecisiontranslation",
            name="law",
            field=models.CharField(blank=True, max_length=500, verbose_name="Law"),
        ),
    ]
