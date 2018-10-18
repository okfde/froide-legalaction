from django.contrib import admin
from django.utils import timezone

from .models import Lawsuit, Proposal, ProposalDocument


class LawsuitAdmin(admin.ModelAdmin):
    raw_id_fields = ('request', 'publicbody')
    date_hierarchy = 'start_date'
    list_display = ('title', 'start_date', 'court_type',
                    'active', 'result')
    list_filter = ('active', 'result', 'court_type',)

    def save_model(self, request, obj, form, change):
        obj.last_update = timezone.now()
        super().save_model(request, obj, form, change)


class ProposalDocumentInline(admin.StackedInline):
    model = ProposalDocument
    raw_id_fields = ('foimessage',)


class ProposalAdmin(admin.ModelAdmin):
    inlines = [ProposalDocumentInline]
    raw_id_fields = ('foirequest', 'publicbody')
    list_display = ('email', 'timestamp', 'publicbody', 'foirequest',
                    'legal_date')


admin.site.register(Lawsuit, LawsuitAdmin)
admin.site.register(Proposal, ProposalAdmin)
