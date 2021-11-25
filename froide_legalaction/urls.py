from django.conf.urls import url
from django.urls import include
from django.urls import path
from django.utils.translation import pgettext_lazy
from django.views.decorators.clickjacking import xframe_options_exempt


from .views import (
    request_form_page,
    thanks_page,
    KlageautomatFoirequestList,
    KlageAutomatWizard,
    KlageautomatAnswerEditView,
    KlageautomatAnswerDownloadView,
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
        pgettext_lazy("url part", r"^klageautomat/$"),
        KlageautomatFoirequestList.as_view(),
        name="klageautomat-index",
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
]
