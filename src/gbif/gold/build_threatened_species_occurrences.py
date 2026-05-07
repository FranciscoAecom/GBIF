"""Build threatened species occurrence gold records from occurrence bronze data."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path
from zipfile import ZipFile

from src.gbif.gold.shared import write_json
from src.gbif.gold.threatened_species_brazil_schema import (
    GOLD_DIR,
    OCCURRENCE_FIELDS,
    OCCURRENCES_PATH,
)
from src.gbif.reference.threatened_species_brazil.filters import (
    load_reference_records,
    operational_species_by_taxon_key,
)
from src.gbif.shared.acm_normalization import (
    normalize_scientific_name,
    normalize_threat_status_br,
)
from src.gbif.shared.coordinate_normalization import normalize_brazil_coordinate
from src.gbif.shared.date_normalization import normalize_event_date
from src.gbif.shared.dates import snapshot_date_iso
from src.gbif.shared.ibge_spatial_lookup import IBGESpatialLookup
from src.gbif.shared.json_stream import write_json_array
from src.gbif.shared.normalize import clean_bool, clean_text, clean_uuid, first_present
from src.gbif.shared.paths import bronze_snapshot_dir
from src.gbif.shared.quality_checks import empty_quality_counts, update_quality_counts


CSV_FIELD_SIZE_LIMIT = sys.maxsize


def load_species_by_taxon_key() -> dict[int, dict]:
    return operational_species_by_taxon_key(load_reference_records())


def parse_int(value) -> int | None:
    text = clean_text(value)
    if text is None:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def parse_float(value) -> float | None:
    text = clean_text(value)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_bool(value) -> bool | None:
    return clean_bool(value)


def first_row_value(row: dict, *field_names: str):
    return first_present(*(row.get(field_name) for field_name in field_names))


def find_download_zip(snapshot_date: str, download_key: str | None) -> Path:
    downloads_dir = bronze_snapshot_dir("occurrence", snapshot_date) / "downloads"
    if download_key:
        path = downloads_dir / f"{download_key}.zip"
        if not path.exists():
            raise FileNotFoundError(f"GBIF download ZIP not found: {path}")
        return path

    archives = sorted(downloads_dir.glob("*.zip"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not archives:
        raise FileNotFoundError(f"No GBIF download ZIP found in {downloads_dir}")
    if len(archives) > 1:
        raise RuntimeError("More than one GBIF download ZIP found. Use --download-key to select one.")
    return archives[0]


def occurrence_member_name(archive: ZipFile) -> str:
    candidates = [name for name in archive.namelist() if Path(name).name.lower() == "occurrence.txt"]
    if not candidates:
        raise FileNotFoundError("The GBIF DWCA archive does not contain occurrence.txt")
    return candidates[0]


def iter_dwca_occurrences(archive_path: Path):
    csv.field_size_limit(CSV_FIELD_SIZE_LIMIT)
    with ZipFile(archive_path) as archive:
        member_name = occurrence_member_name(archive)
        with archive.open(member_name) as member:
            text_stream = io.TextIOWrapper(member, encoding="utf-8", errors="replace", newline="")
            reader = csv.DictReader(text_stream, delimiter="\t")
            for row in reader:
                yield row


def find_species(row: dict, species_by_taxon_key: dict[int, dict]) -> dict:
    for key_name in ["taxonKey", "acceptedTaxonKey", "speciesKey"]:
        taxon_key = parse_int(row.get(key_name))
        if taxon_key is not None and taxon_key in species_by_taxon_key:
            return species_by_taxon_key[taxon_key]
    return {}


def transform_occurrence(
    row: dict,
    archive_path: Path,
    species_by_taxon_key: dict[int, dict],
    snapshot_date: str,
    ibge_lookup: IBGESpatialLookup,
) -> dict | None:
    species = find_species(row, species_by_taxon_key)
    if not species:
        return None
    gbif_id = parse_int(first_row_value(row, "gbifID", "key", "id"))
    event_date = clean_text(first_row_value(row, "eventDate"))
    decimal_latitude = parse_float(first_row_value(row, "decimalLatitude"))
    decimal_longitude = parse_float(first_row_value(row, "decimalLongitude"))
    has_geospatial_issue = parse_bool(first_row_value(row, "hasGeospatialIssues", "hasGeospatialIssue"))
    scientific_name = normalize_scientific_name(
        first_row_value(row, "scientificName"),
        fallback=species.get("scientific_name"),
    )
    state_province = clean_text(first_row_value(row, "stateProvince"))
    municipality = clean_text(first_row_value(row, "municipality"))
    threat_status_br = species.get("threat_status_br")
    normalized_coordinate = normalize_brazil_coordinate(
        decimal_latitude,
        decimal_longitude,
        has_geospatial_issue=has_geospatial_issue,
    )
    ibge_location = ibge_lookup.lookup(
        normalized_coordinate.get("acm_decimal_latitude"),
        normalized_coordinate.get("acm_decimal_longitude"),
    )

    return {
        "record_id": f"GBIF_{gbif_id}_{snapshot_date}" if gbif_id else None,
        "gbif_id": gbif_id,
        "species_id": species.get("species_id"),
        "scientific_name": scientific_name,
        "taxon_key": parse_int(first_row_value(row, "taxonKey")) or species.get("taxon_key"),
        "dataset_key": clean_uuid(first_row_value(row, "datasetKey")),
        "basis_of_record": clean_text(first_row_value(row, "basisOfRecord")),
        "occurrence_status": clean_text(first_row_value(row, "occurrenceStatus")),
        "event_date": event_date,
        **normalize_event_date(event_date),
        "year": parse_int(first_row_value(row, "year")),
        "month": parse_int(first_row_value(row, "month")),
        "day": parse_int(first_row_value(row, "day")),
        "country_code": clean_text(first_row_value(row, "countryCode")),
        "state_province": state_province,
        "municipality": municipality,
        **ibge_location.as_record_fields(),
        "locality": clean_text(first_row_value(row, "locality")),
        "decimal_latitude": decimal_latitude,
        "decimal_longitude": decimal_longitude,
        "coordinate_uncertainty_in_meters": parse_float(first_row_value(row, "coordinateUncertaintyInMeters")),
        "has_coordinate": parse_bool(first_row_value(row, "hasCoordinate")),
        "has_geospatial_issue": has_geospatial_issue,
        **normalized_coordinate,
        "sampling_event_id": clean_text(first_row_value(row, "eventID")),
        "sampling_protocol": clean_text(first_row_value(row, "samplingProtocol")),
        "sampling_effort": clean_text(first_row_value(row, "samplingEffort")),
        "license": clean_text(first_row_value(row, "license")),
        "references": clean_text(first_row_value(row, "references")),
        "snapshot_date": snapshot_date,
        "bronze_file_path": f"{archive_path}::occurrence.txt",
        "threat_status_br": threat_status_br,
        "acm_threat_status_br": normalize_threat_status_br(threat_status_br),
        "threat_status_br_code": species.get("threat_status_br_code"),
    }


def write_records(records, output_path: Path) -> dict:
    quality_counts = empty_quality_counts(OCCURRENCE_FIELDS)
    write_json_array(
        output_path,
        records,
        on_record=lambda record: update_quality_counts(quality_counts, record, OCCURRENCE_FIELDS),
    )
    return quality_counts


def update_manifest(
    snapshot_date: str, archive_path: Path, download_key: str | None, record_count: int, skipped_unmatched_count: int
) -> None:
    manifest_path = GOLD_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest.setdefault("product", "threatened_species_brazil")
    manifest["occurrence_snapshot_date"] = snapshot_date
    manifest["occurrence_bronze_download_zip"] = str(archive_path)
    manifest["occurrence_download_key"] = download_key or archive_path.stem
    manifest["ibge_reference_path"] = "data/gbif/00_reference/ibge"
    manifest["ibge_spatial_lookup"] = {
        "enabled": True,
        "input_coordinate_fields": ["acm_decimal_latitude", "acm_decimal_longitude"],
        "outputs": [
            "acm_state_province",
            "acm_municipality",
        ],
        "method": "point-in-polygon against IBGE simplified GeoJSON meshes",
    }
    manifest.setdefault("outputs", {})
    manifest["outputs"]["occurrences"] = str(OCCURRENCES_PATH)
    manifest["occurrence_record_count"] = record_count
    manifest["occurrence_skipped_unmatched_count"] = skipped_unmatched_count
    write_json(manifest_path, manifest)


def build_gold(args: argparse.Namespace) -> None:
    snapshot_date = snapshot_date_iso(args.date)
    archive_path = find_download_zip(args.date, args.download_key)
    species_by_taxon_key = load_species_by_taxon_key()
    ibge_lookup = IBGESpatialLookup()

    counters = {"skipped_unmatched_count": 0}

    def records():
        for row in iter_dwca_occurrences(archive_path):
            record = transform_occurrence(row, archive_path, species_by_taxon_key, snapshot_date, ibge_lookup)
            if record is None:
                counters["skipped_unmatched_count"] += 1
                continue
            yield record

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    quality_report = write_records(records(), OCCURRENCES_PATH)
    quality_report["skipped_unmatched_count"] = counters["skipped_unmatched_count"]
    write_json(GOLD_DIR / "occurrences_quality_report.json", quality_report)
    update_manifest(
        snapshot_date,
        archive_path,
        args.download_key,
        quality_report["record_count"],
        counters["skipped_unmatched_count"],
    )
    print(f"saved {quality_report['record_count']} threatened occurrence records to {OCCURRENCES_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Occurrence bronze snapshot date in YYYYMMDD format.")
    parser.add_argument("--download-key", help="GBIF download key. Required when the snapshot has more than one ZIP.")
    build_gold(parser.parse_args())


if __name__ == "__main__":
    main()
