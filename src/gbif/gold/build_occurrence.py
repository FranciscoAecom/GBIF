"""Build the GBIF occurrence gold dataset from occurrence silver."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.gbif.gold.shared import read_json, write_gold_product
from src.gbif.shared.paths import bronze_bundle_path, gold_product_dir, silver_snapshot_dir


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


def load_silver_records(snapshot_date: str) -> list[dict]:
    path = silver_snapshot_dir("occurrence", snapshot_date) / "allrecords.json"
    if not path.exists():
        raise FileNotFoundError(f"Silver occurrence file not found: {path}")
    return read_json(path)


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
    silver_records = load_silver_records(args.date)
    records = [transform_record(record) for record in silver_records]
    output_dir = gold_product_dir("occurrence")
    write_gold_product(
        output_dir=output_dir,
        data_file_name="allrecords.json",
        records=records,
        fields=FIELDS,
        schema_title="GBIF Gold Biodiversity Records",
        extra_quality={
            "source_layer": "silver",
            "source_path": str(silver_snapshot_dir("occurrence", args.date) / "allrecords.json"),
        },
        manifest={
            "product": "occurrence",
            "source_class": "occurrence",
            "source_silver_snapshot": args.date,
            "source_silver_file": str(silver_snapshot_dir("occurrence", args.date) / "allrecords.json"),
            "source_bronze_bundle": str(bronze_bundle_path("occurrence", args.date)),
        },
    )
    print(f"saved {len(records)} gold occurrence records to {output_dir}")
    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    build_gold(parser.parse_args())


if __name__ == "__main__":
    main()
