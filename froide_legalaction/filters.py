from django.db.models import Count
from django.db.models.functions import TruncYear
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from django_filters import FilterSet, ModelChoiceFilter, ChoiceFilter

from froide.publicbody.models import Classification, FoiLaw, PublicBody

from .models import LegalDecision, LegalDecisionType
from .widgets import CustomLinkWidget


def get_foi_courts():
    vg_classification = Classification.objects.get(slug="verwaltungsgerichte")
    children = vg_classification.get_children().values_list("id", flat=True)
    ids = list(children) + [vg_classification.id]
    return PublicBody.objects.filter(classification__id__in=ids).exclude(
        pb_legaldecisions=None
    )


def get_foi_laws():
    return FoiLaw.objects.exclude(foi_law_legaldecisions=None)


def get_years_for_choices():
    years = (
        LegalDecision.objects.annotate(year=TruncYear("date"))
        .values("year")
        .annotate(c=Count("id"))
        .values("year", "c")
        .order_by("-year")
    )
    result = []
    for year_entry in years:
        if year_entry.get("year"):
            year = year_entry.get("year").year
            count = year_entry.get("c")
            result.append((year, "{} ({})".format(str(year), str(count))))
    return result


def get_types_for_choices():
    types = LegalDecisionType.objects.annotate(
        decision_count=Count("legaldecision")
    ).order_by("-decision_count")
    result = []
    for type in types:
        result.append((type.id, "{} ({})".format(type.title, str(type.decision_count))))
    return result


class LegalDecisionFilterSet(FilterSet):
    foi_court = ModelChoiceFilter(
        queryset=get_foi_courts(), widget=CustomLinkWidget, label=_("by Court")
    )
    foi_law = ModelChoiceFilter(
        queryset=get_foi_laws(), widget=CustomLinkWidget, label=_("by Law")
    )
    type = ChoiceFilter(
        choices=get_types_for_choices, widget=CustomLinkWidget, label=_("by Type")
    )
    date = ChoiceFilter(
        choices=get_years_for_choices,
        lookup_expr="year",
        widget=CustomLinkWidget,
        label=_("by Year"),
    )

    class Meta:
        model = LegalDecision
        fields = [
            "foi_court",
            "type",
            "date",
            "reference",
            "foi_law",
            "tags",
            "translations__abstract",
        ]

    def get_filter_url(self, clear_field=None):
        data = self.data.copy()
        if "page" in data:
            del data["page"]
        if clear_field:
            del data[clear_field]
        try:
            url = data.urlencode()
        except AttributeError:
            url = urlencode(data)
        return mark_safe("%(query_string)s" % {"query_string": url})

    def get_selected_filters(self):
        res = []
        for key in self.data.keys():
            if not key == "page":
                filter = self.filters.get(key)
                func = filter.extra.get("choices")
                if func:
                    choices = func()
                    for choice in choices:
                        if self.data.get(key) == str(choice[0]):
                            res.append(
                                (
                                    choice[1].split(" ")[0],
                                    self.get_filter_url(clear_field=key),
                                )
                            )
                elif filter.extra.get("queryset"):
                    qs = filter.extra.get("queryset")
                    if self.data.get(key):
                        element = qs.get(id=self.data.get(key))
                        res.append((str(element), self.get_filter_url(clear_field=key)))
        return res
