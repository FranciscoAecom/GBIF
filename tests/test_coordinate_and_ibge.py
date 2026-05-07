from __future__ import annotations

import unittest

from src.gbif.shared.coordinate_normalization import normalize_brazil_coordinate
from src.gbif.shared.ibge_spatial_lookup import IBGESpatialLookup


class CoordinateNormalizationTests(unittest.TestCase):
    def test_valid_brazil_coordinate_is_preserved(self) -> None:
        self.assertEqual(
            normalize_brazil_coordinate(-23.5505, -46.6333),
            {"acm_decimal_latitude": -23.5505, "acm_decimal_longitude": -46.6333},
        )

    def test_swapped_brazil_coordinate_is_corrected(self) -> None:
        self.assertEqual(
            normalize_brazil_coordinate(-46.6333, -23.5505),
            {"acm_decimal_latitude": -23.5505, "acm_decimal_longitude": -46.6333},
        )

    def test_outside_brazil_coordinate_is_removed(self) -> None:
        self.assertEqual(
            normalize_brazil_coordinate(40.7128, -74.0060),
            {"acm_decimal_latitude": None, "acm_decimal_longitude": None},
        )

    def test_geospatial_issue_is_removed_when_swap_does_not_fix_it(self) -> None:
        self.assertEqual(
            normalize_brazil_coordinate(-23.5505, -46.6333, has_geospatial_issue=True),
            {"acm_decimal_latitude": None, "acm_decimal_longitude": None},
        )


class IBGESpatialLookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lookup = IBGESpatialLookup()

    def test_known_points_resolve_to_expected_municipalities(self) -> None:
        cases = [
            (-23.5505, -46.6333, "São Paulo", "São Paulo"),
            (-15.7939, -47.8828, "Distrito Federal", "Brasília"),
            (-3.1190, -60.0217, "Amazonas", "Manaus"),
        ]
        for latitude, longitude, state, municipality in cases:
            with self.subTest(latitude=latitude, longitude=longitude):
                location = self.lookup.lookup(latitude, longitude)
                self.assertEqual(location.state_name, state)
                self.assertEqual(location.municipality_name, municipality)

    def test_invalid_coordinate_returns_empty_location(self) -> None:
        location = self.lookup.lookup(None, None)
        self.assertIsNone(location.state_name)
        self.assertIsNone(location.municipality_name)
