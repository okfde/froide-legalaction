from django.db import models
from django.utils.translation import gettext_lazy as _

from parler.models import TranslatableModel, TranslatedFields
from parler.managers import TranslatableManager

from froide.document.models import Document
from froide.publicbody.models import FoiLaw, PublicBody


class LegalDecisionTagManager(TranslatableManager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("translations")


class LegalDecisionTag(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(verbose_name=_("name"), unique=False, max_length=100),
        slug=models.SlugField(verbose_name=_("slug"), unique=False, max_length=100),
    )

    objects = LegalDecisionTagManager()

    def __str__(self):
        return self.name


class LegalDecisionTypeManager(TranslatableManager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("translations")


class LegalDecisionType(TranslatableModel):
    translations = TranslatedFields(
        title=models.CharField(_("title"), max_length=255),
        slug=models.SlugField(_("slug"), unique=False, max_length=255),
    )

    objects = LegalDecisionTypeManager()

    class Meta:
        verbose_name = _("Legal Decision Type")
        verbose_name_plural = _("Legal Decision Types")

    def __str__(self):
        return self.title


class LegalDecision(TranslatableModel):

    translations = TranslatedFields(
        abstract=models.TextField(blank=True),
        fulltext=models.TextField(blank=True),
        court=models.CharField(max_length=500, blank=True),
        law=models.CharField(max_length=500, blank=True),
    )

    tags = models.ManyToManyField(LegalDecisionTag, blank=True)
    type = models.ForeignKey(
        LegalDecisionType, on_delete=models.SET_NULL, null=True, blank=True
    )

    date = models.DateField(blank=True, null=True)
    outcome = models.CharField(max_length=500, blank=True)
    reference = models.CharField(max_length=200)
    paragraphs = models.JSONField(default=list, blank=True)

    source_data = models.JSONField(blank=True, null=True)

    foi_lawsuit = models.ForeignKey(
        "froide_legalaction.Lawsuit", on_delete=models.SET_NULL, null=True, blank=True
    )
    foi_document = models.ForeignKey(
        Document, on_delete=models.SET_NULL, null=True, blank=True
    )
    foi_court = models.ForeignKey(
        PublicBody,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pb_legaldecisions",
    )
    foi_law = models.ForeignKey(
        FoiLaw,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="foi_law_legaldecisions",
    )

    def __str__(self):
        return "{}".format(self.reference)

    @property
    def title(self):
        if self.date:
            return _("{} of {} on {}").format(
                self.type, self.court_name, str(self.date)
            )
        return _("{} of {}").format(self.type, self.court_name)

    @property
    def court_name(self):
        if self.foi_court:
            return self.foi_court.name
        return self.court

    @property
    def law_name(self):
        if self.foi_law:
            return self.foi_law.name
        return self.law
