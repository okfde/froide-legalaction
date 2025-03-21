from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, FormView
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView

from legal_advice_builder.models import Answer
from legal_advice_builder.views import (
    FormWizardView,
    HTMLDownloadView,
    PdfDownloadView,
    WordDownloadView,
)

from froide.foirequest.auth import can_write_foirequest
from froide.foirequest.models import FoiRequest
from froide.publicbody.models import Classification, PublicBody

from .filters import LegalDecisionFilterSet
from .forms import (
    KlageautomatApprovalForm,
    KlageautomatRenderedDocumentForm,
    LegalActionRequestForm,
    LegalDecisionCreateForm,
    LegalDecisionUpdateForm,
)
from .mixins import KlageautomatMixin
from .models import Instance, LegalDecision
from .utils import make_lawsuit_event_calendar


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


class KlageautomatInfoPage(KlageautomatMixin, FormView):
    template_name = "legal_advice_builder/klageautomat_info.html"
    form_class = KlageautomatApprovalForm

    def get_success_url(self):
        return reverse("klageautomat-form_wizard", args=[self.get_foirequest().id])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({"foi_request": self.get_foirequest()})
        return ctx


class KlageAutomatWizard(KlageautomatMixin, FormWizardView):
    document_form_class = KlageautomatRenderedDocumentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"foi_request": self.get_foirequest()})
        if self.answer:
            context.update(
                {
                    "help_message": self.get_help_message(),
                    "attachments": self.get_attachment_list(self.answer),
                }
            )
        return context

    def get_help_message(self, answer=None):
        if not answer:
            answer = self.answer
        questionaiere = self.get_lawcase().questionaire_set.last()
        return questionaiere.success_message_with_data(answer)

    def get_public_body_type(self, public_body):
        if public_body and public_body.jurisdiction:
            return public_body.jurisdiction.slug
        return ""

    def get_classification(self):
        return Classification.objects.get(slug="verwaltungsgericht")

    def get_court_for_public_body(self, public_body):
        if public_body:
            geo = public_body.geo
            if geo:
                vg_classification = self.get_classification()
                court = PublicBody.objects.filter(
                    classification=vg_classification, regions__geom__intersects=geo
                ).first()
                if court:
                    return court.name, court.address
        return "", ""

    def get_publicbody(self):
        public_body = self.get_foirequest().public_body
        answer_pb = self.get_answer_for_question("behoerde_name")
        if answer_pb and not answer_pb == public_body.name:
            return ""
        return public_body

    def get_initial_dict(self):
        public_body = self.get_publicbody()
        foi_request = self.get_foirequest()
        court_name, court_address = self.get_court_for_public_body(public_body)
        return {
            "pruefen": {
                "antragstellung": {
                    "initial": foi_request.first_message.date().strftime("%Y-%m-%d")
                }
            },
            "person": {
                "behoerde_name": {"initial": public_body.name if public_body else ""},
                "behoerde_adresse": {
                    "initial": public_body.address if public_body else ""
                },
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
                    "attachments": self.get_attachment_list(answer),
                }
            )
        return self.render_to_response(context)


class KlageautomatAnswerEditView(KlageautomatMixin, UpdateView):
    model = Answer
    form_class = KlageautomatRenderedDocumentForm

    def get_object(self):
        foi_request = self.get_foirequest()
        return Answer.objects.filter(
            law_case=self.get_lawcase(),
            external_id=foi_request.id,
        ).last()

    def get_answer_from_list(self, question_id):
        for answer in self.get_object().answers:
            if answer.get("question") == question_id:
                return answer

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
                "attachments": self.get_attachment_list(self.get_object()),
            }
        )
        return context

    def get_success_url(self):
        return self.request.path


class KlageautomatAnswerPDFDownloadView(KlageautomatMixin, PdfDownloadView):
    def get_answer(self):
        foi_request = self.get_foirequest()
        return Answer.objects.filter(
            law_case=self.get_lawcase(),
            external_id=foi_request.id,
        ).last()


class KlageautomatAnswerWordDownloadView(KlageautomatMixin, WordDownloadView):
    def get_answer(self):
        foi_request = self.get_foirequest()
        return Answer.objects.filter(
            law_case=self.get_lawcase(),
            external_id=foi_request.id,
        ).last()


class KlageautomatAnswerHTMLDownloadView(KlageautomatMixin, HTMLDownloadView):
    def get_answer(self):
        foi_request = self.get_foirequest()
        return Answer.objects.filter(
            law_case=self.get_lawcase(),
            external_id=foi_request.id,
        ).last()


class LegalDecisionListView(ListView):
    model = LegalDecision
    paginate_by = 10
    template_name = "froide_legalaction/legaldecision/list.html"

    def get_filter_queryset(self):
        return LegalDecision.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = LegalDecisionFilterSet(
            self.request.GET, queryset=self.get_filter_queryset(), request=self.request
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


class LegalDecisionIncompleteListView(PermissionRequiredMixin, LegalDecisionListView):
    permission_required = "froide_legalaction.change_legaldecision"

    def get_filter_queryset(self):
        incomplete = LegalDecision.objects.all_incomplete()
        if self.request.GET.get("ids"):
            id_list = self.request.GET.get("ids").split(",")
            return incomplete.filter(id__in=id_list)
        return incomplete

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"show_incomplete_fields": True})
        return context


class LegalDecisionCreateView(PermissionRequiredMixin, FormView):
    permission_required = "froide_legalaction.add_legaldecision"
    form_class = LegalDecisionCreateForm
    template_name = "froide_legalaction/legaldecision/create.html"

    def get_success_url(self):
        return reverse("legal-decision-list-incomplete")

    def form_valid(self, form):
        self.object = form.save(request=self.request)
        return redirect(self.object)


class LegalDecisionDetailView(DetailView):
    model = LegalDecision
    template_name = "froide_legalaction/legaldecision/detail.html"


class LegalDecisionIncompleteUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "froide_legalaction.change_legaldecision"
    form_class = LegalDecisionUpdateForm
    model = LegalDecision
    template_name = "froide_legalaction/legaldecision/detail.html"

    def get_next_id(self):
        ids = self.request.GET.get("ids")
        if ids:
            id_list = ids.split(",")
            try:
                index = id_list.index(str(self.object.id))
                return id_list[index + 1]
            except (ValueError, IndexError):
                return None
        next = (
            LegalDecision.objects.all_incomplete()
            .filter(id__gt=self.object.id)
            .order_by("id")
            .first()
        )
        if next:
            return next.id

    def get_success_url(self):
        return reverse("legaldecision:list-incomplete")

    def form_valid(self, form):
        self.object = form.save()
        next_id = self.get_next_id()
        if next_id and "next" in self.request.POST:
            ids = self.request.GET.get("ids")
            url = reverse(
                "legaldecision:incomplete-update", kwargs={"pk": int(next_id)}
            )
            return HttpResponseRedirect("{}?ids={}".format(url, ids))
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.get_next_id():
            context.update({"has_next": True})
        return context


def lawsuit_event_calendar(request):
    instances = Instance.objects.get_last_three_months()

    cal = make_lawsuit_event_calendar(instances)

    response = HttpResponse(cal.to_ical(), content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = "attachment; filename=lawsuit-events.ics"
    return response
