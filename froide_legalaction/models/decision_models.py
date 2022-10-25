import functools

from django.conf import settings
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from django.utils.translation import gettext_lazy as _
from froide.document.models import Document
from froide.publicbody.models import FoiLaw, PublicBody
from parler.managers import TranslatableManager
from parler.models import TranslatableModel, TranslatedFields


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


class LegalDecisionManager(TranslatableManager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("translations")

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

    translations = TranslatedFields(
        abstract=models.TextField(blank=True),
        fulltext=models.TextField(blank=True),
        court=models.CharField(max_length=500, blank=True),
        law=models.CharField(max_length=500, blank=True),
        search_text=models.TextField(blank=True),
        search_vector=SearchVectorField(default="", editable=False),
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

    objects = LegalDecisionManager()

    def __str__(self):
        return "{}".format(self.reference)

    @property
    def title(self):
        if self.date and self.type:
            return _("{} of {} on {}").format(
                self.type, self.court_name, str(self.date)
            )
        return self.court_name

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
