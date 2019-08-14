from django.conf.urls import url
from django.utils.translation import pgettext_lazy
from django.views.decorators.clickjacking import xframe_options_exempt


from .views import request_form_page, thanks_page

urlpatterns = [
    url(r'^$', xframe_options_exempt(request_form_page),
        name='legalaction-index'),
    url(pgettext_lazy('url part', r'^thanks/$'),
        xframe_options_exempt(thanks_page), name='legalaction-thanks'),
    url(pgettext_lazy('url part', r'^request/(?P<pk>\d+)/$'),
        request_form_page, name='legalaction-request_form'),
]
