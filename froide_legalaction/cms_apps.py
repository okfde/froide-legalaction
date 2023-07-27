from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool


@apphook_pool.register
class LegalDecisionApp(CMSApp):
    name = "Legal Decision App"
    app_name = "legaldecision"

    def get_urls(self, page=None, language=None, **kwargs):
        return ["froide_legalaction.urls.legaldecision"]
