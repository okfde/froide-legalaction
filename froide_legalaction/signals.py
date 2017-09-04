from django.urls import reverse
from django.core.mail import mail_managers
from django.utils.translation import ugettext_lazy as _


def send_proposal_created_notification(instance=None, created=False, **kwargs):
    if not created or kwargs.get('raw', False):
        return
    admin_url = reverse('admin:froide_legalaction_proposal_change',
                        args=(instance.pk,))
    mail_managers(_('New legal action proposal submitted'), admin_url,
                  fail_silently=False)