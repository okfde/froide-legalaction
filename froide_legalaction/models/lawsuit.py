from datetime import date, timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from froide.foirequest.models import FoiRequest
from froide.publicbody.models import PublicBody

from .decision import LegalDecision


class CourtTypes(models.TextChoices):
    VG = "VG", _("Administrative Court")
    OVG = "OVG", _("Higher Administrative Court")
    BVerwG = "BVerwG", _("Federal Administrative Court")
    LG = "LG", _("Regional Court")
    OLG = "OLG", _("Higher Regional Court")
    BVerfG = "BVerfG", _("Federal Constitutional Court")
    LVerfG = "LVerfG", _("State Constitutional Court")
    EUG = "EUG", _("European General Court")
    EUGH = "EUGH", _("European Court of Justice")
    EMRK = "EMRK", _("European Court of Human Rights")


class UpcomingTrialsManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(public=True)
            .annotate(next_end_date=models.Max("instance__end_date"))
            .filter(next_end_date__gte=date.today())
            .order_by("next_end_date")
        )


class Lawsuit(models.Model):
    class Result(models.TextChoices):
        WON = "won", _("won")
        LOST = "lost", _("lost")
        NOT_ACCEPTED = "not_accepted", _("not accepted")
        PARTIALLY_SUCCESSFUL = "partially_successful", _("partially successful")
        SETTLED = "settled", _("settled")

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

    result = models.CharField(max_length=20, blank=True, choices=Result.choices)

    objects = models.Manager()
    upcoming = UpcomingTrialsManager()

    class Meta:
        verbose_name = _("lawsuit")
        verbose_name_plural = _("lawsuits")
        ordering = ("-last_update",)

    def __str__(self):
        return self.title

    @property
    def instances(self):
        if not hasattr(self, "_instances"):
            self._instances = list(self.instance_set.all())
        return self._instances

    @property
    def first_instance(self):
        try:
            return self.instances[0]
        except IndexError:
            return None

    @property
    def last_instance(self):
        try:
            return self.instances[-1]
        except IndexError:
            return None

    @property
    def start_date(self):
        return self.first_instance.start_date if self.first_instance else None

    @property
    def end_date(self):
        return self.last_instance.end_date if self.last_instance else None

    @property
    def courts(self):
        return [instance.court for instance in self.instances]

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


class InstanceManager(models.Manager):
    def get_last_three_months(self):
        three_months_ago = timezone.now() - timedelta(days=31 * 3)
        return (
            self.get_queryset()
            .filter(end_date__gte=three_months_ago, lawsuit__public=True)
            .order_by("end_date")
        )


class Instance(models.Model):
    lawsuit = models.ForeignKey(Lawsuit, on_delete=models.CASCADE)

    court_type = models.CharField(max_length=25, choices=CourtTypes.choices, blank=True)
    court = models.ForeignKey(
        PublicBody,
        null=True,
        blank=True,
        related_name="court_public_body",
        on_delete=models.SET_NULL,
    )

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    result = models.CharField(max_length=20, blank=True, choices=Lawsuit.Result.choices)
    decision = models.ForeignKey(
        LegalDecision, null=True, blank=True, on_delete=models.SET_NULL
    )

    objects = InstanceManager()

    class Meta:
        verbose_name = _("lawsuit")
        verbose_name_plural = _("lawsuits")
        ordering = ("start_date",)

    def __str__(self):
        return "%s (%s): %s" % (self.lawsuit, self.court_type, self.result)
