from datetime import date

from django.db.models import Max
from django.utils.translation import gettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import CourtTypes, Lawsuit


@plugin_pool.register_plugin
class LawsuitTablePlugin(CMSPluginBase):
    module = _("Lawsuits")
    name = _("Lawsuit table")
    render_template = "froide_legalaction/cms_plugins/table.html"

    def render(self, context, instance, placeholder):
        context = super().render(context, instance, placeholder)
        lawsuits = Lawsuit.objects.filter(public=True).select_related(
            "publicbody", "request", "plaintiff_user"
        )
        lawsuits = lawsuits.prefetch_related("instance_set", "instance_set__court")
        costs = sum(lawsuit.costs for lawsuit in lawsuits if lawsuit.costs)
        costs_covered = sum(
            lawsuit.costs_covered for lawsuit in lawsuits if lawsuit.costs_covered
        )
        costs_percentage = 0
        if costs:
            costs_percentage = int(costs_covered / costs * 100)

        context.update(
            {
                "object_list": lawsuits,
                "total_costs": costs,
                "total_costs_not_covered": costs - costs_covered,
                "total_costs_percentage": costs_percentage,
                "result_options": Lawsuit.Result.choices,
                "court_options": CourtTypes.choices,
            }
        )
        return context


@plugin_pool.register_plugin
class LawsuitNextTrialsPlugin(CMSPluginBase):
    module = _("Lawsuits")
    name = _("Next trials")
    render_template = "froide_legalaction/cms_plugins/next_trials.html"

    def render(self, context, instance, placeholder):
        context = super().render(context, instance, placeholder)

        today = date.today()
        lawsuits = (
            Lawsuit.objects.filter(public=True)
            .annotate(next_end_date=Max("instance__end_date"))
            .filter(next_end_date__gte=today)
            .order_by("next_end_date")
        )

        context.update({"lawsuits": lawsuits})
        return context
