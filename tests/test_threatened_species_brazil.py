from __future__ import annotations

import re
import unittest
from pathlib import Path

from src.gbif.gold.threatened_species_brazil_schema import (
    GPKG_DOCUMENTED_FIELDS,
    GPKG_ATTRIBUTE_FIELDS,
    OCCURRENCE_FIELDS,
)
from src.gbif.shared.acm_normalization import normalize_scientific_name, normalize_threat_status_br


PROJECT_ROOT = Path(__file__).resolve().parents[1]
THREATENED_SPECIES_DOC = PROJECT_ROOT / "docs/agentes/especies_ameacadas_brasil.md"


def documented_fields(section_title: str) -> list[str]:
    text = THREATENED_SPECIES_DOC.read_text(encoding="utf-8")
    section_start = text.index(f"### `{section_title}`")
    fields_start = text.index("```text", section_start) + len("```text")
    fields_end = text.index("```", fields_start)
    return [
        line.strip()
        for line in text[fields_start:fields_end].splitlines()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", line.strip())
    ]


class ThreatenedSpeciesBrazilTests(unittest.TestCase):
    def test_threat_status_only_requested_values_become_outros(self) -> None:
        self.assertEqual(normalize_threat_status_br("[Nao e especie brasileira]"), "Outros")
        self.assertEqual(normalize_threat_status_br("[Nao e mais taxon valido]"), "Outros")
        self.assertEqual(normalize_threat_status_br("Subespecie que sai da Lista"), "Outros")
        self.assertEqual(normalize_threat_status_br("Extinta (EX)"), "Extinta (EX)")
        self.assertEqual(normalize_threat_status_br("Dados Insuficientes (DD)"), "Dados Insuficientes (DD)")

    def test_threat_status_normalizes_only_case_variant_for_critical(self) -> None:
        self.assertEqual(
            normalize_threat_status_br("Criticamente Em Perigo (CR)"),
            "Criticamente em Perigo (CR)",
        )
        self.assertEqual(
            normalize_threat_status_br("Criticamente em Perigo (CR)(PEX)"),
            "Criticamente em Perigo (CR)(PEX)",
        )

    def test_invalid_scientific_name_uses_reference_fallback(self) -> None:
        self.assertEqual(normalize_scientific_name("-15.173611", fallback="Nome correto"), "Nome correto")
        self.assertEqual(normalize_scientific_name("BOLD:AAA2402", fallback="Nome correto"), "Nome correto")
        self.assertEqual(normalize_scientific_name("Panthera onca", fallback="Nome correto"), "Panthera onca")

    def test_geopackage_attributes_are_subset_of_occurrence_json_fields(self) -> None:
        missing = set(GPKG_ATTRIBUTE_FIELDS) - set(OCCURRENCE_FIELDS)
        self.assertEqual(missing, set())

    def test_geopackage_does_not_export_audit_only_fields(self) -> None:
        audit_only_fields = {
            "locality",
            "decimal_latitude",
            "decimal_longitude",
            "acm_decimal_latitude",
            "acm_decimal_longitude",
            "coordinate_uncertainty_in_meters",
            "has_geospatial_issue",
            "license",
        }
        self.assertEqual(set(GPKG_ATTRIBUTE_FIELDS) & audit_only_fields, set())

    def test_documented_occurrence_fields_match_schema(self) -> None:
        self.assertEqual(documented_fields("occurrences.json"), OCCURRENCE_FIELDS)

    def test_documented_geopackage_fields_match_schema(self) -> None:
        self.assertEqual(documented_fields("threatened_species_occurrences.gpkg"), GPKG_DOCUMENTED_FIELDS)


if __name__ == "__main__":
    unittest.main()
