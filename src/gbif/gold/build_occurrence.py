"""Build the GBIF occurrence gold dataset from occurrence silver."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.gbif.gold.shared import backup_existing_files, build_schema, write_json
from src.gbif.shared.json_stream import iter_json_array, write_json_array
from src.gbif.shared.paths import bronze_bundle_path, gold_product_dir, silver_snapshot_dir
from src.gbif.shared.quality_checks import empty_quality_counts, update_quality_counts


FIELDS = [
    "record_id",
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
    "license",
    "references",
    "snapshot_date",
    "bronze_file_path",
]


def silver_records_path(snapshot_date: str) -> Path:
    path = silver_snapshot_dir("occurrence", snapshot_date) / "allrecords.json"
    if not path.exists():
        raise FileNotFoundError(f"Silver occurrence file not found: {path}")
    return path


def transform_record(record: dict) -> dict:
    gbif_id = record.get("gbif_id")
    snapshot_date = record.get("snapshot_date")
    return {
        "record_id": f"GBIF_{gbif_id}_{snapshot_date}" if gbif_id and snapshot_date else None,
        "gbif_id": gbif_id,
        "dataset_key": record.get("dataset_key"),
        "basis_of_record": record.get("basis_of_record"),
        "occurrence_status": record.get("occurrence_status"),
        "scientific_name": record.get("scientific_name"),
        "canonical_name": record.get("canonical_name"),
        "taxon_key": record.get("taxon_key"),
        "accepted_taxon_key": record.get("accepted_taxon_key"),
        "kingdom": record.get("kingdom"),
        "phylum": record.get("phylum"),
        "class": record.get("class"),
        "order": record.get("order"),
        "family": record.get("family"),
        "genus": record.get("genus"),
        "species": record.get("species"),
        "event_date": record.get("event_date"),
        "year": record.get("year"),
        "month": record.get("month"),
        "day": record.get("day"),
        "country_code": record.get("country_code"),
        "state_province": record.get("state_province"),
        "municipality": record.get("municipality"),
        "locality": record.get("locality"),
        "decimal_latitude": record.get("decimal_latitude"),
        "decimal_longitude": record.get("decimal_longitude"),
        "coordinate_uncertainty_in_meters": record.get("coordinate_uncertainty_in_meters"),
        "has_coordinate": record.get("has_coordinate"),
        "has_geospatial_issue": record.get("has_geospatial_issue"),
        "license": record.get("license"),
        "references": record.get("references"),
        "snapshot_date": snapshot_date,
        "bronze_file_path": record.get("bronze_file_path"),
    }


def build_gold(args: argparse.Namespace) -> Path:
    source_path = silver_records_path(args.date)
    output_dir = gold_product_dir("occurrence")
    output_dir.mkdir(parents=True, exist_ok=True)
    backup_existing_files(output_dir, ["allrecords.json", "schema.json", "quality_report.json", "manifest.json"])

    quality_counts = empty_quality_counts(FIELDS)
    record_count = write_json_array(
        output_dir / "allrecords.json",
        (transform_record(record) for record in iter_json_array(source_path)),
        on_record=lambda record: update_quality_counts(quality_counts, record, FIELDS),
    )
    quality_counts.update(
        {
            "source_layer": "silver",
            "source_path": str(source_path),
        }
    )
    manifest = {
        "product": "occurrence",
        "source_class": "occurrence",
        "source_silver_snapshot": args.date,
        "source_silver_file": str(source_path),
        "source_bronze_bundle": str(bronze_bundle_path("occurrence", args.date)),
        "gold_file": str(output_dir / "allrecords.json"),
        "schema_file": str(output_dir / "schema.json"),
        "quality_report_file": str(output_dir / "quality_report.json"),
        "record_count": record_count,
    }
    write_json(output_dir / "schema.json", build_schema([], FIELDS, "GBIF Gold Biodiversity Records"))
    write_json(output_dir / "quality_report.json", quality_counts)
    write_json(output_dir / "manifest.json", manifest)
    print(f"saved {record_count} gold occurrence records to {output_dir}")
    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    build_gold(parser.parse_args())


if __name__ == "__main__":
    main()
