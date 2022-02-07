# sets permission in KlageautomatMixin and can_use_klageautomat template tag
def can_create_answer(user, foi_request):
    is_staff = user.is_active and user.is_staff
    is_foirequest_creator = user == foi_request.user
    deadline_has_past = foi_request.response_deadline_has_past()
    has_permission = user.has_perm("legal_advice_builder.add_answer")
    return deadline_has_past and (
        is_staff or (is_foirequest_creator and has_permission)
    )
