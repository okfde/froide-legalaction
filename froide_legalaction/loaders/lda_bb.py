import json
from datetime import date
from pathlib import Path

from filingcabinet import get_documentcollection_model

from ..models import LegalDecision
from .base import BaseLoader

Collection = get_documentcollection_model()


class LdaBbLoader(BaseLoader):
    """
    Import JSON file with this decision format:

    {
        "detailUrl": "https://www.lda.brandenburg.de/lda/de/akteneinsicht/rechtsprechungsdatenbank/detail/~10-c-5-21-01092022-45590612",
        "gericht": "Bundesverwaltungsgericht",
        "aktenzeichen": "10 C 5.21",
        "datum": "01.09.2022",
        "art": "Urteil",
        "rechtsgrundlage": "Umweltinformationsgesetz (Bund)",
        "kurztext": "Das Bundesverwaltungsgericht hebt die Entscheidung der Vorinstanz im Revisionsverfahren auf und verweist die Sache dorthin zurück. Zur Bewertung des Schutzbedarfs von Namen und Kontaktdaten niederrangiger Amtsträger sowie Behördenexterner bedarf es einer tatsächlichen, einzelfallbezogenen Feststellung, ob durch deren Offenbarung Interessen der Betroffenen erheblich beeinträchtigt werden. Soweit es daran fehlt, räumt der Gesetzgeber dem Bekanntgabeinteresse generell Vorrang ein. Das allgemeine Risiko, dass zugänglich gemachte Daten Verbreitung im Internet finden könnten, genügt allein nicht, um eine erhebliche Beeinträchtigung von Betroffeneninteressen festzustellen.",
        "schlagwort": "Interessenabwägung, Personenbezogene Daten",
        "download": "10 C 5.21 - 01.09.2022",
        "downloadUrl": "https://www.lda.brandenburg.de/sixcms/media.php/276/BVerwG_10_C_5_21.pdf",
        "quelle": "Bundesverwaltungsgericht",
        "quelleUrl": "https://www.bverwg.de/de/010922U10C5.21.0",
        "verfahrensgang": "Verwaltungsgericht Berlin, Urteil, 2 K 384.16, 22.11.2018 \nOberverwaltungsgericht Berlin-Brandenburg, Urteil, 12 B 1.19, 10.06.2020 \nBundesverwaltungsgericht, Beschluss, 10 B 3.20, 19.05.2021",
        "verfahrensgangUrl": "~2-k-384-16-22112018-453d060b",
        "ecli": null,
        "pdfFile": "Bundesverwaltungsgericht 10 C 5.21.pdf"
    },

    """

    def __init__(self):
        self.collection = Collection.objects.get(slug="ifg-lda-brandenburg")

    def load_path(self, path: Path):
        with open(path) as fp:
            decision_list = json.load(fp)
        for meta in decision_list:
            decision = self.load_decision(path, meta)
            yield decision

    def load_decision(self, path, meta):
        court = self.get_court(meta["gericht"])
        decision = LegalDecision()
        decision.set_current_language(self.language_code)
        decision.foi_court = court
        decision.abstract = meta["kurztext"] + "\n\n(Quelle: LDA Brandenburg)"
        decision.court = meta["gericht"]
        decision.law = meta["rechtsgrundlage"]
        decision.decision_type = self.get_decision_type(meta["art"])
        decision.date = date(*reversed([int(x) for x in meta["datum"].split(".")]))
        decision.ecli = meta["ecli"]
        decision.reference = meta["aktenzeichen"]
        decision.source_data = meta

        pdf_filepath = None
        if meta.get("pdfFile"):
            pdf_filepath = path.parent / meta["pdfFile"]
            if not pdf_filepath.exists():
                pdf_filepath = None

        already_maybe, created = self.save_decision(decision)

        if not created and pdf_filepath and not already_maybe.foi_document:
            self.add_document(already_maybe, pdf_filepath)
        if not created:
            already_maybe.source_data = already_maybe.source_data.update(meta)
            already_maybe.source_data.save()
            return already_maybe

        if pdf_filepath:
            self.add_document(decision, pdf_filepath)

        tags = [s.strip() for s in meta["schlagwort"].split(",") if s.strip()]
        self.add_tags(decision, tags)

        return decision
