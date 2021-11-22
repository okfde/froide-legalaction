from django.contrib import admin
from django.utils import timezone

from parler.admin import TranslatableAdmin

from .models import (
    Instance,
    Lawsuit,
    Proposal,
    ProposalDocument,
    LegalDecisionType,
    LegalDecision,
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


class LegalDecisionAdmin(TranslatableAdmin):
    model = LegalDecision


admin.site.register(Lawsuit, LawsuitAdmin)
admin.site.register(Proposal, ProposalAdmin)
admin.site.register(LegalDecisionType, LegalDecisionTypeAdmin)
admin.site.register(LegalDecision, LegalDecisionAdmin)
