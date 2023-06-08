import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_fsm import FSMField

from froide.foirequest.models import FoiMessage, FoiRequest
from froide.publicbody.models import PublicBody


class Proposal(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now)
    decision_date = models.DateTimeField(null=True, blank=True)
    state = FSMField(default="new")

    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    email = models.EmailField(max_length=255, blank=True)
    phone = models.CharField(max_length=255, blank=True)

    foirequest = models.ForeignKey(
        FoiRequest, null=True, blank=True, on_delete=models.SET_NULL
    )
    publicbody = models.ForeignKey(
        PublicBody, null=True, blank=True, on_delete=models.SET_NULL
    )
    legal_date = models.DateField(blank=True, null=True)

    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _("proposal for legal action")
        verbose_name_plural = _("proposals for legal action")

    def __str__(self):
        return self.last_name


def proposal_document_upload_path(instance, filename):
    uid = str(instance.proposal.uid)
    uid_1 = uid[:2]
    uid_2 = uid[2:4]
    return "legalaction/{0}/{1}/{2}/{3}.pdf".format(uid_1, uid_2, uid, instance.kind)


class ProposalDocument(models.Model):
    DOCUMENT_KINDS = (
        (
            "foirequest",
            {
                "label": _("FOI request"),
                "help_text_upload": _("Please upload your original FOI request."),
                "help_text": _("The original FOI request you made."),
                "select": lambda qs, first: qs.filter(pk=first.pk),
                "hidden": True,
                "initial": lambda qs, first: first,
                "required": True,
            },
        ),
        (
            "rejection",
            {
                "label": _("Rejection"),
                "help_text_upload": _("Please upload your first " "rejection letter."),
                "help_text": _("Please select the rejection response."),
                "select": lambda qs, first: qs.filter(is_response=True),
                "initial": None,
                "required": True,
            },
        ),
        (
            "appeal",
            {
                "label": _("Appeal"),
                "help_text": _(
                    "Please choose the message representing " "your appeal."
                ),
                "help_text_upload": _(
                    "Please upload your appeal to the " "rejection of your FOI request."
                ),
                "select": lambda qs, first: qs.filter(
                    is_response=False, timestamp__gt=first.timestamp
                ),
                "initial": None,
                "required": False,
            },
        ),
        (
            "final_rejection",
            {
                "label": _("Final rejection"),
                "help_text": _(
                    "Please choose the message representing the "
                    "final rejection of your appeal."
                ),
                "help_text_upload": _(
                    "Please upload the final rejection " "of your appeal."
                ),
                "select": lambda qs, first: qs.filter(is_response=True),
                "initial": None,
                "required": False,
            },
        ),
    )
    DOCUMENT_KINDS_CHOICES = [(x[0], x[1]["label"]) for x in DOCUMENT_KINDS]
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    kind = models.CharField(max_length=25, choices=DOCUMENT_KINDS_CHOICES)

    foimessage = models.ForeignKey(
        FoiMessage, null=True, blank=True, on_delete=models.SET_NULL
    )
    date = models.DateField()
    document = models.FileField(
        blank=True, null=True, upload_to=proposal_document_upload_path
    )

    class Meta:
        verbose_name = _("legalaction document")
        verbose_name_plural = _("legalaction documents")

    def __str__(self):
        return self.kind

    def get_bytes(self):
        if not self.document:
            return b""
        self.document.open(mode="rb")
        try:
            return self.document.read()
        finally:
            self.document.close()
