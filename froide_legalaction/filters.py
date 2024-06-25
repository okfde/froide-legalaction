from django import forms
from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, F
from django.db.models.functions import TruncYear
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from django_filters import CharFilter, ChoiceFilter, FilterSet, ModelChoiceFilter

from froide.publicbody.models import FoiLaw, PublicBody

from .models import LegalDecision, LegalDecisionTag
from .widgets import ExcludePageParameterLinkWidget, FilterListWidget


def get_foi_courts():
    return PublicBody.objects.exclude(pb_legaldecisions=None)


def get_foi_law_types():
    foilaw_types = (
        FoiLaw.objects.exclude(legal_decisions=None)
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
    return LegalDecision.LegalDecisionTypes.choices


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
    tags = ModelChoiceFilter(
        queryset=LegalDecisionTag.objects.all().order_by("translations__name"),
        widget=FilterListWidget,
        label=_("by tags"),
    )

    foi_court = ModelChoiceFilter(
        queryset=get_foi_courts(),
        widget=FilterListWidget,
        label=_("by Court"),
    )
    foi_laws__law_type = ChoiceFilter(
        choices=get_foi_law_types,
        widget=ExcludePageParameterLinkWidget,
        label=_("by Law Type"),
        lookup_expr="iexact",
    )
    decision_type = ChoiceFilter(
        choices=get_types_for_choices,
        widget=ExcludePageParameterLinkWidget,
        label=_("by Type"),
    )
    date = ChoiceFilter(
        choices=get_years_for_choices,
        lookup_expr="year",
        widget=FilterListWidget,
        label=_("by Year"),
    )

    class Meta:
        model = LegalDecision
        fields = (
            "quick_search",
            "tags",
            "foi_laws__law_type",
            "foi_court",
            "decision_type",
            "date",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = kwargs.get("request")
        if request:
            self.language = request.LANGUAGE_CODE
        else:
            self.language = settings.LANGUAGE_CODE

    def get_quick_search(self, queryset, name, value):
        query_language = LegalDecision.objects.get_search_lang(self.language)
        query = SearchQuery(value, config=query_language)
        return (
            queryset.filter(translations__search_vector=query)
            .annotate(rank=SearchRank(F("translations__search_vector"), query))
            .order_by("-rank")
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

    def get_selected_choice_value(self, filter, value):
        func = filter.extra.get("choices")
        filter_name = filter.field_name
        if func:
            choices = func()
            for choice in choices:
                if value == str(choice[0]):
                    url = self.get_filter_url(clear_field=filter_name)
                    return (choice[1], url)
        return (value, "")

    def get_selected_model_choice_value(self, filter, value):
        qs = filter.extra.get("queryset")
        try:
            element = qs.get(id=value)
            filter_name = filter.field_name
            return (str(element), self.get_filter_url(clear_field=filter_name))
        except (ValueError, ObjectDoesNotExist):
            return (value, "")

    def get_selected_filters(self):
        res = []
        data = self.data.copy()
        if "page" in data:
            del data["page"]
        for key in data.keys():
            filter = self.filters.get(key)
            value = data.get(key)
            filter_type = filter.__class__.__name__
            if filter and value:
                if filter_type == "ChoiceFilter":
                    res.append(self.get_selected_choice_value(filter, value))
                elif filter_type == "ModelChoiceFilter":
                    res.append(self.get_selected_model_choice_value(filter, value))
                else:
                    res.append((value, self.get_filter_url(clear_field=key)))
        return res
