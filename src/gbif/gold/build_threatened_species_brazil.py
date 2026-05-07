"""Build the first threatened species Brazil gold product."""

from __future__ import annotations

import argparse
import json
from datetime import datetime

from src.gbif.gold.shared import write_json
from src.gbif.gold.threatened_species_brazil_schema import (
    DATASETS_PATH,
    GPKG_PATH,
    GOLD_DIR,
    OCCURRENCES_PATH,
    REFERENCE_PATH,
    SPECIES_FIELDS,
    SPECIES_PATH,
    build_product_schema,
)
from src.gbif.shared.acm_normalization import normalize_threat_status_br
from src.gbif.shared.quality_checks import build_quality_report


def transform_species(record: dict, snapshot_date: str) -> dict:
    transformed = {field: record.get(field) for field in SPECIES_FIELDS}
    transformed["acm_threat_status_br"] = normalize_threat_status_br(record.get("threat_status_br"))
    transformed["snapshot_date"] = snapshot_date
    return transformed


def build_manifest(snapshot_date: str, records: list[dict]) -> dict:
    manifest_path = GOLD_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    outputs = manifest.setdefault("outputs", {})
    outputs["species"] = str(SPECIES_PATH)
    outputs["occurrences"] = str(OCCURRENCES_PATH) if OCCURRENCES_PATH.exists() else "pending_occurrence_extraction"
    outputs["datasets"] = str(DATASETS_PATH) if DATASETS_PATH.exists() else "pending_occurrence_extraction"
    outputs["geopackage"] = str(GPKG_PATH) if GPKG_PATH.exists() else "pending_occurrence_extraction"
    outputs["schema"] = str(GOLD_DIR / "schema.json")
    outputs["quality_report"] = str(GOLD_DIR / "quality_report.json")

    manifest.update(
        {
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
        }
    )
    return manifest


def build_gold(args: argparse.Namespace) -> None:
    source_records = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    species_records = [transform_species(record, args.snapshot_date) for record in source_records]

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    write_json(SPECIES_PATH, species_records)
    write_json(GOLD_DIR / "schema.json", build_product_schema())
    write_json(GOLD_DIR / "quality_report.json", build_quality_report(species_records, SPECIES_FIELDS))
    write_json(GOLD_DIR / "manifest.json", build_manifest(args.snapshot_date, species_records))
    print(f"saved {len(species_records)} threatened species records to {SPECIES_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-date", required=True, help="Gold snapshot date in YYYY-MM-DD format.")
    build_gold(parser.parse_args())


if __name__ == "__main__":
    main()
