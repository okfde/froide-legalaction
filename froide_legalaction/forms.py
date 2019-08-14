from django.utils.translation import ugettext_lazy as _
from django.utils import formats, timezone
from django.db import transaction
from django.utils.safestring import mark_safe
from django.core import validators
from django import forms

from froide.foirequest.models import FoiMessage
from froide.publicbody.models import PublicBody
from froide.publicbody.widgets import PublicBodySelect
from froide.helper.widgets import BootstrapCheckboxInput
from froide.helper.date_utils import calculate_month_range_de
from froide.foirequest.validators import validate_upload_document

from .models import Proposal, ProposalDocument


class PhoneNumberInput(forms.widgets.Input):
    input_type = 'tel'


class FoiMessageChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        """
        This method is used to convert objects into strings; it's used to
        generate the labels for the choices presented by this object.
        Subclasses can override this method to customize the display
        of the choices.
        """
        date = formats.date_format(obj.timestamp, 'SHORT_DATETIME_FORMAT')
        if obj.is_postal:
            date = formats.date_format(obj.timestamp, 'SHORT_DATE_FORMAT')
        if obj.is_response:
            return _('{date} from {publicbody}: {subject}').format(
                date=date, subject=obj.subject,
                publicbody=obj.sender_public_body
            )
        return '{date}: {subject}'.format(date=date, subject=obj.subject)


class LegalActionUserForm(forms.Form):
    first_name = forms.CharField(
        max_length=30,
        label=_('First name'),
        widget=forms.TextInput(attrs={
            'placeholder': _('First Name'),
            'class': 'form-control'}))
    last_name = forms.CharField(
        max_length=30,
        label=_('Last name'),
        widget=forms.TextInput(attrs={
            'placeholder': _('Last Name'),
            'class': 'form-control'}))
    address = forms.CharField(
        max_length=300,
        required=False,
        label=_('Mailing Address'),
        help_text=_('Your real address is required.'),
        widget=forms.Textarea(attrs={
            'rows': '3',
            'class': 'form-control',
            'placeholder': _('Street, Post Code, City'),
        }))
    email = forms.EmailField(
        label=_('Email address'),
        max_length=75,
        help_text=_('Required'),
        widget=forms.EmailInput(attrs={
                'placeholder': _('mail@ddress.net'),
                'class': 'form-control'
        }))
    phone = forms.CharField(
        label=_('Phone number'),
        max_length=75,
        help_text=_('Required. We will need to talk you.'),
        widget=PhoneNumberInput(attrs={
                'class': 'form-control'
        }))

    publicbody = forms.ModelChoiceField(
        label=_('Public body'),
        queryset=PublicBody.objects.all(),
        widget=PublicBodySelect
    )


class LegalActionRequestForm(LegalActionUserForm):
    description = forms.CharField(
            label=_('Anything we should know?'),
            required=False,
            widget=forms.Textarea(attrs={
                'class': 'form-control'
            }))
    terms = forms.BooleanField(
            label=mark_safe(
                _('You agree that we will share this '
                  'data with third-parties '
                  'according to our <a href="'
                  'https://www.transparenzklagen.de/datenschutzerklaerung/"'
                  ' target="_blank">Privacy Terms</a>')),
            required=True,
            widget=BootstrapCheckboxInput
    )

    def __init__(self, *args, **kwargs):
        self.foirequest = kwargs.pop('foirequest', None)
        super(LegalActionRequestForm, self).__init__(*args, **kwargs)

        if self.foirequest is not None:
            self.fields['publicbody'].widget = forms.HiddenInput()
            self.fields['publicbody'].initial = self.foirequest.public_body
            self.fields['first_name'].initial = self.foirequest.user.first_name
            self.fields['last_name'].initial = self.foirequest.user.last_name
            self.fields['email'].initial = self.foirequest.user.email
            self.fields['address'].initial = self.foirequest.user.address
            self.foimessage_qs = FoiMessage.objects.filter(
                request=self.foirequest
            )
            self.first_foimessage = self.foimessage_qs[0]

        custom_fields = []
        for kind, kind_detail in ProposalDocument.DOCUMENT_KINDS:
            if self.foirequest is None:
                custom_fields.extend(
                    self.add_document_fields(kind, kind_detail)
                )
            else:
                custom_fields.extend(
                    self.add_foimessage_fields(kind, kind_detail)
                )

        self.order_fields(
            ['first_name', 'last_name',
                'address', 'email', 'phone', 'publicbody'] +
            custom_fields +
            ['legal_date', 'description', 'terms']
        )

    def add_foimessage_fields(self, kind, kind_detail):
        qs, mes = self.foimessage_qs, self.first_foimessage
        init = kind_detail['initial']
        self.fields['foimessage_%s' % kind] = FoiMessageChoiceField(
            empty_label=None,
            help_text=kind_detail['help_text'],
            queryset=kind_detail['select'](qs, mes),
            initial=init(qs, mes) if init else None,
            label=_('Document for {}').format(kind_detail['label']),
            widget=(
                forms.HiddenInput if kind_detail.get('hidden')
                else forms.RadioSelect
            )
        )
        return ['foimessage_%s' % kind]

    def add_document_fields(self, kind, kind_detail):
        self.fields['date_%s' % kind] = forms.DateField(
            label=_('Date of {}').format(kind_detail['label']),
            validators=[validators.MaxValueValidator(timezone.now().date())],
            widget=forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            )
        )
        self.fields['document_%s' % kind] = forms.FileField(
            label=_('Upload document for {}').format(kind_detail['label']),
            help_text=kind_detail['help_text_upload'],
            validators=[validate_upload_document],
            widget=forms.FileInput(
                attrs={
                        'class': 'form-control'
                }
            )
        )
        return ['date_%s' % kind, 'document_%s' % kind]

    def clean(self):
        cleaned_data = self.cleaned_data

        if self.foirequest is None:
            return

        if Proposal.objects.filter(foirequest=self.foirequest).exists():
            raise forms.ValidationError(_('You already submitted a suit '
                                          'proposal for this request.'))

        DK = ProposalDocument.DOCUMENT_KINDS
        try:
            message_set = set(
                cleaned_data['foimessage_%s' % kind]
                for kind, kind_detail in DK
            )
        except KeyError:
            raise forms.ValidationError(
                _('You have not submitted enough document kinds.')
            )
        if len(message_set) != len(DK):
            raise forms.ValidationError(
                _('You have submitted the same message for '
                    'different document kinds.')
            )

    def save(self):
        cleaned_data = self.cleaned_data

        proposal = None
        with transaction.atomic():
            proposal = Proposal.objects.create(
                first_name=cleaned_data['first_name'],
                last_name=cleaned_data['last_name'],
                address=cleaned_data['address'],
                email=cleaned_data['email'],
                phone=cleaned_data['phone'],
                foirequest=self.foirequest,
                publicbody=cleaned_data['publicbody'],
                description=cleaned_data['description']
            )
            last_date = None
            for kind, kind_detail in ProposalDocument.DOCUMENT_KINDS:
                pd = ProposalDocument(proposal=proposal, kind=kind)
                if self.foirequest is None:
                    pd.date = cleaned_data['date_%s' % kind]
                    pd.document = cleaned_data['document_%s' % kind]
                else:
                    fm = cleaned_data['foimessage_%s' % kind]
                    pd.foimessage = fm
                    pd.date = fm.timestamp.date()
                if kind == 'final_rejection':
                    last_date = pd.date
                pd.save()
            proposal.legal_date = calculate_month_range_de(last_date)
            proposal.save()
        return proposal
