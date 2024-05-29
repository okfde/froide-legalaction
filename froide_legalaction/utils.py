from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext as _

import icalendar

from .models import Instance


def make_lawsuit_event_calendar(instances):
    cal = icalendar.Calendar()
    cal.add(
        "prodid",
        "-//{site_name} {detail} //{domain}//".format(
            site_name=settings.SITE_NAME,
            detail=_("Lawsuit court hearing"),
            domain=settings.SITE_URL.split("/")[-1],
        ),
    )
    cal.add("version", "2.0")
    cal.add("method", "PUBLISH")
    for instance in instances:
        event = add_ical_events(instance)
        cal.add_component(event)
    return cal


def add_ical_events(instance: Instance):
    event_timezone = timezone.get_current_timezone()

    def tz(dt):
        return dt.astimezone(event_timezone)

    uid = "event-%s-{pk}@{domain}".format(
        pk=instance.id, domain=settings.SITE_URL.split("/")[-1]
    )

    if instance.court_type:
        title = "{}: {}".format(instance.court_type, instance.lawsuit.title)
    else:
        title = instance.lawsuit.title

    event = icalendar.Event()
    event.add("uid", uid % "lawsuit-court-hearing")
    event.add("dtstamp", tz(timezone.now()))
    # Add as all day event
    start = datetime.combine(instance.end_date, datetime.min.time())
    event.add("dtstart", tz(start).date())
    event.add("dtend", tz(start + timedelta(days=1)).date())
    event.add("summary", title)
    if instance.court:
        event.add("location", instance.court.address)
    event.add("summary", title)
    event.add("description", instance.lawsuit.description)
    return event
