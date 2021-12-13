from django import forms
from django.db.models import Count
from django.db.models.functions import TruncYear
from django.db.models import Q
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from django_filters import FilterSet, ModelChoiceFilter, ChoiceFilter, CharFilter

from froide.publicbody.models import Classification, FoiLaw, PublicBody

from .models import LegalDecision, LegalDecisionType
from .widgets import ExcludePageParameterLinkWidget


def get_foi_courts():
    vg_classification = Classification.objects.get(slug="verwaltungsgerichte")
    children = vg_classification.get_children().values_list("id", flat=True)
    ids = list(children) + [vg_classification.id]
    return PublicBody.objects.filter(classification__id__in=ids).exclude(
        pb_legaldecisions=None
    )


def get_foi_law_types():
    foilaw_types = (
        FoiLaw.objects.exclude(foi_law_legaldecisions=None)
        .values("law_type")
        .annotate(c=Count("id"))
    )
    return [(type.get("law_type"), type.get("law_type")) for type in foilaw_types]


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
            result.append((year, year))
    return result


def get_types_for_choices():
    types = LegalDecisionType.objects.annotate(
        decision_count=Count("legaldecision")
    ).order_by("-decision_count")
    result = []
    for type in types:
        result.append((type.id, type.title))
    return result


class LegalDecisionFilterSet(FilterSet):
    quick_search = CharFilter(
        method="get_quick_search",
        label="",
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg text-center",
                "placeholder": _("Quicksearch"),
            }
        ),
        help_text="",
    )
    text_search = CharFilter(
        method="get_text_search",
        label=_("by Keyword"),
        widget=forms.TextInput(attrs={"class": "form-control"}),
        help_text=_("searches in abstract and tags"),
    )
    foi_court = ModelChoiceFilter(
        queryset=get_foi_courts(),
        widget=ExcludePageParameterLinkWidget,
        label=_("by Court"),
    )
    foi_law__law_type = ChoiceFilter(
        choices=get_foi_law_types,
        widget=ExcludePageParameterLinkWidget,
        label=_("by Law Type"),
        lookup_expr="iexact",
    )
    type = ChoiceFilter(
        choices=get_types_for_choices,
        widget=ExcludePageParameterLinkWidget,
        label=_("by Type"),
    )
    date = ChoiceFilter(
        choices=get_years_for_choices,
        lookup_expr="year",
        widget=ExcludePageParameterLinkWidget,
        label=_("by Year"),
    )

    class Meta:
        model = LegalDecision
        fields = (
            "quick_search",
            "text_search",
            "foi_law__law_type",
            "foi_court",
            "type",
            "date",
        )

    def get_quick_search(self, queryset, name, value):
        return queryset.filter(
            Q(translations__abstract__contains=value)
            | Q(translations__fulltext__contains=value)
            | Q(tags__translations__name__contains=value)
            | Q(reference__contains=value)
            | Q(type__translations__title__contains=value)
            | Q(foi_court__name__contains=value)
            | Q(foi_law__translations__name__contains=value)
        ).distinct()

    def get_text_search(self, queryset, name, value):
        return queryset.filter(
            Q(translations__abstract__contains=value)
            | Q(tags__translations__name__contains=value)
        )

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
                if filter:
                    func = filter.extra.get("choices")
                    if func:
                        choices = func()
                        for choice in choices:
                            if self.data.get(key) == str(choice[0]):
                                res.append(
                                    (
                                        choice[1],
                                        self.get_filter_url(clear_field=key),
                                    )
                                )
                    elif filter.extra.get("queryset"):
                        qs = filter.extra.get("queryset")
                        if self.data.get(key):
                            element = qs.get(id=self.data.get(key))
                            res.append(
                                (str(element), self.get_filter_url(clear_field=key))
                            )
            if key == "text_search":
                search_string = self.data.get("text_search")
                res.append((search_string, self.get_filter_url(clear_field=key)))
        return res
