"""Build dataset summaries for threatened species occurrences."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.gbif.gold.shared import write_json
from src.gbif.shared.api_client import GbifApiClient
from src.gbif.shared.json_stream import iter_json_array
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


def fetch_dataset_metadata(client: GbifApiClient, dataset_key: str) -> dict:
    return client.get(f"dataset/{dataset_key}")


def build_dataset_record(dataset_key: str, summary: dict, metadata: dict, snapshot_date: str) -> dict:
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
        "threatened_species_record_count": summary["source_occurrence_count"],
        "threatened_species_count": len(summary["species_ids"]),
        "source_occurrence_count": summary["source_occurrence_count"],
        "snapshot_date": snapshot_date,
        "bronze_file_path": summary.get("bronze_file_path"),
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
    snapshot_dates = set()
    summaries_by_dataset: dict[str, dict] = {}
    for occurrence in iter_json_array(OCCURRENCES_PATH):
        if occurrence.get("snapshot_date"):
            snapshot_dates.add(occurrence["snapshot_date"])
        dataset_key = occurrence.get("dataset_key")
        if not dataset_key:
            continue
        summary = summaries_by_dataset.setdefault(
            dataset_key,
            {
                "source_occurrence_count": 0,
                "species_ids": set(),
                "bronze_file_path": occurrence.get("bronze_file_path"),
            },
        )
        summary["source_occurrence_count"] += 1
        if occurrence.get("species_id"):
            summary["species_ids"].add(occurrence["species_id"])
        if not summary.get("bronze_file_path") and occurrence.get("bronze_file_path"):
            summary["bronze_file_path"] = occurrence["bronze_file_path"]

    snapshot_date = sorted(snapshot_dates)[-1] if snapshot_dates else args.snapshot_date

    client = GbifApiClient(timeout=args.timeout, sleep_seconds=args.sleep_seconds)
    dataset_records = []
    failures = []
    for index, (dataset_key, summary) in enumerate(sorted(summaries_by_dataset.items()), start=1):
        try:
            metadata = fetch_dataset_metadata(client, dataset_key)
            dataset_records.append(build_dataset_record(dataset_key, summary, metadata, snapshot_date))
            print(f"{index}/{len(summaries_by_dataset)} dataset={dataset_key} records={summary['source_occurrence_count']}")
        except Exception as exc:
            failures.append({"dataset_key": dataset_key, "error": str(exc)})
            dataset_records.append(build_dataset_record(dataset_key, summary, {}, snapshot_date))
            print(f"{index}/{len(summaries_by_dataset)} failed dataset={dataset_key}: {exc}")

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
