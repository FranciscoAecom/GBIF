"""Build the GBIF metadata gold dataset from metadata silver."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.gbif.gold.shared import read_json, write_gold_product
from src.gbif.shared.paths import bronze_bundle_path, gold_product_dir, silver_snapshot_dir


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


def load_silver_records(snapshot_date: str) -> list[dict]:
    path = silver_snapshot_dir("metadata", snapshot_date) / "alldatasets.json"
    if not path.exists():
        raise FileNotFoundError(f"Silver metadata file not found: {path}")
    return read_json(path)


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
    silver_records = load_silver_records(args.date)
    records = [transform_record(record) for record in silver_records]
    output_dir = gold_product_dir("metadata")
    write_gold_product(
        output_dir=output_dir,
        data_file_name="alldatasets.json",
        records=records,
        fields=FIELDS,
        schema_title="GBIF Gold Datasets",
        extra_quality={
            "source_layer": "silver",
            "source_path": str(silver_snapshot_dir("metadata", args.date) / "alldatasets.json"),
        },
        manifest={
            "product": "metadata",
            "source_class": "metadata",
            "source_silver_snapshot": args.date,
            "source_silver_file": str(silver_snapshot_dir("metadata", args.date) / "alldatasets.json"),
            "source_bronze_bundle": str(bronze_bundle_path("metadata", args.date)),
        },
    )
    print(f"saved {len(records)} gold metadata records to {output_dir}")
    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    build_gold(parser.parse_args())


if __name__ == "__main__":
    main()
