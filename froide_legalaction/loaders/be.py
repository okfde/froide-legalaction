import logging
import re
from datetime import date
from pathlib import Path

from lxml.html import fromstring

from ..models import LegalDecision
from .base import BaseLoader

logger = logging.getLogger(__name__)

meta_needles = {
    "Gericht": "court_name",
    "Entscheidungsdatum": "date",
    "Aktenzeichen": "reference",
    "ECLI": "ecli",
    "Dokumenttyp": "decision_type",
    "Norm": "law_name",
}

content_needles = [
    "",
    "Orientierungssatz",
    "Leitsatz",
    "Tenor",
    "Tatbestand",
    "Entscheidungsgründe",
]
content_sections = ["Tenor", "Tatbestand", "Entscheidungsgründe"]

FIXES = [
    (re.compile(r"BESCHLUSS([A-Z])"), "### Beschluss\n\n\\1"),
]


class BeLoader(BaseLoader):
    def load_path(self, path: Path):
        for file_path in path.glob("*.html"):
            logger.info("Loading %s", file_path)
            yield self.load_html(file_path)

    def load_html(self, path: Path):
        with open(path, "r") as f:
            root = fromstring(f.read())

        title = root.xpath("//div[@class='docLayoutTitel']//p/text()")
        if title:
            title = title[0].strip()
        else:
            title = ""

        meta_data = {
            "url": root.xpath("//link[@rel='self']/@href")[0],
        }

        for needle, key in meta_needles.items():
            value = root.xpath("//tr[./th//*/text()='%s:']/td//text()" % needle)
            if not value:
                continue
            value = value[0].strip()
            value = value.replace("\xa0", "")
            meta_data[key] = value

        meta_data["date"] = date(
            *reversed([int(x) for x in meta_data["date"].split(".")])
        )

        section_map = {}

        for needle in content_needles:
            query = (
                "//div[@class='docLayoutMarginTopMore'][./h4/text()='%s']/following-sibling::div//dd"
                % needle
            )
            parts = root.xpath(query)
            section = "\n\n".join([p.text_content() for p in parts])
            for fix in FIXES:
                section = re.sub(fix[0], fix[1], section)
            section_map[needle] = section.replace("\xa0", "").strip()

        sections = [
            "## %s\n\n%s" % (needle, section_map[needle])
            for needle in content_sections
            if needle in section_map
        ]

        content = "\n\n".join(sections)
        content = re.sub(r"\n{3,}", "\n\n", content)

        court_name = path.name.split("_", 1)[0].replace("-", " ", 1)
        court_name = court_name.replace("ovg", "oberverwaltungsgericht")
        court_name = court_name.replace("vg", "verwaltungsgericht")
        court = self.get_court(court_name)

        decision = LegalDecision()
        decision.set_current_language(self.language_code)
        decision.title = title
        decision.source_url = meta_data["url"]
        decision.guiding_principle = section_map.get("Leitsatz", "")
        decision.fulltext = content
        decision.court = meta_data.get("court_name", "")
        decision.law = meta_data.get("law_name", "")
        decision_type = meta_data.get("decision_type", "")
        if decision_type:
            decision.decision_type = self.get_decision_type(decision_type)
        decision.date = meta_data["date"]
        decision.ecli = meta_data.get("ecli")
        decision.reference = meta_data.get("reference", "")
        decision.foi_court = court
        decision.source_data = {
            "path": str(path),
            "loader": "be",
            "url": meta_data["url"],
        }

        return decision

    def apply_update(self, decision, unsaved):
        decision.source_data = unsaved.source_data
        decision.title = unsaved.title
        decision.source_url = unsaved.source_url
        decision.save()
