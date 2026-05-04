"""Build the first threatened species Brazil gold product."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from src.gbif.gold.shared import write_json
from src.gbif.shared.quality_checks import build_quality_report


REFERENCE_PATH = Path(
    "data/gbif/00_reference/threatened_species_brazil/threatened_species_brazil_reference_gbif_matched.json"
)
GOLD_DIR = Path("data/gbif/03_gold/threatened_species_brazil")

SPECIES_FIELDS = [
    "species_id",
    "scientific_name",
    "canonical_name",
    "accepted_scientific_name",
    "taxon_rank",
    "taxon_key",
    "accepted_taxon_key",
    "kingdom",
    "phylum",
    "class",
    "order",
    "family",
    "genus",
    "species",
    "threat_status_br",
    "threat_status_br_code",
    "threat_status_br_source",
    "threat_status_br_source_document",
    "threat_status_br_year",
    "threat_status_global",
    "threat_status_global_source",
    "is_endemic_to_brazil",
    "biome",
    "state_occurrence",
    "source_reference_path",
    "gbif_checklist_match_status",
    "gbif_taxon_match_confidence",
    "snapshot_date",
]


def transform_species(record: dict, snapshot_date: str) -> dict:
    transformed = {field: record.get(field) for field in SPECIES_FIELDS}
    transformed["snapshot_date"] = snapshot_date
    return transformed


def build_schema() -> dict:
    return {
        "product": "threatened_species_brazil",
        "reference_decision": "MMA Dados Abertos 2021 CSV",
        "files": {
            "species": {
                "path": str(GOLD_DIR / "species.json"),
                "fields": SPECIES_FIELDS,
                "unit": "one threatened species reference record",
            },
            "occurrences": {
                "path": str(GOLD_DIR / "occurrences.json"),
                "status": "pending_occurrence_extraction",
            },
            "datasets": {
                "path": str(GOLD_DIR / "datasets.json"),
                "status": "pending_occurrence_extraction",
            },
            "geopackage": {
                "path": str(GOLD_DIR / "threatened_species_occurrences.gpkg"),
                "status": "pending_occurrence_extraction",
                "crs": "EPSG:4326",
            },
        },
    }


def build_manifest(snapshot_date: str, records: list[dict]) -> dict:
    return {
        "product": "threatened_species_brazil",
        "version_scope": "first_operational_version",
        "threat_reference_decision": "MMA Dados Abertos 2021 CSV used as first-version operational reference",
        "reference_source": "MMA Dados Abertos - Especies Ameacadas",
        "reference_files": [
            "FAUNA - Lista de Especies Ameacadas - 2021.csv",
            "FLORA - Lista de Especies Ameacadas - 2021.csv",
        ],
        "reference_path": str(REFERENCE_PATH),
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "snapshot_date": snapshot_date,
        "species_record_count": len(records),
        "outputs": {
            "species": str(GOLD_DIR / "species.json"),
            "occurrences": "pending_occurrence_extraction",
            "datasets": "pending_occurrence_extraction",
            "geopackage": "pending_occurrence_extraction",
            "schema": str(GOLD_DIR / "schema.json"),
            "quality_report": str(GOLD_DIR / "quality_report.json"),
        },
    }


def build_gold(args: argparse.Namespace) -> None:
    source_records = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    species_records = [transform_species(record, args.snapshot_date) for record in source_records]

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    write_json(GOLD_DIR / "species.json", species_records)
    write_json(GOLD_DIR / "schema.json", build_schema())
    write_json(GOLD_DIR / "quality_report.json", build_quality_report(species_records, SPECIES_FIELDS))
    write_json(GOLD_DIR / "manifest.json", build_manifest(args.snapshot_date, species_records))
    print(f"saved {len(species_records)} threatened species records to {GOLD_DIR / 'species.json'}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-date", required=True, help="Gold snapshot date in YYYY-MM-DD format.")
    build_gold(parser.parse_args())


if __name__ == "__main__":
    main()

