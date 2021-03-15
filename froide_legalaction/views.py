from django.shortcuts import render, get_object_or_404, Http404, redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from froide.foirequest.models import FoiRequest
from froide.foirequest.auth import can_write_foirequest
from .forms import LegalActionRequestForm


def _get_embed_info(request):
    is_embed = request.GET.get('embed', False)
    base_template = ("froide_legalaction/base_embed.html" if is_embed else
                     "froide_legalaction/base.html")
    return is_embed, base_template


def request_form_page(request, pk=None):
    foirequest = None

    is_embed, base_template = _get_embed_info(request)
    status = 200

    if pk is not None:
        if not request.user.is_authenticated:
            raise Http404
        foirequest = get_object_or_404(
            FoiRequest, pk=int(pk)
        )
        if not can_write_foirequest(foirequest, request):
            raise Http404

    if request.method == 'POST':
        form = LegalActionRequestForm(request.POST, request.FILES,
                                      foirequest=foirequest)
        if form.is_valid():
            form.save()
            messages.add_message(
                request, messages.SUCCESS,
                _('We have received your submission and we will review it. Thank you!')
            )
            if foirequest is None:
                url = reverse('legalaction-thanks')
                return redirect(url + ('?embed=1' if is_embed else ''))
            else:
                return redirect(foirequest)
        else:
            status = 400
            messages.add_message(
                request, messages.WARNING,
                _('Please check for errors in your form.')
            )

    else:
        form = LegalActionRequestForm(foirequest=foirequest)

    return render(request, 'froide_legalaction/form.html', {
        'form': form,
        'base_template': base_template
    }, status=status)


def thanks_page(request):
    is_embed, base_template = _get_embed_info(request)
    return render(request, 'froide_legalaction/thanks.html', {
        'base_template': base_template
    })
