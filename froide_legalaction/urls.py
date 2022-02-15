from django.conf.urls import url
from django.urls import include, path
from django.utils.translation import pgettext_lazy
from django.views.decorators.clickjacking import xframe_options_exempt

from .views import (
    KlageautomatAnswerDownloadView,
    KlageautomatAnswerEditView,
    KlageautomatInfoPage,
    KlageAutomatWizard,
    LegalDecisionDetailView,
    LegalDecisionListView,
    request_form_page,
    thanks_page,
)

urlpatterns = [
    url(r"^$", xframe_options_exempt(request_form_page), name="legalaction-index"),
    url(
        pgettext_lazy("url part", r"^thanks/$"),
        xframe_options_exempt(thanks_page),
        name="legalaction-thanks",
    ),
    url(
        pgettext_lazy("url part", r"^request/(?P<pk>\d+)/$"),
        request_form_page,
        name="legalaction-request_form",
    ),
    url(
        pgettext_lazy("url part", r"^klageautomat/info/request/(?P<pk>\d+)/$"),
        KlageautomatInfoPage.as_view(),
        name="klageautomat-info",
    ),
    url(
        pgettext_lazy("url part", r"^klageautomat/request/(?P<pk>\d+)/$"),
        KlageAutomatWizard.as_view(),
        name="klageautomat-form_wizard",
    ),
    url(
        pgettext_lazy("url part", r"^klageautomat/request/(?P<pk>\d+)/answer/$"),
        KlageautomatAnswerEditView.as_view(),
        name="klageautomat-edit-answer",
    ),
    url(
        pgettext_lazy(
            "url part", r"^klageautomat/request/(?P<pk>\d+)/answer/download$"
        ),
        KlageautomatAnswerDownloadView.as_view(),
        name="klageautomat-download-answer",
    ),
    path("klageautomat/admin/", include("legal_advice_builder.urls")),
    url(
        pgettext_lazy("url part", r"^legal-decisions/$"),
        LegalDecisionListView.as_view(),
        name="legal-decision-list",
    ),
    url(
        pgettext_lazy("url part", r"^legal-decisions/(?P<pk>\d+)/$"),
        LegalDecisionDetailView.as_view(),
        name="legal-decision-detail",
    ),
]
