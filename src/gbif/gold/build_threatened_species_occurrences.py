"""Build threatened species occurrence gold records from the occurrence bronze pilot/extraction."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from src.gbif.gold.shared import write_json
from src.gbif.shared.archive_data import unpack_snapshot
from src.gbif.shared.dates import snapshot_date_iso
from src.gbif.shared.normalize import clean_text
from src.gbif.shared.paths import bronze_bundle_path, bronze_snapshot_dir
from src.gbif.shared.quality_checks import build_quality_report


REFERENCE_PATH = Path(
    "data/gbif/00_reference/threatened_species_brazil/threatened_species_brazil_reference_gbif_matched.json"
)
GOLD_DIR = Path("data/gbif/03_gold/threatened_species_brazil")

OCCURRENCE_FIELDS = [
    "record_id",
    "gbif_id",
    "species_id",
    "scientific_name",
    "taxon_key",
    "dataset_key",
    "basis_of_record",
    "occurrence_status",
    "event_date",
    "year",
    "month",
    "day",
    "country_code",
    "state_province",
    "municipality",
    "locality",
    "decimal_latitude",
    "decimal_longitude",
    "coordinate_uncertainty_in_meters",
    "has_coordinate",
    "has_geospatial_issue",
    "sampling_event_id",
    "sampling_protocol",
    "sampling_effort",
    "license",
    "references",
    "snapshot_date",
    "bronze_file_path",
    "threat_status_br",
    "threat_status_br_code",
]


def load_species_by_id() -> dict[str, dict]:
    records = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    return {record["species_id"]: record for record in records}


def transform_occurrence(raw_file: Path, payload: dict, species_by_id: dict[str, dict], snapshot_date: str) -> dict:
    species_id = payload.get("species_id")
    occurrence = payload.get("occurrence") or {}
    species = species_by_id.get(species_id, {})
    gbif_id = occurrence.get("key")

    return {
        "record_id": f"GBIF_{gbif_id}_{snapshot_date}" if gbif_id else None,
        "gbif_id": gbif_id,
        "species_id": species_id,
        "scientific_name": clean_text(occurrence.get("scientificName") or species.get("scientific_name")),
        "taxon_key": occurrence.get("taxonKey") or species.get("taxon_key"),
        "dataset_key": clean_text(occurrence.get("datasetKey")),
        "basis_of_record": clean_text(occurrence.get("basisOfRecord")),
        "occurrence_status": clean_text(occurrence.get("occurrenceStatus")),
        "event_date": clean_text(occurrence.get("eventDate")),
        "year": occurrence.get("year"),
        "month": occurrence.get("month"),
        "day": occurrence.get("day"),
        "country_code": clean_text(occurrence.get("countryCode")),
        "state_province": clean_text(occurrence.get("stateProvince")),
        "municipality": clean_text(occurrence.get("municipality")),
        "locality": clean_text(occurrence.get("locality")),
        "decimal_latitude": occurrence.get("decimalLatitude"),
        "decimal_longitude": occurrence.get("decimalLongitude"),
        "coordinate_uncertainty_in_meters": occurrence.get("coordinateUncertaintyInMeters"),
        "has_coordinate": occurrence.get("hasCoordinate"),
        "has_geospatial_issue": occurrence.get("hasGeospatialIssue"),
        "sampling_event_id": clean_text(occurrence.get("eventID")),
        "sampling_protocol": clean_text(occurrence.get("samplingProtocol")),
        "sampling_effort": clean_text(occurrence.get("samplingEffort")),
        "license": clean_text(occurrence.get("license")),
        "references": clean_text(occurrence.get("references")),
        "snapshot_date": snapshot_date,
        "bronze_file_path": str(raw_file),
        "threat_status_br": species.get("threat_status_br"),
        "threat_status_br_code": species.get("threat_status_br_code"),
    }


def update_manifest(snapshot_date: str, record_count: int) -> None:
    manifest_path = GOLD_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest.setdefault("product", "threatened_species_brazil")
    manifest["occurrence_snapshot_date"] = snapshot_date
    manifest["occurrence_bronze_bundle"] = str(bronze_bundle_path("occurrence", snapshot_date.replace("-", "")))
    manifest.setdefault("outputs", {})
    manifest["outputs"]["occurrences"] = str(GOLD_DIR / "occurrences.json")
    manifest["occurrence_record_count"] = record_count
    write_json(manifest_path, manifest)


def build_gold(args: argparse.Namespace) -> None:
    snapshot_date = snapshot_date_iso(args.date)
    snapshot_dir = unpack_snapshot(bronze_bundle_path("occurrence", args.date), bronze_snapshot_dir("occurrence", args.date))
    species_by_id = load_species_by_id()

    try:
        records = []
        for raw_file in sorted((snapshot_dir / "records").glob("*.json")):
            payload = json.loads(raw_file.read_text(encoding="utf-8"))
            records.append(transform_occurrence(raw_file, payload, species_by_id, snapshot_date))

        GOLD_DIR.mkdir(parents=True, exist_ok=True)
        write_json(GOLD_DIR / "occurrences.json", records)
        write_json(GOLD_DIR / "occurrences_quality_report.json", build_quality_report(records, OCCURRENCE_FIELDS))
        update_manifest(snapshot_date, len(records))
        print(f"saved {len(records)} threatened occurrence records to {GOLD_DIR / 'occurrences.json'}")
    finally:
        shutil.rmtree(snapshot_dir, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Occurrence bronze snapshot date in YYYYMMDD format.")
    build_gold(parser.parse_args())


if __name__ == "__main__":
    main()

