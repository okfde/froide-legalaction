from datetime import timedelta

from django.utils import timezone
from froide.foirequest.auth import can_write_foirequest
from froide.foirequest.models.request import Status


def request_is_older_than_three_months(foi_request):
    if foi_request.first_message:
        now = timezone.now().date()
        three_months_ago = now - timedelta(days=30 * 3)
        return foi_request.first_message.date() < three_months_ago
    return False


def request_not_adresses_eu(foi_request):
    if foi_request.jurisdiction:
        return not foi_request.jurisdiction.slug == "europaeische-union"
    return False


def request_is_active(foi_request):
    return foi_request.status in [Status.AWAITING_RESPONSE, Status.ASLEEP]


def foirequest_can_be_tested(foi_request):
    is_old_enough = request_is_older_than_three_months(foi_request)
    is_no_eu_request = request_not_adresses_eu(foi_request)
    is_active = request_is_active(foi_request)
    return is_old_enough and is_active and is_no_eu_request


def user_has_klageautomat_permissions(foi_request, request):
    return can_write_foirequest(foi_request, request)


# is used in KlageautomatMixin and can_use_klageautomat template tag
def can_create_answer(foi_request, request):
    return foirequest_can_be_tested(foi_request) and user_has_klageautomat_permissions(
        foi_request, request
    )
