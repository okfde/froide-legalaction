from django.shortcuts import render, get_object_or_404, Http404, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic.edit import UpdateView
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator

from legal_advice_builder.views import FormWizardView
from legal_advice_builder.forms import RenderedDocumentForm
from legal_advice_builder.models import LawCase, Answer

from froide.foirequest.models import FoiRequest
from froide.foirequest.auth import can_write_foirequest
from froide.publicbody.models import Classification, PublicBody
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
            messages[key] = 'am {} von {}: {}'.format(
                message.timestamp.date(),
                message.sender_name,
                message.subject)
            for attachment in message.foiattachment_set.all():
                if not attachment.is_irrelevant and not attachment.is_redacted:
                    attachment_key = 'attachment_{}'.format(attachment.id)
                    messages[attachment_key] = attachment.name
        return messages

    def get_public_body_type(self, public_body):
        return public_body.jurisdiction.slug

    def get_classification(self):
        return Classification.objects.get(
            slug='verwaltungsgerichte')

    def get_court_for_public_body(self, public_body):
        geo = public_body.geo
        if geo:
            classification = self.get_classification()
            court_type_ids = classification.get_children().values_list(
                'id', flat=True)
            court = PublicBody.objects.filter(
                regions__geom__intersects=geo,
                classification__id__in=court_type_ids).first()
            if court:
                return court.name, court.address
        return '', ''

    def get_initial_dict(self):
        foi_request = self.get_foirequest()
        public_body = foi_request.public_body
        court_name, court_address = self.get_court_for_public_body(public_body)
        return {
            'pruefen': {
                'antragstellung': {
                    'initial': foi_request.first_message.date().strftime(
                        "%Y-%m-%d")
                }
            },
            'person': {
                'behoerde_name': {
                    'initial': public_body.name
                },
                'behoerde_adresse': {
                    'initial': public_body.address
                },
                'behoerde_type': {
                    'initial': self.get_public_body_type(public_body),
                },
                'gericht_name': {
                    'initial': court_name
                },
                'gericht_adresse': {
                    'initial': court_address
                },
                'anfrage_text': {
                    'initial': foi_request.messages[0].plaintext
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

    def save_answers(self, answers):
        answer = super().save_answers(answers)
        foi_request = self.get_foirequest()
        answer.extra_info = {
            'foi_request': foi_request.id
        }
        answer.save()
        Answer.objects.filter(
            creator=self.request.user,
            extra_info__foi_request=foi_request.id
        ).exclude(id=answer.id).delete()
        return answer


@method_decorator(staff_member_required, name='dispatch')
class KlageautomatAnswerEditView(UpdateView):
    model = Answer
    form_class = RenderedDocumentForm

    def get_object(self):
        foi_request = self.get_foirequest()
        return Answer.objects.filter(
            creator=self.request.user,
            extra_info__foi_request=foi_request.id).last()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'foi_request': self.get_foirequest()
        })
        return context

    def get_foirequest(self):
        pk = self.kwargs.get('pk')
        return FoiRequest.objects.get(pk=pk)

    def get_success_url(self):
        return self.request.path
