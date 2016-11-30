# -*- encoding: utf-8 -*-
import uuid

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from django_fsm import FSMField, transition

from froide.publicbody.models import PublicBody
from froide.foirequest.models import FoiRequest, FoiMessage


@python_2_unicode_compatible
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

    foirequest = models.ForeignKey(FoiRequest, null=True, blank=True)
    publicbody = models.ForeignKey(PublicBody, null=True, blank=True)
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



@python_2_unicode_compatible
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
            'help_text_upload': _('Please upload your first rejection letter.'),
            'help_text': _('Please select the rejection response.'),
            'select': lambda qs, first: qs.filter(is_response=True),
            'initial': None,
        }),
        ('appeal', {
            'label': _('Appeal'),
            'help_text': _('Please choose the message representing your appeal.'),
            'help_text_upload': _('Please upload your appeal to the rejection of your FOI request.'),
            'select': lambda qs, first: qs.filter(is_response=False,
                                timestamp__gt=first.timestamp),
            'initial': None,
        }),
        ('final_rejection', {
            'label': _('Final rejection'),
            'help_text': _('Please choose the message representing the final rejection of your appeal.'),
            'help_text_upload': _('Please upload the final rejection of your appeal.'),
            'select': lambda qs, first: qs.filter(is_response=True),
            'initial': None,
        }),
    )
    DOCUMENT_KINDS_CHOICES = [
        (x[0], x[1]['label']) for x in DOCUMENT_KINDS
    ]
    proposal = models.ForeignKey(Proposal)
    kind = models.CharField(max_length=25, choices=DOCUMENT_KINDS_CHOICES)

    foimessage = models.ForeignKey(FoiMessage, null=True, blank=True)
    date = models.DateField()
    document = models.FileField(blank=True, null=True,
                                upload_to=proposal_document_upload_path)

    class Meta:
        verbose_name = _('legalaction')
        verbose_name_plural = _('legalactions')

    def __str__(self):
        return self.kind
