import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.conf import settings

from django_fsm import FSMField

from froide.publicbody.models import PublicBody
from froide.foirequest.models import FoiRequest, FoiMessage


class Lawsuit(models.Model):
    title = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    start_date = models.DateField(null=True, blank=True)
    last_update = models.DateField(null=True)
    end_date = models.DateField(null=True, blank=True)

    costs = models.DecimalField(
        null=True, blank=True,
        decimal_places=2, max_digits=10
    )
    costs_covered = models.DecimalField(
        null=True, blank=True,
        decimal_places=2, max_digits=10
    )
    cost_detail = models.TextField(blank=True)

    links = models.TextField(blank=True)

    request = models.ForeignKey(FoiRequest, null=True, blank=True)
    publicbody = models.ForeignKey(
        PublicBody, null=True, blank=True,
        related_name='defendant_in')

    court_type = models.CharField(max_length=25, choices=(
        ('VG', _('Verwaltungsgericht')),
        ('OVG', _('Oberverwaltungsgericht')),
        ('BVerwG', _('Bundesverwaltungsgericht')),
        ('BVerfG', _('Bundesverfassungsgericht')),
        ('LVerfG', _('Landesverfassungsgericht')),
        ('EUG', _('Gericht der Europäischen Union')),
        ('EUGH', _('Europäischer Gerichtshof')),
        ('EMRK', _('European Court of Human Rights')),
    ), blank=True)
    court = models.ForeignKey(
        PublicBody, null=True, blank=True,
        related_name='ruling_over'
    )
    plaintiff = models.CharField(max_length=255, blank=True)
    plaintiff_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True)
    active = models.BooleanField(default=True)

    result = models.CharField(max_length=20, blank=True, choices=(
        ('won', _('gewonnen')),
        ('lost', _('verloren')),
        ('not_accepted', _('nicht angenommen')),
        ('partially_successful', _('teilweise erfolgreich')),
        ('settled', _('Erledigung')),
    ))
    public = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('lawsuit')
        verbose_name_plural = _('lawsuits')
        ordering = ('-last_update',)

    def __str__(self):
        return self.title

    @property
    def costs_covered_percent(self):
        if self.costs and self.costs_covered:
            return int(self.costs_covered / self.costs * 100)
        return None

    @property
    def costs_deficit(self):
        if self.costs and self.costs_covered:
            return self.costs - self.costs_covered
        return None

    @property
    def needs_money(self):
        if self.costs and self.costs_covered:
            return self.costs_covered < self.costs
        return None

    @property
    def plaintiff_name(self):
        if self.plaintiff_user:
            return self.plaintiff_user.get_full_name()
        return self.plaintiff

    @property
    def result_bootstrap_class(self):
        if self.active:
            return 'light'
        if self.result in ('won', 'partially_successful'):
            return 'success'
        if self.result in ('lost', 'not_accepted'):
            return 'dark'
        if self.result in ('settled',):
            return 'secondary'
        return 'light'


class Proposal(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now)
    decision_date = models.DateTimeField(null=True, blank=True)
    state = FSMField(default='new')

    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    email = models.EmailField(max_length=255, blank=True)
    phone = models.CharField(max_length=255, blank=True)

    foirequest = models.ForeignKey(FoiRequest, null=True, blank=True,
                                   on_delete=models.SET_NULL)
    publicbody = models.ForeignKey(PublicBody, null=True, blank=True,
                                   on_delete=models.SET_NULL)
    legal_date = models.DateField(blank=True, null=True)

    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _('proposal for legal action')
        verbose_name_plural = _('proposals for legal action')

    def __str__(self):
        return self.last_name


def proposal_document_upload_path(instance, filename):
    uid = str(instance.proposal.uid)
    uid_1 = uid[:2]
    uid_2 = uid[2:4]
    return 'legalaction/{0}/{1}/{2}/{3}.pdf'.format(
        uid_1, uid_2, uid, instance.kind
    )


class ProposalDocument(models.Model):
    DOCUMENT_KINDS = (
        ('foirequest', {
            'label': _('FOI request'),
            'help_text_upload': _('Please upload your original FOI request.'),
            'help_text': _('The original FOI request you made.'),
            'select': lambda qs, first: qs.filter(pk=first.pk),
            'hidden': True,
            'initial': lambda qs, first: first,
        }),
        ('rejection', {
            'label': _('Rejection'),
            'help_text_upload': _('Please upload your first '
                                  'rejection letter.'),
            'help_text': _('Please select the rejection response.'),
            'select': lambda qs, first: qs.filter(is_response=True),
            'initial': None,
        }),
        ('appeal', {
            'label': _('Appeal'),
            'help_text': _('Please choose the message representing '
                           'your appeal.'),
            'help_text_upload': _('Please upload your appeal to the '
                                  'rejection of your FOI request.'),
            'select': lambda qs, first: qs.filter(
                is_response=False,
                timestamp__gt=first.timestamp),
            'initial': None,
        }),
        ('final_rejection', {
            'label': _('Final rejection'),
            'help_text': _('Please choose the message representing the '
                           'final rejection of your appeal.'),
            'help_text_upload': _('Please upload the final rejection '
                                  'of your appeal.'),
            'select': lambda qs, first: qs.filter(is_response=True),
            'initial': None,
        }),
    )
    DOCUMENT_KINDS_CHOICES = [
        (x[0], x[1]['label']) for x in DOCUMENT_KINDS
    ]
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    kind = models.CharField(max_length=25, choices=DOCUMENT_KINDS_CHOICES)

    foimessage = models.ForeignKey(FoiMessage, null=True, blank=True,
                                   on_delete=models.SET_NULL)
    date = models.DateField()
    document = models.FileField(blank=True, null=True,
                                upload_to=proposal_document_upload_path)

    class Meta:
        verbose_name = _('legalaction document')
        verbose_name_plural = _('legalaction documents')

    def __str__(self):
        return self.kind
