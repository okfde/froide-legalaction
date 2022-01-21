from datetime import timedelta

from django.db.models import Exists, OuterRef
from django.shortcuts import render, get_object_or_404, Http404, redirect
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.views.generic import TemplateView, FormView, DetailView
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator

from legal_advice_builder.views import FormWizardView, PdfDownloadView
from legal_advice_builder.forms import RenderedDocumentForm
from legal_advice_builder.models import LawCase, Answer

from froide.foirequest.models import FoiRequest, FoiMessage
from froide.foirequest.models.request import Status
from froide.foirequest.auth import can_write_foirequest
from froide.publicbody.models import Classification, PublicBody

from .filters import LegalDecisionFilterSet
from .forms import LegalActionRequestForm, KlageautomatApprovalForm
from .models import LegalDecision


def _get_embed_info(request):
    is_embed = request.GET.get("embed", False)
    base_template = (
        "froide_legalaction/base_embed.html"
        if is_embed
        else "froide_legalaction/base.html"
    )
    return is_embed, base_template


def request_form_page(request, pk=None):
    foirequest = None

    is_embed, base_template = _get_embed_info(request)
    status = 200

    if pk is not None:
        if not request.user.is_authenticated:
            raise Http404
        foirequest = get_object_or_404(FoiRequest, pk=int(pk))
        if not can_write_foirequest(foirequest, request):
            raise Http404

    if request.method == "POST":
        form = LegalActionRequestForm(
            request.POST, request.FILES, foirequest=foirequest
        )
        if form.is_valid():
            form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                _("We have received your submission and we will review it. Thank you!"),
            )
            if foirequest is None:
                url = reverse("legalaction-thanks")
                return redirect(url + ("?embed=1" if is_embed else ""))
            else:
                return redirect(foirequest)
        else:
            status = 400
            messages.add_message(
                request, messages.WARNING, _("Please check for errors in your form.")
            )

    else:
        form = LegalActionRequestForm(foirequest=foirequest)

    return render(
        request,
        "froide_legalaction/form.html",
        {"form": form, "base_template": base_template},
        status=status,
    )


def thanks_page(request):
    is_embed, base_template = _get_embed_info(request)
    return render(
        request, "froide_legalaction/thanks.html", {"base_template": base_template}
    )


@method_decorator(staff_member_required, name="dispatch")
class KlageautomatFoirequestList(TemplateView):
    template_name = "legal_advice_builder/foirequest_list.html"

    def get_lawcase(self):
        return LawCase.objects.all().first()

    def get_foi_requests(self):

        subquery = Answer.objects.filter(
            law_case=self.get_lawcase(), external_id=OuterRef("pk")
        )

        now = timezone.now().date()

        three_months_ago = now - timedelta(days=30 * 3)

        message_query = FoiMessage.objects.filter(
            request=OuterRef("pk"), timestamp__gte=three_months_ago
        )

        search = self.request.GET.get("Search")
        all_requests = self.request.GET.get("allRequests")
        only_candidates = self.request.GET.get("onlyCandidates")
        page_number = self.request.GET.get("page")
        filter = {
            "user": self.request.user,
            "status__in": [Status.AWAITING_RESPONSE, Status.ASLEEP],
        }
        if search or all_requests or only_candidates:
            if not search == "":
                filter["title__contains"] = search
            if all_requests and all_requests == "on":
                del filter["user"]
            if only_candidates and only_candidates == "on":
                filter["needs_waiting"] = False
        foi_requests = (
            FoiRequest.objects.annotate(answer_exists=Exists(subquery))
            .annotate(needs_waiting=Exists(message_query))
            .filter(**filter)
        )
        paginator = Paginator(foi_requests, 10)
        return paginator.get_page(page_number)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_obj": self.get_foi_requests()})
        return context


@method_decorator(staff_member_required, name="dispatch")
class KlageautomatInfoPage(FormView):
    template_name = "legal_advice_builder/klageautomat_info.html"
    form_class = KlageautomatApprovalForm

    def get_foirequest(self):
        pk = self.kwargs.get("pk")
        return FoiRequest.objects.get(pk=pk)

    def get_success_url(self):
        return reverse("klageautomat-form_wizard", args=[self.get_foirequest().id])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({"foi_request": self.get_foirequest()})
        return ctx


@method_decorator(staff_member_required, name="dispatch")
class KlageAutomatWizard(FormWizardView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"foi_request": self.get_foirequest()})
        if self.answer:
            context.update({"help_message": self.get_help_message()})
        return context

    def get_help_message(self, answer=None):
        if not answer:
            answer = self.answer
        questionaiere = self.get_lawcase().questionaire_set.last()
        return questionaiere.success_message_with_data(answer)

    def get_lawcase(self):
        return LawCase.objects.all().first()

    def get_foirequest(self):
        pk = self.kwargs.get("pk")
        return FoiRequest.objects.get(pk=pk)

    def get_public_body_type(self, public_body):
        return public_body.jurisdiction.slug

    def get_classification(self):
        return Classification.objects.get(slug="verwaltungsgericht")

    def get_court_for_public_body(self, public_body):
        geo = public_body.geo
        if geo:
            vg_classification = self.get_classification()
            court = PublicBody.objects.filter(
                classification=vg_classification, regions__geom__intersects=geo
            ).first()
            if court:
                return court.name, court.address
        return "", ""

    def get_initial_dict(self):
        foi_request = self.get_foirequest()
        public_body = foi_request.public_body
        court_name, court_address = self.get_court_for_public_body(public_body)
        return {
            "pruefen": {
                "antragstellung": {
                    "initial": foi_request.first_message.date().strftime("%Y-%m-%d")
                }
            },
            "person": {
                "behoerde_name": {"initial": public_body.name},
                "behoerde_adresse": {"initial": public_body.address},
                "behoerde_type": {
                    "initial": self.get_public_body_type(public_body),
                },
                "gericht_name": {"initial": court_name},
                "gericht_adresse": {"initial": court_address},
                "anfrage_text": {"initial": foi_request.description},
                "name": {
                    "initial": "{} {}".format(
                        foi_request.user.first_name, foi_request.user.last_name
                    )
                },
                "adresse": {"initial": foi_request.user.address},
            },
        }

    def save_answers(self, answers):
        answer = super().save_answers(answers)
        foi_request = self.get_foirequest()
        answer.external_id = foi_request.id
        answer.save()
        Answer.objects.filter(
            law_case=self.get_lawcase(),
            creator=self.request.user,
            external_id=foi_request.id,
        ).exclude(id=answer.id).delete()
        return answer

    def render_done(self, answers=None, **kwargs):
        context = self.get_template_with_context(answers)
        if self.law_case.save_answers:
            answer = self.save_answers(answers)
            form = self.get_answer_template_form(answer)
            preview = answer.rendered_document
            context.update(
                {
                    "answer_form": form,
                    "preview": preview,
                    "help_message": self.get_help_message(answer),
                }
            )
        return self.render_to_response(context)


@method_decorator(staff_member_required, name="dispatch")
class KlageautomatAnswerEditView(UpdateView):
    model = Answer
    form_class = RenderedDocumentForm

    def get_lawcase(self):
        return LawCase.objects.all().first()

    def get_object(self):
        foi_request = self.get_foirequest()
        return Answer.objects.filter(
            law_case=self.get_lawcase(),
            external_id=foi_request.id,
        ).last()

    def get_help_message(self):
        questionaiere = self.get_lawcase().questionaire_set.last()
        return questionaiere.success_message_with_data(self.object)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "foi_request": self.get_foirequest(),
                "law_case": self.get_lawcase(),
                "help_message": self.get_help_message(),
            }
        )
        return context

    def get_foirequest(self):
        pk = self.kwargs.get("pk")
        return FoiRequest.objects.get(pk=pk)

    def get_success_url(self):
        return self.request.path


@method_decorator(staff_member_required, name="dispatch")
class KlageautomatAnswerDownloadView(PdfDownloadView):
    def get_lawcase(self):
        return LawCase.objects.all().first()

    def get_foirequest(self):
        pk = self.kwargs.get("pk")
        return FoiRequest.objects.get(pk=pk)

    def get_answer(self):
        foi_request = self.get_foirequest()
        return Answer.objects.filter(
            law_case=self.get_lawcase(),
            creator=self.request.user,
            external_id=foi_request.id,
        ).last()

    def get_filename(self):
        return "{}_{}.pdf".format(self.get_lawcase(), self.get_foirequest().id)


@method_decorator(staff_member_required, name="dispatch")
class LegalDecisionListView(ListView):

    model = LegalDecision
    paginate_by = 10

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = LegalDecisionFilterSet(
            self.request.GET, queryset=LegalDecision.objects.all()
        )

        paginator = Paginator(f.qs, self.paginate_by)
        page = self.request.GET.get("page")
        paginated = paginator.get_page(page)
        ctx.update(
            {
                "filter": f,
                "result": paginated,
                "selected_filters": f.get_selected_filters(),
                "query_url": f.get_filter_url(),
            }
        )
        return ctx


@method_decorator(staff_member_required, name="dispatch")
class LegalDecisionDetailView(DetailView):

    model = LegalDecision
