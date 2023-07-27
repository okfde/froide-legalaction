from .klageautomat import urlpatterns as klageautomat_urls
from .lawsuit import urlpatterns as lawsuit_urls

urlpatterns = [*lawsuit_urls, *klageautomat_urls]
