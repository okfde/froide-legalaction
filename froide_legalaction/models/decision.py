import functools

from django.conf import settings
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from django.db.models import Q
from django.template import defaultfilters
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from parler.managers import TranslatableManager
from parler.models import TranslatableModel, TranslatedFields

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


class LegalDecisionManager(TranslatableManager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("translations")

    def all_incomplete(self):
        return self.filter(
            Q(reference="")
            | Q(date__isnull=True)
            | Q(type__isnull=True)
            | Q(translations__abstract="")
            | Q(foi_laws__isnull=True)
            | Q(foi_court__isnull=True, translations__court="")
        )

    def get_search_vector(self, language):
        SEARCH_LANG = "simple"

        if language == "de":
            SEARCH_LANG = "german"
        elif language == "en":
            SEARCH_LANG = "english"

        fields = [
            ("search_text", "A"),
        ]
        return functools.reduce(
            lambda a, b: a + b,
            [SearchVector(f, weight=w, config=SEARCH_LANG) for f, w in fields],
        )

    def update_search_index(self, qs=None):
        from froide_legalaction.models import LegalDecisionTranslation

        if qs is None:
            qs = self.get_queryset()
        for decision in qs:
            decision.generate_search_texts()
        translations = LegalDecisionTranslation.objects.all()
        languages = [entry.get("code") for entry in settings.PARLER_LANGUAGES.get(1)]
        for language in languages:
            translations_for_lang = translations.filter(language_code=language)
            search_vector = self.get_search_vector(language)
            translations_for_lang.update(search_vector=search_vector)


class LegalDecision(TranslatableModel):
    class LegalDecisionTypes(models.TextChoices):
        COURT_NOTICE = "court_notice", _("Court Notice")
        COURT_DECISION = "court_decision", _("Court Decision")
        COURT_RULING = "court_ruling", _("Court Ruling")

    slug = models.SlugField(
        max_length=255, blank=True, null=True, unique=True, verbose_name=_("Slug")
    )
    translations = TranslatedFields(
        abstract=models.TextField(blank=True, verbose_name=_("Abstract")),
        fulltext=models.TextField(blank=True),
        verbose_name=_("Fulltext"),
        court=models.CharField(
            max_length=500, blank=True, verbose_name=_("Name of Court")
        ),
        law=models.CharField(max_length=500, blank=True, verbose_name=_("Law")),
        search_text=models.TextField(blank=True),
        search_vector=SearchVectorField(default="", editable=False),
    )

    tags = models.ManyToManyField(LegalDecisionTag, blank=True)
    decision_type = models.CharField(
        choices=LegalDecisionTypes.choices, max_length=20, blank=True
    )

    date = models.DateField(blank=True, null=True, verbose_name=_("Date"))
    outcome = models.CharField(max_length=500, blank=True, verbose_name=_("Outcome"))
    reference = models.CharField(
        max_length=200, blank=True, verbose_name=_("Reference")
    )
    ecli = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("European Case Law Identifier"),
    )
    paragraphs = models.JSONField(
        default=list, blank=True, verbose_name=_("Paragraphs")
    )

    source_data = models.JSONField(blank=True, null=True)

    foi_lawsuit = models.ForeignKey(
        "froide_legalaction.Lawsuit",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Lawsuit"),
    )
    foi_document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Document"),
    )
    foi_court = models.ForeignKey(
        PublicBody,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pb_legaldecisions",
        verbose_name=_("Link to Court"),
    )
    foi_laws = models.ManyToManyField(
        FoiLaw, related_name="legal_decisions", blank=True, verbose_name=_("Laws")
    )

    objects = LegalDecisionManager()

    def __str__(self):
        return "{}".format(self.reference)

    def get_absolute_url(self):
        return reverse("legal-decision-detail", kwargs={"pk": self.pk})

    @property
    def formatted_date(self):
        return defaultfilters.date(self.date, "DATE_FORMAT")

    @property
    def title(self):
        if self.decision_type and self.court_name:
            if self.date:
                return _("{} of {} on {}").format(
                    self.decision_type, self.court_name, str(self.formatted_date)
                )
            return _("{} of {}").format(self.decision_type, self.court_name)
        if self.foi_document:
            return self.foi_document.title
        return self.reference

    @property
    def court_name(self):
        if self.foi_court:
            return self.foi_court.name
        return self.court

    @property
    def law_name(self):
        if self.foi_laws:
            return ", ".join([foi_law.name for foi_law in self.foi_laws.all()])
        return self.law

    def abstract_is_set(self):
        try:
            self.abstract
            return not self.abstract == ""
        except self.DoesNotExist:
            return False

    def court_is_set(self):
        if not self.foi_court:
            try:
                self.court
                return True
            except self.DoesNotExist:
                return False
        return True

    @property
    def fields_incomplete(self):
        from froide_legalaction.models import LegalDecisionTranslation

        relevant_fields = [
            "reference",
            "date",
            "abstract",
            "foi_court",
            "decision_type",
        ]
        res = []

        fields = self._meta.fields
        translated_fields = LegalDecisionTranslation._meta.get_fields()
        all_fields = fields + translated_fields

        for field in all_fields:
            is_relevant = field.name in relevant_fields
            has_field = hasattr(self, field.name)
            if is_relevant:
                if has_field and not getattr(self, field.name):
                    res.append(str(field.verbose_name))
                elif not has_field:
                    res.append(str(field.verbose_name))
        if not self.foi_laws.all():
            res.append(str(_("Laws")))
        return ", ".join(res)

    def generate_search_texts(self):
        for translation in self.translations.all():
            fulltext = ""
            if translation.fulltext:
                fulltext = translation.fulltext
            text = "{} {} {} {}".format(
                self.reference, translation.law, translation.abstract, fulltext
            )
            translation.search_text = text
            translation.save()
