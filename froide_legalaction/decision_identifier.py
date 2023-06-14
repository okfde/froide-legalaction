import re

from slugify import slugify


def make_german_ecli(date, ref, court):
    # ECLI:DE:BVerwG:2002:170402U9CN1.01.0
    # ECLI:DE:VGMI:2008:1210.7K982.08.00

    formatted_reference = make_vg_ecli_reference(date, ref)

    return "ECLI:{country}:{court_code}:{year}:{reference}".format(
        country="DE",
        court_code=court.extra_data.get("ecli_court_code", ""),
        year=date.strftime("%Y"),
        reference=formatted_reference,
    )


def make_vg_ecli_reference(date, ref):
    collision = "00"
    formatted_ref = ref.replace("/", ".").replace(" ", "").upper()
    return "{mm}{dd}.{formatted_ref}.{collision}".format(
        dd=date.strftime("%d"),
        mm=date.strftime("%m"),
        formatted_ref=formatted_ref,
        collision=collision,
    )


def parse_reference(reference):
    AKTENZEICHEN = re.compile(r"\d+ *[A-Z]+ *\d+ *[\/\. ] *\d+")
    match = AKTENZEICHEN.search(reference)
    if match:
        return match.group(0).replace(".", "/")
    raise ValueError(f"Could not parse reference: {reference}")


def make_slug(decision):
    if decision.slug:
        return decision.slug
    if decision.ecli:
        _, rest = decision.ecli.split(":", 1)
        return slugify(rest)
    if decision.reference:
        reference = parse_reference(decision.reference)
        fake_ecli = make_german_ecli(decision.date, reference, decision.foi_court)
        _, rest = fake_ecli.split(":", 1)
        return slugify(rest)
    raise ValueError("Cannot make slug for decision")
