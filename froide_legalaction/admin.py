import os
import tempfile

from django.contrib import admin
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import path
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from froide.helper.admin_utils import (
    ForeignKeyFilter,
    make_emptyfilter,
    make_nullfilter,
)
from parler.admin import TranslatableAdmin

from .models import (
    Instance,
    Lawsuit,
    LegalDecision,
    LegalDecisionTag,
    LegalDecisionTagTranslation,
    LegalDecisionTranslation,
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
        ("publicbody", ForeignKeyFilter),
        make_nullfilter("costs", _("Has Costs")),
    )
    search_fields = ["title", "reference"]
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


class LegalDecisionTagAdmin(TranslatableAdmin):
    model = LegalDecisionTag


class LegalDecisionAdmin(TranslatableAdmin):
    model = LegalDecision
    list_filter = (
        "decision_type",
        "foi_court__jurisdiction",
        ("foi_court", ForeignKeyFilter),
        make_nullfilter("ecli", _("Has ECLI")),
        make_emptyfilter("reference", _("Has reference")),
        make_nullfilter("date", _("Has date")),
        make_emptyfilter("decision_type", _("Has decision type")),
        make_emptyfilter("translations__abstract", _("Has abstract")),
    )
    list_display = ("reference", "court")
    search_fields = ["reference", "translations__court", "translations__abstract"]
    raw_id_fields = (
        "foi_lawsuit",
        "foi_document",
        "foi_court",
        "foi_laws",
        "created_by",
    )
    actions = ["export_legal_decisions", "update_search_index"]

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

    def update_search_index(self, request, queryset):
        LegalDecision.objects.update_search_index(qs=queryset)

    def export_legal_decisions(self, request, queryset):
        all_objects = [
            *queryset,
            *LegalDecisionTranslation.objects.all(),
            *LegalDecisionTag.objects.all(),
            *LegalDecisionTagTranslation.objects.all(),
        ]

        export_json = serializers.serialize("json", all_objects)
        response = HttpResponse(export_json, content_type="application/json")
        response["Content-Disposition"] = "attachment; filename=export.json"
        return response

    def upload_legal_decisions(self, request):
        if not request.method == "POST":
            raise PermissionDenied
        if not self.has_change_permission(request):
            raise PermissionDenied
        uploaded_file = request.FILES["file"]
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
admin.site.register(LegalDecision, LegalDecisionAdmin)
