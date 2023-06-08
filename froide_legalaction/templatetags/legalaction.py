from django import template

from legal_advice_builder.models import Answer

from ..helper.permissions.klageautomat import can_create_answer
from ..models import Proposal

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


@register.simple_tag(takes_context=True)
def can_use_klageautomat(context, foirequest):
    request = context.get("request")
    return can_create_answer(foirequest, request)
