# -*- encoding: utf-8 -*-
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _
from django.db.models import signals


class FroideLegalActionConfig(AppConfig):
    name = 'froide_legalaction'
    verbose_name = _("Froide Legal Action App")

    def ready(self):
        from .models import Proposal
        from .signals import send_proposal_created_notification

        signals.post_save.connect(send_proposal_created_notification,
                                  sender=Proposal)
