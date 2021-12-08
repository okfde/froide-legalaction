from itertools import chain, islice

from django.db.models.fields import BLANK_CHOICE_DASH
from django_filters.widgets import LinkWidget
from django.utils.encoding import force_str
from django.utils.http import urlencode
from django.utils.translation import gettext as _


class CustomLinkWidget(LinkWidget):
    def render_options(self, choices, selected_choices, name):
        selected_choices = set(force_str(v) for v in selected_choices)
        output = []
        n = 5
        combined_choices = chain(self.choices, choices)
        combined_choices = islice(combined_choices, n)
        for option_value, option_label in combined_choices:
            if isinstance(option_label, (list, tuple)):
                for option in option_label:
                    output.append(self.render_option(name, selected_choices, *option))
            else:
                output.append(
                    self.render_option(
                        name, selected_choices, option_value, option_label
                    )
                )
        return "\n".join(output)

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
