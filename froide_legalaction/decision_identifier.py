"""
This module contains functions to generate German ECLI identifiers for decisions.

https://e-justice.europa.eu/175/DE/european_case_law_identifier_ecli?GERMANY

"""

import re

from slugify import slugify


def make_german_ecli(date, ref, court, decision_type=None):
    # ECLI:DE:BVerwG:2002:170402U9CN1.01.0
    # ECLI:DE:VGMI:2008:1210.7K982.08.00

    if court.jurisdiction.slug == "europaeische-union":
        raise ValueError("EU court decisions ECLI cannot be generated from references")

    if court.jurisdiction.slug == "bund":
        formatted_reference = make_federal_ecli_reference(
            date, ref, court, decision_type=decision_type
        )
    else:
        formatted_reference = make_state_ecli_reference(date, ref)

    return "ECLI:{country}:{court_code}:{year}:{reference}".format(
        country="DE",
        court_code=court.extra_data.get("ecli_court_code", ""),
        year=date.strftime("%Y"),
        reference=formatted_reference,
    )


def make_federal_ecli_reference(date, ref, court, decision_type=None):
    supported_federal_courts = (
        "Bundesgerichtshof",
        "Bundesverwaltungsgericht",
        "Bundesfinanzhof",
        "Bundesarbeitsgericht",
    )
    # not supported: Bundessozialgericht

    formatted_ref = ref.replace("/", ".").replace(" ", "").upper()
    if court.name not in supported_federal_courts:
        raise ValueError("Cannot generate ECLI for this federal court")

    if court.name == "Bundesfinanzhof":
        """
        VE: Vorabentscheidungsersuchen an den EuGH
        VV: Vorlage an das BVerfG
        BA: Beschluss im Verfahren des einstweiligen Rechtsschutzes:
            AdV[A1] -Antrag und AdV[A2] -Beschwerde
        B: Beschluss, soweit nicht „BA“ zu vergeben ist
        U: Urteil, rechtskräftiger Gerichtsbescheid, Zwischenurteil etc.
        """
        # TODO: implement
        # For now we pretend that all decisions are U or B
        pass

    collision = "0"
    # Abkürzung für den Entscheidungstyp („U“ für Urteil, „B“ für Beschluss, „V“ für Verfügung, „S“ für Sonstige),
    if not decision_type:
        formatted_decision_type = "U"
    if decision_type == "court_ruling":
        formatted_decision_type = "U"
    elif decision_type == "court_decision":
        formatted_decision_type = "B"
    elif decision_type == "court_notice":
        formatted_decision_type = "G"
    elif decision_type == "court_order":
        formatted_decision_type = "V"
    else:
        formatted_decision_type = "S"

    return "{dd}{mm}{yy}.{decision_type}.{reference}.{collision}".format(
        dd=date.strftime("%d"),
        mm=date.strftime("%m"),
        yy=date.strftime("%y"),
        reference=formatted_ref,
        decision_type=formatted_decision_type,
        collision=collision,
    )


def make_state_ecli_reference(date, ref):
    collision = "00"
    formatted_ref = ref.replace("/", ".").replace(" ", "").upper()
    return "{mm}{dd}.{formatted_ref}.{collision}".format(
        dd=date.strftime("%d"),
        mm=date.strftime("%m"),
        formatted_ref=formatted_ref,
        collision=collision,
    )


def parse_reference(reference):
    AKTENZEICHEN = re.compile(
        r"(?:\d+|[IVX]+) *[A-Za-z]+ *\d+ *[\/\. _] *\d+(?:\.[A-Z])?"
    )
    match = AKTENZEICHEN.search(reference)
    if match:
        return match.group(0).replace(".", "/")
    raise ValueError(f"Could not parse reference: {reference}")


def guess_ecli_from_decision(decision):
    reference = parse_reference(decision.reference)
    return make_german_ecli(
        decision.date,
        reference,
        decision.foi_court,
        decision_type=decision.decision_type,
    )


def make_slug(decision):
    if decision.slug:
        return decision.slug
    if decision.ecli:
        _, rest = decision.ecli.split(":", 1)
        return slugify(rest)
    if decision.reference:
        guessed_ecli = guess_ecli_from_decision(decision)
        _, rest = guessed_ecli.split(":", 1)
        return slugify(rest)
    raise ValueError("Cannot make slug for decision")
