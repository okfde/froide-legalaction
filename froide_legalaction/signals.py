from django.conf import settings
from django.core.mail import mail_managers
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


def send_proposal_created_notification(instance=None, created=False, **kwargs):
    if not created or kwargs.get("raw", False):
        return
    admin_url = reverse("admin:froide_legalaction_proposal_change", args=(instance.pk,))
    admin_url = settings.SITE_URL + admin_url
    mail_managers(
        _("New legal action proposal submitted"), admin_url, fail_silently=False
    )
