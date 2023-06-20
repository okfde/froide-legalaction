import logging
from datetime import datetime
from typing import Tuple

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from filingcabinet.api import create_document
from slugify import slugify

from froide.publicbody.models import Classification, PublicBody

from ..decision_identifier import make_slug
from ..models import LegalDecision, LegalDecisionTag

logger = logging.getLogger(__name__)


class BaseLoader:
    jurisdiction = None
    language_code = settings.LANGUAGE_CODE
    base_classification_slug = "gericht"

    def load(self, path):
        logger.info("Loading %s", path)
        for decision in self.load_path(path):
            if not decision.pk:
                _, created = self.save_decision(decision)
                if created:
                    logger.info("Imported %s", decision)
                else:
                    logger.info("Found %s", decision)

    def save_decision(self, decision: LegalDecision) -> Tuple[LegalDecision, bool]:
        try:
            decision.slug = make_slug(decision)
        except ValueError:
            pass
        already = self.already_exists(decision)
        if already:
            if hasattr(self, "apply_update"):
                self.apply_update(already, decision)
            return (already, False)
        decision.save()
        return (decision, True)

    def get_court(self, name):
        logger.info("Getting court %s", name)
        base_classification = Classification.objects.get(
            slug=self.base_classification_slug
        )
        sub_classifications = list(base_classification.get_descendants()) + [
            base_classification
        ]
        qs = PublicBody.non_filtered_objects.all()
        qs = qs.filter(classification__in=sub_classifications)
        if self.jurisdiction:
            qs = qs.filter(jurisdiction__name=self.jurisdiction)

        try:
            return qs.get(name__istartswith=name)
        except PublicBody.DoesNotExist:
            pass
        return qs.filter(Q(name__icontains=name) | Q(other_names__icontains=name)).get()

    def get_decision_type(self, name):
        reverse_map = {str(v): k for k, v in LegalDecision.LegalDecisionTypes.choices}
        if name in reverse_map:
            return reverse_map[name]
        return ""

    def already_exists(self, decision):
        filt = Q(
            reference=decision.reference,
            date=decision.date,
            foi_court=decision.foi_court,
        )
        if decision.ecli:
            filt |= Q(ecli=decision.ecli)
        if decision.slug:
            filt |= Q(slug=decision.slug)
        if decision.source_url:
            filt |= Q(source_url=decision.source_url)
        return LegalDecision.objects.filter(filt).first()

    def add_tags(self, decision, tags):
        for tag in tags:
            ld_tag = LegalDecisionTag.objects.filter(translations__name=tag).first()
            if ld_tag is None:
                ld_tag = LegalDecisionTag.objects.create(name=tag, slug=slugify(tag))
            decision.tags.add(ld_tag)

    def add_document(self, decision: LegalDecision, pdf_filepath):
        title = "{reference}, {court} ({dd}.{mm}.{yyyy})".format(
            reference=decision.reference,
            court=decision.court,
            dd=decision.date.day,
            mm=decision.date.month,
            yyyy=decision.date.year,
        )
        with open(pdf_filepath, "rb") as f:
            published_at = timezone.make_aware(
                datetime.combine(decision.date, datetime.min.time())
            )
            document = create_document(
                f,
                {
                    "title": title,
                    "published_at": published_at,
                    "collection": self.collection,
                },
                process=False,
            )
        decision.foi_document = document
        decision.save(update_fields=["foi_document"])
