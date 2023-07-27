from django.urls import path
from django.utils.translation import pgettext_lazy

from ..views import request_form_page, thanks_page

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
]
