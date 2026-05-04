"""Reconcile threatened-species names with the GBIF species match API."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import requests


REFERENCE_DIR = Path("data/gbif/00_reference/threatened_species_brazil")
INPUT_PATH = REFERENCE_DIR / "threatened_species_brazil_reference.json"
OUTPUT_PATH = REFERENCE_DIR / "gbif_taxonomy_matches.json"


def match_name(session: requests.Session, name: str, timeout: int) -> dict:
    response = session.get(
        "https://api.gbif.org/v1/species/match",
        params={"name": name},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def reconcile(args: argparse.Namespace) -> None:
    records = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    if args.limit:
        records = records[: args.limit]
        output_path = REFERENCE_DIR / f"gbif_taxonomy_matches_limit_{args.limit}.json"
    else:
        output_path = OUTPUT_PATH

    matches = []
    matched_species_ids = set()
    if output_path.exists() and args.resume:
        matches = json.loads(output_path.read_text(encoding="utf-8"))
        matched_species_ids = {record.get("species_id") for record in matches}
        print(f"resuming from {output_path} with {len(matches)} existing matches")

    session = requests.Session()
    for index, record in enumerate(records, start=1):
        if record["species_id"] in matched_species_ids:
            continue

        name = record["scientific_name"]
        try:
            match = match_name(session, name, args.timeout)
            matches.append(
                {
                    "species_id": record["species_id"],
                    "scientific_name": name,
                    "gbif_match": match,
                }
            )
            if index == 1 or index % args.progress_every == 0 or index == len(records):
                print(f"{index}/{len(records)} matched {name}: {match.get('usageKey')}")
        except Exception as exc:
            matches.append(
                {
                    "species_id": record["species_id"],
                    "scientific_name": name,
                    "error": str(exc),
                }
            )
            print(f"{index}/{len(records)} failed {name}: {exc}")
        if index % args.checkpoint_every == 0 or index == len(records):
            output_path.write_text(json.dumps(matches, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(args.sleep_seconds)

    output_path.write_text(json.dumps(matches, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {len(matches)} GBIF taxonomy matches to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    parser.add_argument("--sleep-seconds", type=float, default=0.25)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--progress-every", type=int, default=100)
    parser.add_argument("--checkpoint-every", type=int, default=25)
    parser.add_argument("--resume", action="store_true", default=True)
    reconcile(parser.parse_args())


if __name__ == "__main__":
    main()
