from __future__ import annotations

import unittest

from src.gbif.shared.acm_normalization import normalize_scientific_name, normalize_threat_status_br


class ACMNormalizationTests(unittest.TestCase):
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
