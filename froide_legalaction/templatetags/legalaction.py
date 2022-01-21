from django import template

from ..models import Proposal

from legal_advice_builder.models import Answer

register = template.Library()


@register.filter
def legalaction_proposal_submitted(value):
    try:
        return Proposal.objects.get(foirequest=value)
    except Proposal.DoesNotExist:
        return None


@register.filter
def questionaire_taken(value):
    try:
        return Answer.objects.get(external_id=value.id)
    except Answer.DoesNotExist:
        return None
