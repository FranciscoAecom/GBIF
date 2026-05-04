"""Build dataset summaries for threatened species occurrences."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import requests

from src.gbif.gold.shared import write_json
from src.gbif.shared.quality_checks import build_quality_report


GOLD_DIR = Path("data/gbif/03_gold/threatened_species_brazil")
OCCURRENCES_PATH = GOLD_DIR / "occurrences.json"
DATASETS_PATH = GOLD_DIR / "datasets.json"

DATASET_FIELDS = [
    "dataset_key",
    "dataset_title",
    "dataset_type",
    "publishing_org_key",
    "hosting_org_key",
    "doi",
    "license",
    "homepage",
    "citation",
    "record_count_total",
    "threatened_species_record_count",
    "threatened_species_count",
    "source_occurrence_count",
    "snapshot_date",
    "bronze_file_path",
]


def fetch_dataset_metadata(session: requests.Session, dataset_key: str, timeout: int) -> dict:
    response = session.get(f"https://api.gbif.org/v1/dataset/{dataset_key}", timeout=timeout)
    response.raise_for_status()
    return response.json()


def build_dataset_record(dataset_key: str, occurrences: list[dict], metadata: dict, snapshot_date: str) -> dict:
    citation = metadata.get("citation")
    if isinstance(citation, dict):
        citation = citation.get("text")

    return {
        "dataset_key": dataset_key,
        "dataset_title": metadata.get("title"),
        "dataset_type": metadata.get("type"),
        "publishing_org_key": metadata.get("publishingOrganizationKey"),
        "hosting_org_key": metadata.get("hostingOrganizationKey"),
        "doi": metadata.get("doi"),
        "license": metadata.get("license"),
        "homepage": metadata.get("homepage"),
        "citation": citation,
        "record_count_total": metadata.get("recordCount") or metadata.get("numOccurrences"),
        "threatened_species_record_count": len(occurrences),
        "threatened_species_count": len({record.get("species_id") for record in occurrences if record.get("species_id")}),
        "source_occurrence_count": len(occurrences),
        "snapshot_date": snapshot_date,
        "bronze_file_path": None,
    }


def update_manifest(snapshot_date: str, record_count: int) -> None:
    manifest_path = GOLD_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest.setdefault("outputs", {})
    manifest["outputs"]["datasets"] = str(DATASETS_PATH)
    manifest["dataset_snapshot_date"] = snapshot_date
    manifest["dataset_record_count"] = record_count
    write_json(manifest_path, manifest)


def build_gold(args: argparse.Namespace) -> None:
    occurrences = json.loads(OCCURRENCES_PATH.read_text(encoding="utf-8"))
    snapshot_dates = sorted({record.get("snapshot_date") for record in occurrences if record.get("snapshot_date")})
    snapshot_date = snapshot_dates[-1] if snapshot_dates else args.snapshot_date

    occurrences_by_dataset: dict[str, list[dict]] = {}
    for occurrence in occurrences:
        dataset_key = occurrence.get("dataset_key")
        if not dataset_key:
            continue
        occurrences_by_dataset.setdefault(dataset_key, []).append(occurrence)

    session = requests.Session()
    dataset_records = []
    failures = []
    for index, (dataset_key, dataset_occurrences) in enumerate(sorted(occurrences_by_dataset.items()), start=1):
        try:
            metadata = fetch_dataset_metadata(session, dataset_key, args.timeout)
            dataset_records.append(build_dataset_record(dataset_key, dataset_occurrences, metadata, snapshot_date))
            print(f"{index}/{len(occurrences_by_dataset)} dataset={dataset_key} records={len(dataset_occurrences)}")
        except Exception as exc:
            failures.append({"dataset_key": dataset_key, "error": str(exc)})
            dataset_records.append(build_dataset_record(dataset_key, dataset_occurrences, {}, snapshot_date))
            print(f"{index}/{len(occurrences_by_dataset)} failed dataset={dataset_key}: {exc}")
        time.sleep(args.sleep_seconds)

    write_json(DATASETS_PATH, dataset_records)
    quality_report = build_quality_report(dataset_records, DATASET_FIELDS)
    quality_report["metadata_fetch_failures"] = failures
    write_json(GOLD_DIR / "datasets_quality_report.json", quality_report)
    update_manifest(snapshot_date, len(dataset_records))
    print(f"saved {len(dataset_records)} threatened species dataset records to {DATASETS_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-date", default=None)
    parser.add_argument("--sleep-seconds", type=float, default=0.1)
    parser.add_argument("--timeout", type=int, default=60)
    build_gold(parser.parse_args())


if __name__ == "__main__":
    main()

