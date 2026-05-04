"""Extract occurrence search pages for threatened species in Brazil using GBIF public search."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.gbif.shared.api_client import GbifApiClient
from src.gbif.shared.archive_data import pack_snapshot
from src.gbif.shared.dates import snapshot_date_iso
from src.gbif.shared.paths import bronze_bundle_path, bronze_snapshot_dir


REFERENCE_PATH = Path(
    "data/gbif/00_reference/threatened_species_brazil/threatened_species_brazil_reference_gbif_matched.json"
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def get_taxon_key(reference_record: dict) -> int | None:
    return reference_record.get("accepted_taxon_key") or reference_record.get("taxon_key")


def extract(args: argparse.Namespace) -> Path:
    reference_records = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    if args.species_limit:
        reference_records = reference_records[: args.species_limit]

    snapshot_dir = bronze_snapshot_dir("occurrence", args.date)
    query_dir = snapshot_dir / "query"
    pages_dir = snapshot_dir / "pages"
    records_dir = snapshot_dir / "records"
    client = GbifApiClient(timeout=args.timeout, sleep_seconds=args.sleep_seconds)

    write_json(
        query_dir / "threatened_species_request.json",
        {
            "endpoint": "/occurrence/search",
            "country": "BR",
            "source_reference": str(REFERENCE_PATH),
            "snapshot_date": snapshot_date_iso(args.date),
            "species_limit": args.species_limit,
            "occurrence_limit_per_species": args.occurrence_limit_per_species,
        },
    )

    total_records = 0
    for reference_record in reference_records:
        taxon_key = get_taxon_key(reference_record)
        if not taxon_key:
            continue

        params = {"country": "BR", "taxonKey": taxon_key}
        species_id = reference_record["species_id"]
        page_number = 0
        for page_params, page in client.paged_search(
            "occurrence/search",
            params=params,
            limit=args.occurrence_limit_per_species,
            page_size=args.page_size,
        ):
            page_number += 1
            write_json(
                pages_dir / f"{species_id}_page_{page_number:06d}.json",
                {"request": page_params, "response": page},
            )
            for record in page.get("results", []):
                gbif_id = record.get("key") or f"{species_id}_{total_records:08d}"
                write_json(records_dir / f"{gbif_id}.json", {"species_id": species_id, "occurrence": record})
                total_records += 1
        print(f"{species_id} taxonKey={taxon_key} accumulated_records={total_records}")

    bundle_path = pack_snapshot(snapshot_dir, bronze_bundle_path("occurrence", args.date))
    print(f"saved {total_records} threatened occurrence records to {bundle_path}")
    return bundle_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--species-limit", type=int)
    parser.add_argument("--occurrence-limit-per-species", type=int, default=100)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--sleep-seconds", type=float, default=0.25)
    parser.add_argument("--timeout", type=int, default=60)
    extract(parser.parse_args())


if __name__ == "__main__":
    main()
