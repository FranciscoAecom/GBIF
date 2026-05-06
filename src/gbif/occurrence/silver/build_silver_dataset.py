"""Build the silver GBIF occurrence dataset."""

from __future__ import annotations

import argparse
import json
import shutil

from src.gbif.shared.archive_data import unpack_snapshot
from src.gbif.shared.coordinate_normalization import normalize_brazil_coordinate
from src.gbif.shared.date_normalization import normalize_event_date
from src.gbif.shared.dates import snapshot_date_iso
from src.gbif.shared.json_stream import write_json_array
from src.gbif.shared.normalize import clean_bool, clean_list, clean_text
from src.gbif.shared.paths import bronze_bundle_path, bronze_snapshot_dir, silver_snapshot_dir
from src.gbif.shared.quality_checks import empty_quality_counts, update_quality_counts


FIELDS = [
    "gbif_id",
    "dataset_key",
    "basis_of_record",
    "occurrence_status",
    "scientific_name",
    "canonical_name",
    "taxon_key",
    "accepted_taxon_key",
    "kingdom",
    "phylum",
    "class",
    "order",
    "family",
    "genus",
    "species",
    "event_date",
    "acm_event_date",
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
    "acm_decimal_latitude",
    "acm_decimal_longitude",
    "recorded_by",
    "identified_by",
    "license",
    "references",
    "snapshot_date",
    "bronze_file_path",
]


def transform_record(raw: dict, bronze_file_path: str, snapshot_date: str) -> dict:
    event_date = clean_text(raw.get("eventDate"))
    normalized_event_date = normalize_event_date(event_date)
    has_geospatial_issue = clean_bool(raw.get("hasGeospatialIssues") or raw.get("hasGeospatialIssue"))
    normalized_coordinate = normalize_brazil_coordinate(
        raw.get("decimalLatitude"),
        raw.get("decimalLongitude"),
        has_geospatial_issue=has_geospatial_issue,
    )
    return {
        "gbif_id": raw.get("key"),
        "dataset_key": clean_text(raw.get("datasetKey")),
        "basis_of_record": clean_text(raw.get("basisOfRecord")),
        "occurrence_status": clean_text(raw.get("occurrenceStatus")),
        "scientific_name": clean_text(raw.get("scientificName")),
        "canonical_name": clean_text(raw.get("genericName") or raw.get("acceptedScientificName")),
        "taxon_key": raw.get("taxonKey"),
        "accepted_taxon_key": raw.get("acceptedTaxonKey"),
        "kingdom": clean_text(raw.get("kingdom")),
        "phylum": clean_text(raw.get("phylum")),
        "class": clean_text(raw.get("class")),
        "order": clean_text(raw.get("order")),
        "family": clean_text(raw.get("family")),
        "genus": clean_text(raw.get("genus")),
        "species": clean_text(raw.get("species")),
        "event_date": event_date,
        **normalized_event_date,
        "year": raw.get("year"),
        "month": raw.get("month"),
        "day": raw.get("day"),
        "country_code": clean_text(raw.get("countryCode")),
        "state_province": clean_text(raw.get("stateProvince")),
        "municipality": clean_text(raw.get("municipality")),
        "locality": clean_text(raw.get("locality")),
        "decimal_latitude": raw.get("decimalLatitude"),
        "decimal_longitude": raw.get("decimalLongitude"),
        "coordinate_uncertainty_in_meters": raw.get("coordinateUncertaintyInMeters"),
        "has_coordinate": clean_bool(raw.get("hasCoordinate")),
        "has_geospatial_issue": has_geospatial_issue,
        **normalized_coordinate,
        "recorded_by": clean_list(raw.get("recordedBy")),
        "identified_by": clean_list(raw.get("identifiedBy")),
        "license": clean_text(raw.get("license")),
        "references": clean_text(raw.get("references")),
        "snapshot_date": snapshot_date,
        "bronze_file_path": bronze_file_path,
    }


def build_silver(args: argparse.Namespace) -> None:
    snapshot_dir = unpack_snapshot(bronze_bundle_path("occurrence", args.date), bronze_snapshot_dir("occurrence", args.date))
    try:
        snapshot_date = snapshot_date_iso(args.date)

        def transformed_records():
            for raw_path in sorted((snapshot_dir / "records").glob("*.json")):
                raw = json.loads(raw_path.read_text(encoding="utf-8"))
                yield transform_record(raw, str(raw_path), snapshot_date)

        output_dir = silver_snapshot_dir("occurrence", args.date)
        output_dir.mkdir(parents=True, exist_ok=True)
        quality_counts = empty_quality_counts(FIELDS)
        record_count = write_json_array(
            output_dir / "allrecords.json",
            transformed_records(),
            on_record=lambda record: update_quality_counts(quality_counts, record, FIELDS),
        )
        (output_dir / "quality_report.json").write_text(
            json.dumps(quality_counts, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (output_dir / "mapping_report.json").write_text(
            json.dumps({"fields": FIELDS, "source": "bronze records/*.json"}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"saved {record_count} occurrence records to {output_dir}")
    finally:
        shutil.rmtree(snapshot_dir, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    build_silver(parser.parse_args())


if __name__ == "__main__":
    main()
