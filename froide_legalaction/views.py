from django.shortcuts import render, get_object_or_404, Http404, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator

from legal_advice_builder.views import FormWizardView
from legal_advice_builder.models import LawCase

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


@staff_member_required
def klageautomat(request):
    return render(request, 'legal_advice_builder/foirequest_list.html', {})


@method_decorator(staff_member_required, name='dispatch')
class KlageAutomatWizard(FormWizardView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'foi_request': self.get_foirequest()
        })
        return context

    def get_lawcase(self):
        return LawCase.objects.all().first()

    def get_foirequest(self):
        pk = self.kwargs.get('pk')
        return FoiRequest.objects.get(pk=pk)

    def get_messages_as_options(self, foirequest):
        messages = {}
        for message in foirequest.messages:
            key = 'message_{}'.format(message.id)
            messages[key] = message
        return messages

    def get_initial_dict(self):
        foi_request = self.get_foirequest()
        return {
            'pruefen': {
                'antragstellung': {
                    'initial': foi_request.first_message.date().strftime(
                        "%Y-%m-%d")
                }
            },
            'person': {
                'behoerde_name': {
                    'initial': foi_request.public_body.name
                },
                'behoerde_adresse': {
                    'initial': foi_request.public_body.address
                },
                'anfrage_gesetz': {
                    'initial': [foi_request.law.law_type]
                },
                'anfrage_text': {
                    'initial': foi_request.messages[0].plaintext
                },
                'anfrage_datum': {
                    'initial': foi_request.first_message.date()
                },
                'anfrage_frist': {
                    'initial': foi_request.due_date.date().strftime(
                        "%Y-%m-%d"),
                },
                'name': {
                    'initial': '{} {}'.format(
                        foi_request.user.first_name,
                        foi_request.user.last_name)
                },
                'adresse': {
                    'initial': foi_request.user.address
                },
                'anhaenge': {
                    'options': self.get_messages_as_options(foi_request)
                }
            }
        }
