import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings

from django_fsm import FSMField

from froide.publicbody.models import PublicBody
from froide.foirequest.models import FoiRequest, FoiMessage

RESULTS = (
    ("won", _("gewonnen")),
    ("lost", _("verloren")),
    ("not_accepted", _("nicht angenommen")),
    ("partially_successful", _("teilweise erfolgreich")),
    ("settled", _("Erledigung")),
)

COURTS = (
    ("VG", _("Verwaltungsgericht")),
    ("OVG", _("Oberverwaltungsgericht")),
    ("BVerwG", _("Bundesverwaltungsgericht")),
    ("LG", _("Landgericht")),
    ("OLG", _("Oberlandesgericht")),
    ("BVerfG", _("Bundesverfassungsgericht")),
    ("LVerfG", _("Landesverfassungsgericht")),
    ("EUG", _("Gericht der Europäischen Union")),
    ("EUGH", _("Europäischer Gerichtshof")),
    ("EMRK", _("European Court of Human Rights")),
)


class Lawsuit(models.Model):
    title = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    last_update = models.DateField(null=True)

    costs = models.DecimalField(null=True, blank=True, decimal_places=2, max_digits=10)
    costs_covered = models.DecimalField(
        null=True, blank=True, decimal_places=2, max_digits=10
    )
    cost_detail = models.TextField(blank=True)

    links = models.TextField(blank=True)

    request = models.ForeignKey(
        FoiRequest, null=True, blank=True, on_delete=models.SET_NULL
    )
    publicbody = models.ForeignKey(
        PublicBody,
        null=True,
        blank=True,
        related_name="defendant_in",
        on_delete=models.SET_NULL,
    )

    plaintiff = models.CharField(max_length=255, blank=True)
    plaintiff_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    active = models.BooleanField(default=True)
    public = models.BooleanField(default=False)

    result = models.CharField(max_length=20, blank=True, choices=RESULTS)

    class Meta:
        verbose_name = _("lawsuit")
        verbose_name_plural = _("lawsuits")
        ordering = ("-last_update",)

    def __str__(self):
        return self.title

    @property
    def instances(self):
        return Instance.objects.filter(lawsuit=self).select_related("court")

    @property
    def first_instance(self):
        return self.instances.order_by("start_date").first()

    @property
    def last_instance(self):
        return self.instances.order_by("-start_date").first()

    @property
    def start_date(self):
        return self.first_instance.start_date if self.first_instance else None

    @property
    def end_date(self):
        return self.last_instance.end_date if self.last_instance else None

    @property
    def courts(self):
        return map(lambda instance: instance.court, self.instances)

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
            return "secondary"
        if self.result in ("won", "partially_successful", "settled"):
            return "success"
        if self.result in ("lost", "not_accepted"):
            return "danger"
        return "secondary"

    @property
    def result_icon(self):
        if self.active:
            return "clock-o"
        if self.result in ("won", "partially_successful", "settled"):
            return "check"
        if self.result in ("lost", "not_accepted"):
            return "times"
        return "clock-o"


class Instance(models.Model):
    lawsuit = models.ForeignKey(Lawsuit, on_delete=models.CASCADE)

    court_type = models.CharField(max_length=25, choices=COURTS, blank=True)
    court = models.ForeignKey(
        PublicBody,
        null=True,
        blank=True,
        related_name="court_public_body",
        on_delete=models.SET_NULL,
    )

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = _("lawsuit")
        verbose_name_plural = _("lawsuits")


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
