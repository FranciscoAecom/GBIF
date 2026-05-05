"""Build the GBIF metadata gold dataset from metadata silver."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.gbif.gold.shared import backup_existing_files, build_schema, write_json
from src.gbif.shared.json_stream import iter_json_array, write_json_array
from src.gbif.shared.paths import bronze_bundle_path, gold_product_dir, silver_snapshot_dir
from src.gbif.shared.quality_checks import empty_quality_counts, update_quality_counts


FIELDS = [
    "dataset_gold_id",
    "dataset_key",
    "dataset_title",
    "dataset_type",
    "publishing_org_key",
    "hosting_org_key",
    "doi",
    "license",
    "language",
    "homepage",
    "citation",
    "created",
    "modified",
    "published",
    "record_count",
    "snapshot_date",
    "bronze_file_path",
]


def silver_records_path(snapshot_date: str) -> Path:
    path = silver_snapshot_dir("metadata", snapshot_date) / "alldatasets.json"
    if not path.exists():
        raise FileNotFoundError(f"Silver metadata file not found: {path}")
    return path


def transform_record(record: dict) -> dict:
    dataset_key = record.get("dataset_key")
    snapshot_date = record.get("snapshot_date")
    return {
        "dataset_gold_id": f"{dataset_key}_{snapshot_date}" if dataset_key and snapshot_date else None,
        "dataset_key": record.get("dataset_key"),
        "dataset_title": record.get("dataset_title"),
        "dataset_type": record.get("dataset_type"),
        "publishing_org_key": record.get("publishing_org_key"),
        "hosting_org_key": record.get("hosting_org_key"),
        "doi": record.get("doi"),
        "license": record.get("license"),
        "language": record.get("language"),
        "homepage": record.get("homepage"),
        "citation": record.get("citation"),
        "created": record.get("created"),
        "modified": record.get("modified"),
        "published": record.get("published"),
        "record_count": record.get("record_count"),
        "snapshot_date": snapshot_date,
        "bronze_file_path": record.get("bronze_file_path"),
    }


def build_gold(args: argparse.Namespace) -> Path:
    source_path = silver_records_path(args.date)
    output_dir = gold_product_dir("metadata")
    output_dir.mkdir(parents=True, exist_ok=True)
    backup_existing_files(output_dir, ["alldatasets.json", "schema.json", "quality_report.json", "manifest.json"])

    quality_counts = empty_quality_counts(FIELDS)
    record_count = write_json_array(
        output_dir / "alldatasets.json",
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
        "product": "metadata",
        "source_class": "metadata",
        "source_silver_snapshot": args.date,
        "source_silver_file": str(source_path),
        "source_bronze_bundle": str(bronze_bundle_path("metadata", args.date)),
        "gold_file": str(output_dir / "alldatasets.json"),
        "schema_file": str(output_dir / "schema.json"),
        "quality_report_file": str(output_dir / "quality_report.json"),
        "record_count": record_count,
    }
    write_json(output_dir / "schema.json", build_schema([], FIELDS, "GBIF Gold Datasets"))
    write_json(output_dir / "quality_report.json", quality_counts)
    write_json(output_dir / "manifest.json", manifest)
    print(f"saved {record_count} gold metadata records to {output_dir}")
    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    build_gold(parser.parse_args())


if __name__ == "__main__":
    main()
