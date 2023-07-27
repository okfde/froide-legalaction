from django.urls import path
from django.utils.translation import pgettext_lazy

from ..views import (
    LegalDecisionCreateView,
    LegalDecisionDetailView,
    LegalDecisionIncompleteListView,
    LegalDecisionIncompleteUpdateView,
    LegalDecisionListView,
)

app_name = "legaldecision"

urlpatterns = [
    path(
        "",
        LegalDecisionListView.as_view(),
        name="list",
    ),
    path(
        pgettext_lazy("url part", "incomplete/"),
        LegalDecisionIncompleteListView.as_view(),
        name="list-incomplete",
    ),
    path(
        pgettext_lazy("url part", "incomplete/<int:pk>/"),
        LegalDecisionIncompleteUpdateView.as_view(),
        name="incomplete-update",
    ),
    path(
        pgettext_lazy("url part", "create/"),
        LegalDecisionCreateView.as_view(),
        name="create",
    ),
    path(
        pgettext_lazy("url part", "<int:pk>/"),
        LegalDecisionDetailView.as_view(),
        name="detail",
    ),
    path(
        pgettext_lazy("url part", "<slug:slug>/"),
        LegalDecisionDetailView.as_view(),
        name="detail",
    ),
]
