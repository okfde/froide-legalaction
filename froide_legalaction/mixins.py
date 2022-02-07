from django.http import Http404
from django.shortcuts import get_object_or_404

from froide.foirequest.models import FoiRequest
from legal_advice_builder.models import LawCase

from .helper.permissions.klageautomat import can_create_answer


class KlageautomatMixin:
    def dispatch(self, request, *args, **kwargs):
        foi_request = get_object_or_404(FoiRequest, pk=kwargs.get("pk"))
        if not can_create_answer(request.user, foi_request):
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_foirequest(self):
        pk = self.kwargs.get("pk")
        return FoiRequest.objects.get(pk=pk)

    def get_lawcase(self):
        return LawCase.objects.all().first()
