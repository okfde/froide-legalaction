from django.db.models.fields import BLANK_CHOICE_DASH
from django_filters.widgets import LinkWidget
from django.utils.encoding import force_str
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _


class ExcludePageParameterLinkWidget(LinkWidget):
    def render_option(self, name, selected_choices, option_value, option_label):
        option_value = force_str(option_value)
        if option_label == BLANK_CHOICE_DASH[0][1]:
            option_label = _("All")
        data = self.data.copy()
        if "page" in data:
            del data["page"]
        data[name] = option_value
        selected = data == self.data or option_value in selected_choices
        try:
            url = data.urlencode()
        except AttributeError:
            url = urlencode(data)
        return self.option_string() % {
            "attrs": selected and ' class="selected"' or "",
            "query_string": url,
            "label": force_str(option_label),
        }


class FilterListWidget(ExcludePageParameterLinkWidget):
    class Media:
        extend = False
        js = ("js/legal_decisions_listfilter.js",)

    def render(self, name, value, attrs=None, choices=(), renderer=None):
        output = super().render(name, value, attrs, choices, renderer)
        search_field = mark_safe(
            '<div class="list-filter"><input type="text" placeholder={} class="form-control form-control-sm list-filter__search">{}</div>'.format(
                _("search"), output
            )
        )
        return search_field
