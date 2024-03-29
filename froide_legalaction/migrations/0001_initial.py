# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-30 00:28
from __future__ import unicode_literals

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import django_fsm

import froide_legalaction.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("foirequest", "0001_initial"),
        ("publicbody", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Proposal",
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
                ("uid", models.UUIDField(default=uuid.uuid4, editable=False)),
                ("timestamp", models.DateTimeField(default=django.utils.timezone.now)),
                ("decision_date", models.DateTimeField(blank=True, null=True)),
                ("state", django_fsm.FSMField(default=b"new", max_length=50)),
                ("first_name", models.CharField(blank=True, max_length=255)),
                ("last_name", models.CharField(blank=True, max_length=255)),
                ("address", models.TextField(blank=True)),
                ("email", models.EmailField(blank=True, max_length=255)),
                ("phone", models.CharField(blank=True, max_length=255)),
                ("legal_date", models.DateField(blank=True)),
                ("description", models.TextField(blank=True)),
                (
                    "foirequest",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="foirequest.FoiRequest",
                    ),
                ),
                (
                    "publicbody",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="publicbody.PublicBody",
                    ),
                ),
            ],
            options={
                "verbose_name": "proposal for legal action",
                "verbose_name_plural": "proposals for legal action",
            },
        ),
        migrations.CreateModel(
            name="ProposalDocument",
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
                    "kind",
                    models.CharField(
                        choices=[
                            (b"foirequest", "FOI request"),
                            (b"rejection", "Rejection"),
                            (b"appeal", "Appeal"),
                            (b"final_rejection", "Final rejection"),
                        ],
                        max_length=25,
                    ),
                ),
                ("date", models.DateField()),
                (
                    "document",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to=froide_legalaction.models.proposal.proposal_document_upload_path,
                    ),
                ),
                (
                    "foimessage",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="foirequest.FoiMessage",
                    ),
                ),
                (
                    "proposal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="froide_legalaction.Proposal",
                    ),
                ),
            ],
            options={
                "verbose_name": "legalaction",
                "verbose_name_plural": "legalactions",
            },
        ),
    ]
