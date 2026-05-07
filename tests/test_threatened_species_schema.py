from __future__ import annotations

import unittest

from tests.documentation_helpers import documented_fields
from src.gbif.gold.threatened_species_brazil_schema import (
    GPKG_ATTRIBUTE_FIELDS,
    GPKG_DOCUMENTED_FIELDS,
    OCCURRENCE_FIELDS,
)


class ThreatenedSpeciesSchemaTests(unittest.TestCase):
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
