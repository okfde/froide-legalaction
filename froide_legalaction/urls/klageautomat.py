from django.urls import include, path
from django.utils.translation import pgettext_lazy

from ..views import (
    KlageautomatAnswerEditView,
    KlageautomatAnswerHTMLDownloadView,
    KlageautomatAnswerPDFDownloadView,
    KlageautomatAnswerWordDownloadView,
    KlageautomatInfoPage,
    KlageAutomatWizard,
)

urlpatterns = [
    path(
        pgettext_lazy("url part", "klageautomat/info/request/<int:pk>/"),
        KlageautomatInfoPage.as_view(),
        name="klageautomat-info",
    ),
    path(
        pgettext_lazy("url part", "klageautomat/request/<int:pk>/"),
        KlageAutomatWizard.as_view(),
        name="klageautomat-form_wizard",
    ),
    path(
        pgettext_lazy("url part", "klageautomat/request/<int:pk>/answer/"),
        KlageautomatAnswerEditView.as_view(),
        name="klageautomat-edit-answer",
    ),
    path(
        pgettext_lazy("url part", "klageautomat/request/<int:pk>/answer/pdf-download/"),
        KlageautomatAnswerPDFDownloadView.as_view(),
        name="klageautomat-pdf-download-answer",
    ),
    path(
        pgettext_lazy(
            "url part", "klageautomat/request/<int:pk>/answer/word-download/"
        ),
        KlageautomatAnswerWordDownloadView.as_view(),
        name="klageautomat-word-download-answer",
    ),
    path(
        pgettext_lazy(
            "url part", "klageautomat/request/<int:pk>/answer/html-download/"
        ),
        KlageautomatAnswerHTMLDownloadView.as_view(),
        name="klageautomat-html-download-answer",
    ),
    path("klageautomat/admin/", include("legal_advice_builder.urls")),
]
