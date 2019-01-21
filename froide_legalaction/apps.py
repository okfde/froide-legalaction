import json
import os

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

        from froide.account.export import registry

        registry.register(export_user_data)


def export_user_data(user):
    from froide.foirequest.models.request import get_absolute_domain_short_url
    from .models import Proposal

    proposals = (
        Proposal.objects
        .filter(foirequest__user=user)
    )
    if not proposals:
        return
    yield ('legalaction_proposals.json', json.dumps([
        {
            'timestamp': p.timestamp.isoformat(),
            'decision_date': (
                p.decision_date.isoformat()
                if p.decision_date else None
            ),
            'legal_date': (
                p.legal_date.isoformat()
                if p.legal_date else None
            ),
            'request': (
                get_absolute_domain_short_url(p.foirequest_id)
            ),
            'phone': p.phone,
            'first_name': p.first_name,
            'last_name': p.last_name,
            'address': p.address,
            'email': p.email,
            'description': p.description,
        }
        for p in proposals]).encode('utf-8')
    )
    for p in proposals:
        yield (
            'legalaction_proposals/%d/documents.json' % p.id,
            json.dumps([
                {
                    'kind': d.kind,
                    'date': d.date.isoformat() if d.date else None,
                    'message': (
                        d.foimessage.get_absolute_domain_short_url()
                        if d.foimessage else None
                    ),
                }
                for d in p.proposaldocument_set.all()
            ]).encode('utf-8')
        )
        for d in p.proposaldocument_set.all():
            if not d.document:
                continue
            yield (
                'legalaction_proposals/%d/%s' % (
                    p.id,
                    os.path.basename(d.document.path)
                ),
                d.get_bytes()
            )
