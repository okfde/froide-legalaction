from django.contrib import admin

from .models import Proposal, ProposalDocument


class ProposalDocumentInline(admin.StackedInline):
    model = ProposalDocument
    raw_id_fields = ('foimessage',)


class ProposalAdmin(admin.ModelAdmin):
    inlines = [ProposalDocumentInline]
    raw_id_fields = ('foirequest', 'publicbody')
    list_display = ('email', 'timestamp', 'publicbody', 'foirequest',
                    'legal_date')


admin.site.register(Proposal, ProposalAdmin)
