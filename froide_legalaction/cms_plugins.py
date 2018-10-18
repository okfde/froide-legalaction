from django.utils.translation import ugettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import Lawsuit


@plugin_pool.register_plugin
class LawsuitTablePlugin(CMSPluginBase):
    module = _("Lawsuits")
    name = _("Lawsuit table")
    render_template = "froide_legalaction/cms_plugins/table.html"

    def render(self, context, instance, placeholder):
        context = super().render(context, instance, placeholder)
        context.update({
            'object_list': Lawsuit.objects.all().select_related(
                'publicbody', 'court', 'request'
            )
        })
        return context
