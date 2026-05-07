"""Run the threatened species Brazil gold pipeline in the expected order."""

from __future__ import annotations

import argparse

from src.gbif.gold import (
    build_threatened_species_brazil,
    build_threatened_species_datasets,
    build_threatened_species_geopackage,
    build_threatened_species_occurrences,
)
from src.gbif.gold.validate_threatened_species_brazil import validate


def build_pipeline(args: argparse.Namespace) -> None:
    print("1/4 building species.json")
    build_threatened_species_brazil.build_gold(
        argparse.Namespace(snapshot_date=args.snapshot_date)
    )

    print("2/4 building occurrences.json")
    build_threatened_species_occurrences.build_gold(
        argparse.Namespace(date=args.date, download_key=args.download_key)
    )

    print("3/4 building datasets.json")
    build_threatened_species_datasets.build_gold(
        argparse.Namespace(
            snapshot_date=args.snapshot_date,
            sleep_seconds=args.sleep_seconds,
            timeout=args.timeout,
        )
    )

    print("4/4 building threatened_species_occurrences.gpkg")
    build_threatened_species_geopackage.build_geopackage(
        argparse.Namespace(overwrite=True, batch_size=args.batch_size)
    )

    if args.validate:
        print("validating threatened_species_brazil outputs")
        validate()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Occurrence bronze snapshot date in YYYYMMDD format.")
    parser.add_argument("--snapshot-date", required=True, help="Gold snapshot date in YYYY-MM-DD format.")
    parser.add_argument("--download-key", required=True, help="GBIF download key used for occurrence ZIP selection.")
    parser.add_argument("--sleep-seconds", type=float, default=0.1)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--batch-size", type=int, default=50000)
    parser.add_argument("--skip-validate", action="store_true")
    args = parser.parse_args()
    args.validate = not args.skip_validate
    build_pipeline(args)


if __name__ == "__main__":
    main()
