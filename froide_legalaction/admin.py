import csv
import json
import os
import tempfile
from io import StringIO

from django.contrib import admin
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import path
from django.utils import timezone
from froide.publicbody.models import FoiLaw, PublicBody
from parler.admin import TranslatableAdmin

from .models import (
    Instance,
    Lawsuit,
    LegalDecision,
    LegalDecisionTag,
    LegalDecisionTagTranslation,
    LegalDecisionTranslation,
    LegalDecisionType,
    LegalDecisionTypeTranslation,
    Proposal,
    ProposalDocument,
)


class InstanceInline(admin.TabularInline):
    model = Instance
    extra = 1
    raw_id_fields = ("court",)


class LawsuitAdmin(admin.ModelAdmin):
    raw_id_fields = (
        "request",
        "publicbody",
        "plaintiff_user",
    )
    # date_hierarchy = 'start_date'
    list_display = ("title", "public", "active", "result")
    list_filter = (
        "active",
        "public",
        "result",
    )
    inlines = [InstanceInline]

    def save_model(self, request, obj, form, change):
        obj.last_update = timezone.now()
        super().save_model(request, obj, form, change)


class ProposalDocumentInline(admin.StackedInline):
    model = ProposalDocument
    raw_id_fields = ("foimessage",)


class ProposalAdmin(admin.ModelAdmin):
    inlines = [ProposalDocumentInline]
    raw_id_fields = ("foirequest", "publicbody")
    list_display = ("email", "timestamp", "publicbody", "foirequest", "legal_date")


class LegalDecisionTypeAdmin(TranslatableAdmin):
    model = LegalDecisionType


class LegalDecisionTagAdmin(TranslatableAdmin):
    model = LegalDecisionTag


class LegalDecisionAdmin(TranslatableAdmin):
    model = LegalDecision
    list_filter = ("type", "tags")
    list_display = ("reference", "court")
    search_fields = ["reference", "translations__court", "translations__abstract"]
    raw_id_fields = ("foi_lawsuit", "foi_document", "foi_court", "foi_law")
    actions = ["export_legal_decisions"]

    def get_urls(self):
        urls = super().get_urls()
        upload_urls = [
            path(
                "upload/",
                self.admin_site.admin_view(self.upload_legal_decisions),
                name="legal_decision-admin_upload",
            ),
        ]
        return upload_urls + urls

    def export_legal_decisions(self, request, queryset):

        all_objects = [
            *queryset,
            *LegalDecisionTranslation.objects.all(),
            *LegalDecisionTag.objects.all(),
            *LegalDecisionTagTranslation.objects.all(),
            *LegalDecisionType.objects.all(),
            *LegalDecisionTypeTranslation.objects.all(),
        ]

        export_json = serializers.serialize("json", all_objects)
        response = HttpResponse(export_json, content_type="application/json")
        response["Content-Disposition"] = "attachment; filename=export.json"
        return response

    def fetch_data_from_db(self, court, law):
        law = FoiLaw.objects.translated(name=law).first()
        court = PublicBody.objects.filter(name=court).first()
        return court, law

    def add_tags_to_legal_decision(self, legal_decision, tags):
        tags = json.loads(tags)
        for tag in tags:
            if len(tag) < 100:
                obj = LegalDecisionTag.objects.translated(name=tag).first()
                if not obj:
                    obj = LegalDecisionTag.objects.create(name=tag)
                legal_decision.tags.add(obj)

    def load_decisions_from_csv(self, csv_file):
        csvf = StringIO(csv_file.read().decode())
        reader = csv.DictReader(csvf)
        for row in reader:
            tags = row.pop("tags")
            court, law = self.fetch_data_from_db(row.get("court"), row.get("law"))
            row.update({"foi_court": court, "foi_law": law})
            ld = LegalDecision.objects.create(**row)
            self.add_tags_to_legal_decision(ld, tags)

    def upload_legal_decisions(self, request):
        if not request.method == "POST":
            raise PermissionDenied
        if not self.has_change_permission(request):
            raise PermissionDenied
        uploaded_file = request.FILES["file"]

        if uploaded_file.content_type == "text/csv":
            self.load_decisions_from_csv(uploaded_file)
            return redirect("admin:froide_legalaction_legaldecision_changelist")

        prefix, suffix = os.path.splitext(uploaded_file.name)
        destination_path = tempfile.mkstemp(suffix=suffix, prefix=prefix + "_")[1]
        with open(destination_path, "wb") as fp:
            for chunk in uploaded_file.chunks():
                fp.write(chunk)
        tmp_fixtures = [destination_path]
        fixtures = [destination_path]
        call_command(
            "loaddata",
            *fixtures,
        )
        for tmp_file in tmp_fixtures:
            os.unlink(tmp_file)
        return redirect("admin:froide_legalaction_legaldecision_changelist")


admin.site.register(Lawsuit, LawsuitAdmin)
admin.site.register(Proposal, ProposalAdmin)
admin.site.register(LegalDecisionTag, LegalDecisionTagAdmin)
admin.site.register(LegalDecisionType, LegalDecisionTypeAdmin)
admin.site.register(LegalDecision, LegalDecisionAdmin)
