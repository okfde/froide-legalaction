from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse, reverse_lazy
from django.utils import formats, timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from legal_advice_builder.forms import RenderedDocumentForm
from parler.forms import TranslatableModelForm

from froide.document.models import DocumentCollection
from froide.foirequest.models import FoiMessage
from froide.foirequest.validators import validate_upload_document
from froide.helper.date_utils import calculate_month_range_de
from froide.helper.widgets import (
    AutocompleteMultiWidget,
    AutocompleteWidget,
    BootstrapCheckboxInput,
)
from froide.publicbody.models import Classification, FoiLaw, PublicBody
from froide.publicbody.widgets import PublicBodySelect

from .models import LegalDecision, Proposal, ProposalDocument


class PhoneNumberInput(forms.widgets.Input):
    input_type = "tel"


class FoiMessageChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        """
        This method is used to convert objects into strings; it's used to
        generate the labels for the choices presented by this object.
        Subclasses can override this method to customize the display
        of the choices.
        """
        date = formats.date_format(obj.timestamp, "SHORT_DATETIME_FORMAT")
        if obj.is_postal:
            date = formats.date_format(obj.timestamp, "SHORT_DATE_FORMAT")
        if obj.is_response:
            return _("{date} from {publicbody}: {subject}").format(
                date=date, subject=obj.subject, publicbody=obj.sender_public_body
            )
        return "{date}: {subject}".format(date=date, subject=obj.subject)


class LegalActionUserForm(forms.Form):
    first_name = forms.CharField(
        max_length=30,
        label=_("First name"),
        widget=forms.TextInput(
            attrs={"placeholder": _("First Name"), "class": "form-control"}
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        label=_("Last name"),
        widget=forms.TextInput(
            attrs={"placeholder": _("Last Name"), "class": "form-control"}
        ),
    )
    address = forms.CharField(
        max_length=300,
        required=False,
        label=_("Mailing Address"),
        help_text=_("Your real address is required."),
        widget=forms.Textarea(
            attrs={
                "rows": "3",
                "class": "form-control",
                "placeholder": _("Street, Post Code, City"),
            }
        ),
    )
    email = forms.EmailField(
        label=_("Email address"),
        max_length=75,
        help_text=_("Required"),
        widget=forms.EmailInput(
            attrs={"placeholder": _("mail@ddress.net"), "class": "form-control"}
        ),
    )
    phone = forms.CharField(
        label=_("Phone number"),
        max_length=75,
        help_text=_("Required. We will need to talk you."),
        widget=PhoneNumberInput(attrs={"class": "form-control"}),
    )

    publicbody = forms.ModelChoiceField(
        label=_("Public body"),
        queryset=PublicBody.objects.all(),
        widget=PublicBodySelect,
    )

    terms = forms.BooleanField(
        label=format_html(
            _(
                "You agree "
                'to our <a href="'
                '/datenschutzerklaerung/"'
                ' target="_blank">Privacy Terms</a>'
            )
        ),
        required=True,
        widget=BootstrapCheckboxInput,
    )


class LegalActionRequestForm(LegalActionUserForm):
    description = forms.CharField(
        label=_("Anything we should know?"),
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        self.foirequest = kwargs.pop("foirequest", None)
        super().__init__(*args, **kwargs)

        if self.foirequest is not None:
            user = self.foirequest.user
            self.fields["publicbody"].widget = forms.HiddenInput()
            self.fields["publicbody"].initial = self.foirequest.public_body
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["email"].initial = user.email
            self.fields["address"].initial = user.address
            self.foimessage_qs = FoiMessage.objects.filter(request=self.foirequest)
            self.first_foimessage = self.foimessage_qs[0]

        custom_fields = []
        for kind, kind_detail in ProposalDocument.DOCUMENT_KINDS:
            if self.foirequest is None:
                custom_fields.extend(self.add_document_fields(kind, kind_detail))
            else:
                custom_fields.extend(self.add_foimessage_fields(kind, kind_detail))

        self.order_fields(
            ["first_name", "last_name", "address", "email", "phone", "publicbody"]
            + custom_fields
            + ["legal_date", "description"]
        )

    def add_foimessage_fields(self, kind, kind_detail):
        required = kind_detail["required"]
        qs, mes = self.foimessage_qs, self.first_foimessage
        init = kind_detail["initial"]
        self.fields["foimessage_%s" % kind] = FoiMessageChoiceField(
            empty_label=None,
            help_text=kind_detail["help_text"],
            queryset=kind_detail["select"](qs, mes),
            initial=init(qs, mes) if init else None,
            label=_("Document for {}").format(kind_detail["label"]),
            widget=(
                forms.HiddenInput if kind_detail.get("hidden") else forms.RadioSelect
            ),
            required=required,
        )
        return ["foimessage_%s" % kind]

    def add_document_fields(self, kind, kind_detail):
        required = kind_detail["required"]
        self.fields["date_%s" % kind] = forms.DateField(
            label=_("Date of {}").format(kind_detail["label"]),
            validators=[validators.MaxValueValidator(timezone.now().date())],
            widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            required=required,
        )
        self.fields["document_%s" % kind] = forms.FileField(
            label=_("Upload document for {}").format(kind_detail["label"]),
            help_text=kind_detail["help_text_upload"],
            validators=[validate_upload_document],
            widget=forms.FileInput(attrs={"class": "form-control"}),
            required=required,
        )
        return ["date_%s" % kind, "document_%s" % kind]

    def clean(self):
        cleaned_data = self.cleaned_data

        if self.foirequest is None:
            return

        if Proposal.objects.filter(foirequest=self.foirequest).exists():
            raise forms.ValidationError(
                _("You already submitted a suit " "proposal for this request.")
            )

        DK = ProposalDocument.DOCUMENT_KINDS
        try:
            messages = []
            for kind, _kind_detail in DK:
                if cleaned_data["foimessage_%s" % kind]:
                    messages.append(cleaned_data["foimessage_%s" % kind])
            message_set = set(messages)
        except KeyError:
            raise forms.ValidationError(
                _("You have not submitted enough document kinds.")
            )
        if len(message_set) != len(messages):
            raise forms.ValidationError(
                _(
                    "You have submitted the same message for "
                    "different document kinds."
                )
            )

    def save(self):
        cleaned_data = self.cleaned_data

        proposal = None
        with transaction.atomic():
            proposal = Proposal.objects.create(
                first_name=cleaned_data["first_name"],
                last_name=cleaned_data["last_name"],
                address=cleaned_data["address"],
                email=cleaned_data["email"],
                phone=cleaned_data["phone"],
                foirequest=self.foirequest,
                publicbody=cleaned_data["publicbody"],
                description=cleaned_data["description"],
            )
            last_date = None
            for kind, _kind_detail in ProposalDocument.DOCUMENT_KINDS:
                pd = None
                if self.foirequest is None:
                    date = None
                    document = None
                    if "date_%s" % kind in cleaned_data:
                        date = cleaned_data["date_%s" % kind]
                    if "document_%s" % kind in cleaned_data:
                        document = cleaned_data["document_%s" % kind]
                    if date and document:
                        pd = ProposalDocument(proposal=proposal, kind=kind)
                        pd.date = date
                        pd.document = document
                else:
                    if cleaned_data["foimessage_%s" % kind]:
                        pd = ProposalDocument(proposal=proposal, kind=kind)
                        fm = cleaned_data["foimessage_%s" % kind]
                        pd.foimessage = fm
                        pd.date = fm.timestamp.date()
                if pd:
                    if kind == "final_rejection":
                        last_date = pd.date
                    pd.save()
            if last_date:
                proposal.legal_date = calculate_month_range_de(last_date)
            proposal.save()
        return proposal


class KlageautomatApprovalForm(forms.Form):
    read_faqs = forms.BooleanField(
        required=True,
        label=format_html(
            'Ich habe die <a target="_blank" href="/hilfe/tipps-fur-den-anfrageprozess/klagen/untatigkeitsklage/">Informationen zur Untätigkeitsklage</a> gelesen.'
        ),
    )
    all_files_uploaded = forms.BooleanField(
        required=True,
        label="Ich habe alle Informationen zu meiner Anfrage auf FragDenStaat eingetragen.",
    )
    no_payment_of_costs = forms.BooleanField(
        required=True,
        label=format_html(
            'Ich habe verstanden, dass FragDenStaat für evtl. <a target="_blank" href="/hilfe/tipps-fur-den-anfrageprozess/klagen/untatigkeitsklage/kosten/">anfallende Kosten</a> nach dem Einreichen einer Klage nicht aufkommt.'
        ),
    )


class KlageautomatRenderedDocumentForm(RenderedDocumentForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rendered_document"].label = "Ihr Klageentwurf"


class FoiCourtFieldMixin:
    def get_court_queryset(self):
        court = Classification.objects.filter(name="Gericht").first()
        descendants = court.get_descendants().values_list("id", flat=True)
        court_ids = [court.id] + list(descendants)
        return PublicBody.objects.filter(classification__id__in=court_ids)

    def set_foi_court_widget_url(self):
        court = Classification.objects.filter(name="Gericht").first()
        url = self.fields["foi_court"].widget.autocomplete_url
        self.fields[
            "foi_court"
        ].widget.autocomplete_url = "{}?classification={}".format(url, court.id)


class LegalDecisionCreateForm(forms.Form, FoiCourtFieldMixin):
    document_collection = forms.ModelChoiceField(
        queryset=DocumentCollection.objects.none()
    )
    foi_court = forms.ModelChoiceField(
        queryset=PublicBody.objects.none(),
        label=_("Court"),
        widget=AutocompleteWidget(
            autocomplete_url=reverse_lazy("api:publicbody-autocomplete"),
            model=PublicBody,
            allow_new=False,
        ),
        required=False,
    )
    decision_type = forms.ChoiceField(choices=LegalDecision.LegalDecisionTypes.choices)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)
        qs = DocumentCollection.objects.get_authenticated_queryset(
            self.request
        ).order_by("-created_at")
        self.fields["document_collection"].queryset = qs
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
        self.set_foi_court_widget_url()
        self.fields["foi_court"].queryset = self.get_court_queryset()


class LegalDecisionUpdateForm(TranslatableModelForm, FoiCourtFieldMixin):
    foi_laws = forms.ModelMultipleChoiceField(
        queryset=FoiLaw.objects.all(),
        label=_("Laws"),
        widget=AutocompleteMultiWidget(
            autocomplete_url=reverse_lazy("api:law-autocomplete"),
            model=FoiLaw,
            allow_new=False,
        ),
        required=False,
    )
    foi_court = forms.ModelChoiceField(
        queryset=PublicBody.objects.none(),
        label=_("Court"),
        widget=AutocompleteWidget(
            autocomplete_url=reverse_lazy("api:publicbody-autocomplete"),
            model=PublicBody,
            allow_new=False,
        ),
        required=False,
    )

    class Meta:
        model = LegalDecision
        fields = [
            "reference",
            "decision_type",
            "date",
            "court",
            "foi_court",
            "foi_laws",
            "abstract",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
        url = self.fields["foi_laws"].widget.autocomplete_url
        self.fields["foi_laws"].widget.autocomplete_url = "{}?meta=False".format(url)

        self.set_foi_court_widget_url()
        self.fields["foi_court"].queryset = self.get_court_queryset()

    def clean_reference(self):
        reference = self.cleaned_data.get("reference")
        legal_decision = (
            LegalDecision.objects.filter(reference=reference)
            .exclude(id=self.instance.id)
            .first()
        )
        if legal_decision:
            url = reverse(
                "legal-decision-incomplete-update", kwargs={"pk": legal_decision.id}
            )
            message = _(
                "This reference already exists <a href='{}' target='_blank'>here.</a>"
            ).format(url)
            raise ValidationError(format_html(message))
        return reference
