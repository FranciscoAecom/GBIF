"""Build the silver GBIF metadata dataset."""

from __future__ import annotations

import argparse
import json
import shutil

from src.gbif.shared.archive_data import unpack_snapshot
from src.gbif.shared.dates import snapshot_date_iso
from src.gbif.shared.normalize import clean_list, clean_text
from src.gbif.shared.paths import bronze_bundle_path, bronze_snapshot_dir, silver_snapshot_dir
from src.gbif.shared.quality_checks import build_quality_report


FIELDS = [
    "dataset_key",
    "dataset_title",
    "dataset_type",
    "publishing_org_key",
    "hosting_org_key",
    "doi",
    "license",
    "description",
    "language",
    "homepage",
    "citation",
    "created",
    "modified",
    "published",
    "record_count",
    "contacts",
    "keywords",
    "snapshot_date",
    "bronze_file_path",
]


def transform_record(raw: dict, bronze_file_path: str, snapshot_date: str) -> dict:
    return {
        "dataset_key": clean_text(raw.get("key")),
        "dataset_title": clean_text(raw.get("title")),
        "dataset_type": clean_text(raw.get("type")),
        "publishing_org_key": clean_text(raw.get("publishingOrganizationKey")),
        "hosting_org_key": clean_text(raw.get("hostingOrganizationKey")),
        "doi": clean_text(raw.get("doi")),
        "license": clean_text(raw.get("license")),
        "description": clean_text(raw.get("description")),
        "language": clean_text(raw.get("language")),
        "homepage": clean_text(raw.get("homepage")),
        "citation": clean_text(raw.get("citation", {}).get("text") if isinstance(raw.get("citation"), dict) else raw.get("citation")),
        "created": clean_text(raw.get("created")),
        "modified": clean_text(raw.get("modified")),
        "published": clean_text(raw.get("published")),
        "record_count": raw.get("numConstituents") or raw.get("recordCount"),
        "contacts": raw.get("contacts") or [],
        "keywords": clean_list(raw.get("keywordCollections")),
        "snapshot_date": snapshot_date,
        "bronze_file_path": bronze_file_path,
    }


def build_silver(args: argparse.Namespace) -> None:
    snapshot_dir = unpack_snapshot(bronze_bundle_path("metadata", args.date), bronze_snapshot_dir("metadata", args.date))
    try:
        records = []
        for raw_path in sorted((snapshot_dir / "records").glob("*.json")):
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            records.append(transform_record(raw, str(raw_path), snapshot_date_iso(args.date)))

        output_dir = silver_snapshot_dir("metadata", args.date)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "alldatasets.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        (output_dir / "quality_report.json").write_text(
            json.dumps(build_quality_report(records, FIELDS), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (output_dir / "mapping_report.json").write_text(
            json.dumps({"fields": FIELDS, "source": "bronze records/*.json"}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"saved {len(records)} metadata records to {output_dir}")
    finally:
        shutil.rmtree(snapshot_dir, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    build_silver(parser.parse_args())


if __name__ == "__main__":
    main()
