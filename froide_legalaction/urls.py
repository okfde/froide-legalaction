from django.conf.urls import url
from django.utils.translation import pgettext_lazy
from django.views.decorators.clickjacking import xframe_options_exempt


from .views import (request_form_page, thanks_page,
                    klageautomat, KlageAutomatWizard)

urlpatterns = [
    url(r'^$', xframe_options_exempt(request_form_page),
        name='legalaction-index'),
    url(pgettext_lazy('url part', r'^thanks/$'),
        xframe_options_exempt(thanks_page), name='legalaction-thanks'),
    url(pgettext_lazy('url part', r'^request/(?P<pk>\d+)/$'),
        request_form_page, name='legalaction-request_form'),
    url(pgettext_lazy('url part', r'^klageautomat/$'),
        klageautomat, name='klageautomat-index'),
    url(pgettext_lazy('url part', r'^klageautomat/request/(?P<pk>\d+)/$'),
        KlageAutomatWizard.as_view(), name='klageautomat-form_wizard'),
]
