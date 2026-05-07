"""Build the first threatened species Brazil gold product."""

from __future__ import annotations

import argparse
import json

from src.gbif.gold.threatened_species_brazil_manifest import base_manifest, write_manifest
from src.gbif.gold.shared import write_json
from src.gbif.gold.threatened_species_brazil_schema import (
    GOLD_DIR,
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
    manifest = base_manifest(snapshot_date)
    manifest["species_record_count"] = len(records)
    return manifest


def build_gold(args: argparse.Namespace) -> None:
    source_records = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    species_records = [transform_species(record, args.snapshot_date) for record in source_records]

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    write_json(SPECIES_PATH, species_records)
    write_json(GOLD_DIR / "schema.json", build_product_schema())
    write_json(GOLD_DIR / "quality_report.json", build_quality_report(species_records, SPECIES_FIELDS))
    write_manifest(build_manifest(args.snapshot_date, species_records))
    print(f"saved {len(species_records)} threatened species records to {SPECIES_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-date", required=True, help="Gold snapshot date in YYYY-MM-DD format.")
    build_gold(parser.parse_args())


if __name__ == "__main__":
    main()
