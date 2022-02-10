from froide.foirequest.models.request import Status


def foirequest_can_be_tested(foi_request):
    if not foi_request.jurisdiction:
        return False
    deadline_has_past = foi_request.response_deadline_has_past()
    is_eu_request = foi_request.jurisdiction.slug == "europaeische-union"
    has_status = foi_request.status in [Status.AWAITING_RESPONSE, Status.ASLEEP]
    return deadline_has_past and has_status and not is_eu_request


def user_has_permissions(user, foi_request):
    is_staff = user.is_active and user.is_staff
    is_foirequest_creator = user == foi_request.user
    has_permission = user.has_perm("legal_advice_builder.add_answer")
    return is_staff or (is_foirequest_creator and has_permission)


# is used in KlageautomatMixin and can_use_klageautomat template tag
def can_create_answer(user, foi_request):
    return foirequest_can_be_tested(foi_request) and user_has_permissions(
        user, foi_request
    )
