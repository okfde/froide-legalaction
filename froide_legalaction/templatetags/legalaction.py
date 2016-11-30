from django import template

from ..models import Proposal

register = template.Library()


@register.filter
def legalaction_proposal_submitted(value):
    try:
        return Proposal.objects.get(foirequest=value)
    except Proposal.DoesNotExist:
        return None
