from django.utils.translation import gettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from datetime import datetime

from .models import Lawsuit, RESULTS, COURTS


@plugin_pool.register_plugin
class LawsuitTablePlugin(CMSPluginBase):
    module = _("Lawsuits")
    name = _("Lawsuit table")
    render_template = "froide_legalaction/cms_plugins/table.html"

    def render(self, context, instance, placeholder):
        context = super().render(context, instance, placeholder)
        lawsuits = Lawsuit.objects.filter(public=True).order_by('-start_date').select_related(
            'publicbody', 'court', 'request', 'plaintiff_user'
        )
        costs = sum(l.costs for l in lawsuits if l.costs)
        costs_covered = sum(l.costs_covered for l in lawsuits
                            if l.costs_covered)
        costs_percentage = 0
        if costs:
            costs_percentage = int(costs_covered / costs * 100)

        context.update({
            'object_list': lawsuits,
            'total_costs': costs,
            'total_costs_not_covered': costs - costs_covered,
            'total_costs_percentage': costs_percentage,
            'result_options': RESULTS,
            'court_options': COURTS
        })
        return context


@plugin_pool.register_plugin
class LawsuitNextTrialsPlugin(CMSPluginBase):
    module = _("Lawsuits")
    name = _("Next trials")
    render_template = "froide_legalaction/cms_plugins/next_trials.html"

    def render(self, context, instance, placeholder):
        context = super().render(context, instance, placeholder)

        lawsuits = Lawsuit.objects.filter(
            public=True, end_date__gte=datetime.today()
        ).order_by('end_date').select_related('court')

        context.update({
            'lawsuits': lawsuits
        })
        return context
