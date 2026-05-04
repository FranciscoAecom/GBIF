"""Apply GBIF taxonomy matches to the normalized threatened-species reference."""

from __future__ import annotations

import json
from pathlib import Path


REFERENCE_DIR = Path("data/gbif/00_reference/threatened_species_brazil")
REFERENCE_PATH = REFERENCE_DIR / "threatened_species_brazil_reference.json"
MATCHES_PATH = REFERENCE_DIR / "gbif_taxonomy_matches.json"
OUTPUT_PATH = REFERENCE_DIR / "threatened_species_brazil_reference_gbif_matched.json"


def apply_matches() -> None:
    reference_records = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    match_records = json.loads(MATCHES_PATH.read_text(encoding="utf-8"))
    matches_by_species_id = {record["species_id"]: record for record in match_records}

    enriched = []
    for record in reference_records:
        match_record = matches_by_species_id.get(record["species_id"], {})
        match = match_record.get("gbif_match") or {}
        enriched_record = {
            **record,
            "accepted_scientific_name": match.get("species") or match.get("scientificName"),
            "canonical_name": match.get("canonicalName"),
            "taxon_rank": match.get("rank"),
            "taxon_key": match.get("usageKey"),
            "accepted_taxon_key": match.get("acceptedUsageKey") or match.get("usageKey"),
            "kingdom": match.get("kingdom") or record.get("kingdom"),
            "phylum": match.get("phylum") or record.get("phylum"),
            "class": match.get("class") or record.get("class"),
            "order": match.get("order") or record.get("order"),
            "family": match.get("family") or record.get("family"),
            "genus": match.get("genus") or record.get("genus"),
            "species": match.get("species") or record.get("species"),
            "gbif_checklist_match_status": match.get("matchType") or match.get("status"),
            "gbif_taxon_match_confidence": match.get("confidence"),
        }
        enriched.append(enriched_record)

    OUTPUT_PATH.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {len(enriched)} GBIF-enriched reference records to {OUTPUT_PATH}")


def main() -> None:
    apply_matches()


if __name__ == "__main__":
    main()

