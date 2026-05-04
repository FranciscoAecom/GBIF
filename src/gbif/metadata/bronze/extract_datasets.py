"""Extract raw GBIF dataset metadata pages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.gbif.shared.api_client import GbifApiClient
from src.gbif.shared.archive_data import pack_snapshot
from src.gbif.shared.dates import snapshot_date_iso
from src.gbif.shared.paths import bronze_bundle_path, bronze_snapshot_dir


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_datasets(args: argparse.Namespace) -> Path:
    snapshot_dir = bronze_snapshot_dir("metadata", args.date)
    query_dir = snapshot_dir / "query"
    pages_dir = snapshot_dir / "pages"
    records_dir = snapshot_dir / "records"

    client = GbifApiClient(timeout=args.timeout, sleep_seconds=args.sleep_seconds)
    params = {}
    if args.type:
        params["type"] = args.type
    if args.q:
        params["q"] = args.q

    write_json(
        query_dir / "request.json",
        {
            "endpoint": "/dataset/search",
            "params": params,
            "snapshot_date": snapshot_date_iso(args.date),
        },
    )

    total_records = 0
    for page_number, (page_params, page) in enumerate(
        client.paged_search("dataset/search", params=params, limit=args.limit, page_size=args.page_size),
        start=1,
    ):
        write_json(pages_dir / f"page_{page_number:06d}.json", {"request": page_params, "response": page})
        for record in page.get("results", []):
            dataset_key = record.get("key") or f"page_{page_number:06d}_{total_records:06d}"
            write_json(records_dir / f"{dataset_key}.json", record)
            total_records += 1
        print(f"metadata page={page_number} records={total_records}")

    bundle_path = pack_snapshot(snapshot_dir, bronze_bundle_path("metadata", args.date))
    print(f"saved {total_records} datasets to {bundle_path}")
    return bundle_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Snapshot date in YYYYMMDD format.")
    parser.add_argument("--type", choices=["OCCURRENCE", "CHECKLIST", "SAMPLING_EVENT", "METADATA"])
    parser.add_argument("--q")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--sleep-seconds", type=float, default=0.25)
    parser.add_argument("--timeout", type=int, default=60)
    return parser


def main() -> None:
    extract_datasets(build_parser().parse_args())


if __name__ == "__main__":
    main()

