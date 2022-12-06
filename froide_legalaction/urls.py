from django.urls import include, path
from django.utils.translation import pgettext_lazy

from .views import (
    KlageautomatAnswerEditView,
    KlageautomatAnswerHTMLDownloadView,
    KlageautomatAnswerPDFDownloadView,
    KlageautomatAnswerWordDownloadView,
    KlageautomatInfoPage,
    KlageAutomatWizard,
    LegalDecisionCreateView,
    LegalDecisionDetailView,
    LegalDecisionIncompleteListView,
    LegalDecisionIncompleteUpdateView,
    LegalDecisionListView,
    request_form_page,
    thanks_page,
)

urlpatterns = [
    path(
        pgettext_lazy("url part", "propose/"),
        request_form_page,
        name="legalaction-index",
    ),
    path(
        pgettext_lazy("url part", "thanks/"),
        thanks_page,
        name="legalaction-thanks",
    ),
    path(
        pgettext_lazy("url part", "request/<int:pk>/"),
        request_form_page,
        name="legalaction-request_form",
    ),
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
    path(
        pgettext_lazy("url part", "legal-decisions/"),
        LegalDecisionListView.as_view(),
        name="legal-decision-list",
    ),
    path(
        pgettext_lazy("url part", "legal-decisions-incomplete/"),
        LegalDecisionIncompleteListView.as_view(),
        name="legal-decision-list-incomplete",
    ),
    path(
        pgettext_lazy("url part", "legal-decisions-incomplete/<int:pk>/"),
        LegalDecisionIncompleteUpdateView.as_view(),
        name="legal-decision-incomplete-update",
    ),
    path(
        pgettext_lazy("url part", "legal-decisions/create/"),
        LegalDecisionCreateView.as_view(),
        name="legal-decision-create",
    ),
    path(
        pgettext_lazy("url part", "legal-decisions/<int:pk>/"),
        LegalDecisionDetailView.as_view(),
        name="legal-decision-detail",
    ),
]
